import os
import sys
import time
import json

import MuteTypes
import poST_code
import plant_code


def run():
    sleepTime = 0
    path = sys.argv[1]
    paused = False
    stopSim = False
    pauseTime = 0
    pauseStartTime = 0
    control_program = poST_code.Program()
    plant_program = plant_code.Program()
    while not stopSim:
        if not os.path.exists(path + "/flags"):
            with open(path + "/flags", "w") as fl:
                fl.write(False.__str__() + "\n" + False.__str__() + "\n")
                fl.close()
        with open(path + "/flags", "r") as f:
            flags = f.read()
            f.close()
        flags = flags.splitlines()
        try:
            stopSim = (flags[0] != "True")
            pauseSim = (flags[1] == "True")
        except:
            pauseSim = True
            stopSim = False
        if pauseSim and not paused:
            paused = True
            pauseStartTime = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)//(10**6)
        elif not pauseSim and paused:
            paused = False
            pauseFinishTime = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)//(10**6)
            pauseTime += pauseFinishTime - pauseStartTime
        elif not pauseSim:
            iterStartTime = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)//(10**6)
            startTime = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)//(10**6) + sleepTime - pauseTime
            poST_code._global_time = startTime
            plant_code._global_time = startTime

            control(control_program)
            for k,v in poST_code.globVars.items():
                plant_code.setVariable(k, v)
            for k,v in poST_code.outVars.items():
                plant_code.setVariable(k, v)
            plant(plant_program)
            for k,v in plant_code.globVars.items():
                poST_code.setVariable(k, v)
            for k,v in plant_code.outVars.items():
                poST_code.setVariable(k, v)

            #TODO: отображать время в миллисекундах или микросекундах
            iterFinishTime = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)//(10**6)
            if poST_code.taskTime is not None:
                if (plant_code.taskTime > 0):
                    sleepStartTime = time.perf_counter_ns()//(10**6)
                    checkTime = plant_code.taskTime - (iterFinishTime - iterStartTime)
                    if checkTime > 0:
                        time.sleep(checkTime)
                    sleepEndTime = time.perf_counter_ns()//(10**6)
                    sleepTime += (sleepEndTime - sleepStartTime)


def plant(program):
    path = sys.argv[1]
    sim_in_path = os.path.join(path, "plant_sim_in")

    # Ensure the file exists
    if not os.path.exists(sim_in_path):
        open(sim_in_path, "w").close()

    # Read the file content
    with open(sim_in_path, "r") as f:
        try:
            sim_in = json.load(f)
        except json.JSONDecodeError:
            sim_in = {}  # Default to empty if JSON is invalid
        f.close()

    # Update inVars dictionary
    for key in plant_code.inVars.keys():
        value = sim_in.get(key)
        try:
            if value is not None:
                plant_code.setVariable(key, value)
        except Exception as e:
            print(f"Failed to set value for {key}: {e}")

    open(sim_in_path, "w").close()

    program.run_iter()

    with open(path + "/plant_inputs", 'w') as f:
        json.dump(plant_code.inVars, f, cls=MuteTypes.MuteEncoder, indent=4)
        f.close()
    with open(path + "/plant_output", 'w') as f:
        json.dump(plant_code.outVars, f, cls=MuteTypes.MuteEncoder, indent=4)
        f.close()
    with open(path + "/plant_states", 'w') as f:
        json.dump(plant_code.pStates, f, indent=4)
        f.close()
    with open(path + "/plant_times", 'w') as f:
        json.dump(plant_code.pTimes, f, indent=4)
        f.close()
    with open(path + "/plant_glob_vars", 'w') as f:
        json.dump(plant_code.globVars, f, cls=MuteTypes.MuteEncoder, indent=4)
        f.close()
    with open(path + "/plant_vars", 'w') as f:
        json.dump(plant_code.Vars, f, cls=MuteTypes.MuteEncoder, indent=4)
        f.close()
    all_data = {
        "inputs": plant_code.inVars,
        "outputs": plant_code.outVars,
        "states": plant_code.pStates,
        "times": plant_code.pTimes,
        "global_vars": plant_code.globVars,
        "vars": plant_code.Vars
        }

    # Write the JSON to file using MuteEncoder
    with open(os.path.join(path, "plant_all"), 'w') as f:
        json.dump(all_data, f, cls=MuteTypes.MuteEncoder, indent=4)
        f.close()


def control(program):
    path = sys.argv[1]

    sim_in_path = os.path.join(path, "sim_in")
    global_sim_in_path = os.path.join(path, "global_sim_in")

    # Ensure the file exists
    if not os.path.exists(global_sim_in_path):
        open(global_sim_in_path, "w").close()

    # Read the file content
    with open(global_sim_in_path, "r") as f:
        try:
            global_sim_in = json.load(f)
        except json.JSONDecodeError:
            global_sim_in = {}  # Default to empty if JSON is invalid
        f.close()

    # Update globVars dictionary
    for key in poST_code.globVars.keys():
        value = global_sim_in.get(key)
        try:
            if value is not None:
                poST_code.setVariable(key, value)
        except Exception as e:
            print(f"Failed to set value for {key}: {e}")

    # Ensure the file exists
    if not os.path.exists(sim_in_path):
        open(sim_in_path, "w").close()

    # Read the file content
    with open(sim_in_path, "r") as f:
        try:
            sim_in = json.load(f)
        except json.JSONDecodeError:
            sim_in = {}  # Default to empty if JSON is invalid
        f.close()

    # Update inVars dictionary
    for key in poST_code.inVars.keys():
        value = sim_in.get(key)
        try:
            if value is not None:
                poST_code.setVariable(key, value)
        except Exception as e:
            print(f"Failed to set value for {key}: {e}")

    open(global_sim_in_path, "w").close();
    open(sim_in_path, "w").close()

    program.run_iter()

    with open(path + "/inputs", 'w') as f:
        json.dump(poST_code.inVars, f, cls=MuteTypes.MuteEncoder, indent=4)
        f.close()
    with open(path + "/output", 'w') as f:
        json.dump(poST_code.outVars, f, cls=MuteTypes.MuteEncoder, indent=4)
        f.close()
    with open(path + "/states", 'w') as f:
        json.dump(poST_code.pStates, f, indent=4)
        f.close()
    with open(path + "/times", 'w') as f:
        json.dump(poST_code.pTimes, f, indent=4)
        f.close()
    with open(path + "/glob_vars", 'w') as f:
        json.dump(poST_code.globVars, f, cls=MuteTypes.MuteEncoder, indent=4)
        f.close()
    with open(path + "/vars", 'w') as f:
        json.dump(poST_code.Vars, f, cls=MuteTypes.MuteEncoder, indent=4)
        f.close()
    all_data = {"inputs": poST_code.inVars, "outputs": poST_code.outVars, "states": poST_code.pStates,
        "times": poST_code.pTimes, "global_vars": poST_code.globVars, "vars": poST_code.Vars}

    # Write the JSON to file using MuteEncoder
    with open(os.path.join(path, "all"), 'w') as f:
        json.dump(all_data, f, cls=MuteTypes.MuteEncoder, indent=4)
        f.close()


if __name__ == '__main__':
    run()
