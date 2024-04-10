import os
import sys
import time
import json

import poST_code
import MuteTypes


def main():
    sleepTime = 0
    program = poST_code.Program()
    path = sys.argv[1]
    paused = False
    pauseTime = 0
    pauseStartTime = 0
    while True:
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
            pauseStartTime = time.process_time()
        elif not pauseSim and paused:
            paused = False
            pauseFinishTime = time.process_time()
            pauseTime += pauseFinishTime - pauseStartTime
        elif not pauseSim:
            iterStartTime = time.process_time()
            startTime = time.process_time() + sleepTime - pauseTime
            poST_code._global_time = startTime

            if not os.path.exists(path + "/sim_in"):
                open(path + "/sim_in", "w").close()
            with open(path + "/sim_in", "r") as f:
                sim_in = f.read()
                f.close()
            sim_in = sim_in.splitlines()
            for key in poST_code.inVars.keys():
                if key in sim_in:
                    try:
                        poST_code.inVars[key].__set__(True)
                    except:
                        pass
                else:
                    try:
                        poST_code.inVars[key].__set__(False)
                    except:
                        pass

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
            # TODO: _g_p_times (или они уже в vars?)

            iterFinishTime = time.process_time()
            if poST_code.taskTime is not None:
                if (poST_code.taskTime.total_seconds() > 0):
                    sleepStartTime = time.perf_counter()
                    checkTime = poST_code.taskTime.total_seconds() - (iterFinishTime - iterStartTime)
                    if checkTime > 0:
                        time.sleep(checkTime)
                    sleepEndTime = time.perf_counter()
                    sleepTime += (sleepEndTime - sleepStartTime)
            else:
                open(path + "/inputs", 'w').close()
                break
        if stopSim:
            open(path + "/inputs", 'w').close()
            break


if __name__ == '__main__':
    main()
