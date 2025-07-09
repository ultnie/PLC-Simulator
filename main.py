import os
import sys
import time
from json_helpers import read_json_file, write_json_file, write_simulation_outputs

import poST_code
import plant_code

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
    global paused, stopSim, pauseTime, pauseStartTime, path, control_program, plant_program, scale, tCurrentScaled, tPrevScaled, tScaleChanged, poSTIterFinishTime, plantIterFinishTime

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
        startTime = iterStartTime - pauseTime

        checkTime_control = int(poST_code.taskTime / scale) - (iterStartTime - poSTIterFinishTime)
        if checkTime_control <= 0:
            control(control_program, startTime)
            poSTIterFinishTime = int(((time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) // (10 ** 6)) - tScaleChanged) * scale + tPrevScaled)

        checkTime_plant = int(plant_code.taskTime / scale) - (iterStartTime - plantIterFinishTime)
        if checkTime_plant <= 0:
            plant(plant_program, startTime)
            plantIterFinishTime = int(((time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW) // (10 ** 6)) - tScaleChanged) * scale + tPrevScaled)

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
            open(time_scale_path, 'w').close()

        simulation_step()


def process_program(program, module, other_module, name_prefix, start_time, handle_global_vars=False):
    global path, scale

    module._global_time = start_time

    if handle_global_vars:
        global_sim_in_path = os.path.join(path, "global_sim_in")
        global_sim_in = read_json_file(global_sim_in_path)

        for key in module.globVars.keys():
            value = global_sim_in.get(key)
            if value is not None:
                try:
                    module.setVariable(key, value)
                except Exception as e:
                    print(f"Failed to set global var {key}: {e}")

        for k, v in module.globVars.items():
            other_module.setVariable(k, v)

        write_json_file(global_sim_in_path, {})

    sim_in_path = os.path.join(path, f"{name_prefix}_sim_in")
    sim_in = read_json_file(sim_in_path)

    for key in sim_in.keys():
        value = sim_in.get(key)
        if value is not None:
            try:
                module.setVariable(key, value)
            except Exception as e:
                print(f"Failed to set input var {key}: {e}")

    write_json_file(sim_in_path, {})

    program.run_iter()

    write_simulation_outputs(path, name_prefix, module, scale)

    for k, v in module.outVars.items():
        other_module.setVariable(k, v)


def control(program, start_time):
    process_program(program, poST_code, plant_code, "control",  start_time, handle_global_vars=False)


def plant(program, start_time):
    process_program(program, plant_code, poST_code, "plant", start_time, handle_global_vars=True)


if __name__ == '__main__':
    run()
