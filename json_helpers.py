import os
import json
import MuteTypes

def read_json_file(filepath):
    if not os.path.exists(filepath):
        open(filepath, "w").close()
        return {}

    with open(filepath, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def write_json_file(filepath, data, encoder_cls=None):
    with open(filepath, 'w') as f:
        json.dump(data, f, cls=encoder_cls, indent=4)


def write_simulation_outputs(path, name_prefix, module, time_scale):
    all_data = {
        "scale": time_scale,
        "inputs": module.inVars,
        "outputs": module.outVars,
        "states": module.pStates,
        "times": module.pTimes,
        "global_vars": module.globVars,
        "vars": module.Vars
    }

    for fname, data in all_data.items():
        suffix = f"{name_prefix}_{fname}" if name_prefix else fname
        filepath = os.path.join(path, suffix)
        write_json_file(filepath, data, encoder_cls=MuteTypes.MuteEncoder)

    all_file = os.path.join(path, f"{name_prefix}_all" if name_prefix else "all")
    write_json_file(all_file, all_data, encoder_cls=MuteTypes.MuteEncoder)