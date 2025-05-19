import os
import sys
import time
import json

import MuteTypes
import poST_code
import plant_code

sleepTime = 0
paused = False
stopSim = False
pauseTime = 0
pauseStartTime = 0
scale = 1.0
tCurrentScaled = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) // (10 ** 6)
tPrevScaled = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) // (10 ** 6)
tScaleChanged = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) // (10 ** 6)
poSTIterFinishTime = 0
plantIterFinishTime = 0
path = sys.argv[1]
control_program = poST_code.Program()
plant_program = plant_code.Program()


def simulation_step():
    global sleepTime, paused, stopSim, pauseTime, pauseStartTime, path, control_program, plant_program, scale, tCurrentScaled, tPrevScaled, tScaleChanged, poSTIterFinishTime, plantIterFinishTime

    flags_path = os.path.join(path, "flags")
    if not os.path.exists(flags_path):
        with open(flags_path, "w") as fl:
            fl.write("True\nFalse\nFalse\n")  # stopSim, pauseSim, stepOnce

    with open(flags_path, "r") as f:
        flags = f.read().splitlines()

    try:
        stopSim = (flags[0] != "True")
        pauseSim = (flags[1] == "True")
        stepOnce = (len(flags) > 2 and flags[2] == "True")
    except:
        pauseSim = True
        stepOnce = False
        stopSim = False

    if (pauseSim and not stepOnce) and not paused:
        paused = True
        pauseStartTime = int(((time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) // (10 ** 6)) - tScaleChanged) * scale + tPrevScaled)
    elif (not pauseSim or stepOnce) and paused:
        paused = False
        pauseFinishTime = int(((time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) // (10 ** 6)) - tScaleChanged) * scale + tPrevScaled)
        pauseTime += pauseFinishTime - pauseStartTime
    elif not pauseSim or stepOnce:
        iterStartTime = int(((time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) // (10 ** 6)) - tScaleChanged) * scale + tPrevScaled)
        startTime = int(((time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) // (10 ** 6)) - tScaleChanged) * scale + tPrevScaled) + sleepTime - pauseTime
        poST_code._global_time = startTime
        plant_code._global_time = startTime

        if poST_code.taskTime is not None and poST_code.taskTime > 0:
            sleepStartTime = int(((time.perf_counter_ns() // (10**6)) - tScaleChanged) * scale + tPrevScaled)
            checkTime = int(poST_code.taskTime / scale) - (iterStartTime - poSTIterFinishTime)
            print(poST_code.taskTime)
            print(checkTime)
            if checkTime <= 0:
                control(control_program)
                for k, v in poST_code.globVars.items():
                    plant_code.setVariable(k, v)
                for k, v in poST_code.outVars.items():
                    plant_code.setVariable(k, v)
                poSTIterFinishTime = int(((time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) // (10 ** 6)) - tScaleChanged) * scale + tPrevScaled)
            sleepEndTime = int(((time.perf_counter_ns() // (10**6)) - tScaleChanged) * scale + tPrevScaled)
            sleepTime += (sleepEndTime - sleepStartTime)


        if plant_code.taskTime is not None and plant_code.taskTime > 0:
            sleepStartTime = int(((time.perf_counter_ns() // (10**6)) - tScaleChanged) * scale + tPrevScaled)
            checkTime = int(plant_code.taskTime / scale) - (iterStartTime - plantIterFinishTime)
            print(plant_code.taskTime)
            print(checkTime)
            if checkTime <= 0:
                plant(plant_program)
                for k, v in plant_code.globVars.items():
                    poST_code.setVariable(k, v)
                for k, v in plant_code.outVars.items():
                    poST_code.setVariable(k, v)
                plantIterFinishTime = int(((time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) // (10 ** 6)) - tScaleChanged) * scale + tPrevScaled)
            sleepEndTime = int(((time.perf_counter_ns() // (10**6)) - tScaleChanged) * scale + tPrevScaled)
            sleepTime += (sleepEndTime - sleepStartTime)

        # If stepOnce was used, clear it
        if stepOnce:
            with open(flags_path, "w") as f:
                f.write("True\nTrue\nFalse\n")


def run():
    global stopSim, scale, tCurrentScaled, tPrevScaled, tScaleChanged
    time_scale_path = os.path.join(path, "time_scale")
    while not stopSim:
        try:
            if os.path.getsize(time_scale_path) != 0:
                with open(time_scale_path, "r") as f:
                    newScale = float(f.read())
                    tPrevScaled = int(((time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) // (10 ** 6)) - tScaleChanged) * scale + tPrevScaled) #Масштабированное время на момент изменения масштаба
                    tScaleChanged = (time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) // (10 ** 6)) #Реальное время изменения масштаба
                    if 0.001 <= newScale <= 1000:
                        scale = newScale
                    else:
                        print("New scale is out of bounds (less than 0.001 or more than 1000)")
                    f.close()
                    tCurrentScaled = int(((time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) // (10 ** 6)) - tScaleChanged) * scale + tPrevScaled) #Масштабированное время
                open(time_scale_path, "w").close()
        except FileNotFoundError:
            print("time_scale file does not exist")

        simulation_step()


def process_program(program, module, name_prefix, handle_global_vars=False):
    global path, scale

    if handle_global_vars:
        global_sim_in_path = os.path.join(path, "global_sim_in")
        if not os.path.exists(global_sim_in_path):
            open(global_sim_in_path, "w").close()

        with open(global_sim_in_path, "r") as f:
            try:
                global_sim_in = json.load(f)
            except json.JSONDecodeError:
                global_sim_in = {}

        for key in module.globVars.keys():
            value = global_sim_in.get(key)
            if value is not None:
                try:
                    module.setVariable(key, value)
                except Exception as e:
                    print(f"Failed to set global var {key}: {e}")

        open(global_sim_in_path, "w").close()

    sim_in_path = os.path.join(path, f"{name_prefix}_sim_in") if name_prefix else os.path.join(path, "sim_in")
    if not os.path.exists(sim_in_path):
        open(sim_in_path, "w").close()

    with open(sim_in_path, "r") as f:
        try:
            sim_in = json.load(f)
        except json.JSONDecodeError:
            sim_in = {}

    for key in module.inVars.keys():
        value = sim_in.get(key)
        if value is not None:
            try:
                module.setVariable(key, value)
            except Exception as e:
                print(f"Failed to set input var {key}: {e}")
    open(sim_in_path, "w").close()

    program.run_iter()

    all_data = {
        "scale": scale,
        "inputs": module.inVars,
        "outputs": module.outVars,
        "states": module.pStates,
        "times": module.pTimes,
        "global_vars": module.globVars,
        "vars": module.Vars
    }

    for fname, data in all_data.items():
        suffix = f"{name_prefix}_{fname}" if name_prefix else fname
        with open(os.path.join(path, suffix), 'w') as f:
            json.dump(data, f, cls=MuteTypes.MuteEncoder, indent=4)

    all_file = os.path.join(path, f"{name_prefix}_all" if name_prefix else "all")
    with open(all_file, 'w') as f:
        json.dump(all_data, f, cls=MuteTypes.MuteEncoder, indent=4)


def control(program):
    process_program(program, poST_code, name_prefix="", handle_global_vars=True)


def plant(program):
    process_program(program, plant_code, name_prefix="plant", handle_global_vars=False)


if __name__ == '__main__':
    run()
