import os
import sys
import time

import poST_code


def main():
    sleepTime = 0
    program = poST_code.Program()
    path = sys.argv[1]
    inputs = "\n".join("{!r}".format(k).replace("\'", "") for k in poST_code.inVars.keys()) + "\n"
    paused = False
    pauseTime = 0
    pauseStartTime = 0
    with open(path + "/inputs", 'w') as f:
        f.write(inputs)
        f.close()
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
            in_text = "INPUTS:\n" + "\n".join(
                "{!r}: {!r}".format(k, v).replace("\'", "") for k, v in poST_code.inVars.items())
            out_text = "\n\nOUTPUTS:\n" + "\n".join(
                "{!r}: {!r}".format(k, v).replace("\'", "") for k, v in poST_code.outVars.items())
            states_text = "\n\nSTATES:\n" + "\n".join(
                "{!r}: {!r}".format(k, v).replace("\'", "") for k, v in poST_code.pStates.items())
            times_text = "\n\nTIMES:\n" + "\n".join(
                "{!r}: {!r}".format(k, v).replace("\'", "") for k, v in poST_code.pTimes.items())
            glob_text = "\n\nGLOBAL:\n" + "\n".join(
                "{!r}: {!r}".format(k, v).replace("\'", "") for k, v in poST_code.globVars.items())
            if os.path.exists(path + "/outputs"):
                with open(path + "/outputs", 'r') as f:
                    text = f.read()
                    f.close()
            if text != in_text + out_text + states_text + times_text + glob_text:
                with open(path + "/outputs", 'w') as f:
                    f.write(in_text + out_text + states_text + times_text + glob_text)
                    f.close()

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
