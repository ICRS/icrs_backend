import json
import os

os.makedirs("../assets/filament/", exist_ok=True)
os.makedirs("../assets/machine/", exist_ok=True)
os.makedirs("../assets/process/", exist_ok=True)


def merge_json(initial_filament_folder,
               filament_bbl_path,
               filament_name, output_path="../assets/",
               additional_params=None):
    with open(initial_filament_folder + filament_name, "r") as f:
        d = json.load(f)

    json_list = [d]
    inherits = d["inherits"]
    while inherits:
        print(inherits)
        with open(filament_bbl_path + inherits + ".json", "r") as ff:
            json_list.append(json.load(ff))
            inherits = json_list[-1].get("inherits", None)

    merged = {}
    for j in reversed(json_list):
        merged.update(j)

    merged.pop("inherits", None)
    if additional_params:
        merged.update(additional_params)

    json.dump(merged, open(output_path + filament_name, "w"), indent=4)


filament_p1p_path = "BBL/filament/P1P/"
filament_bbl_path = "BBL/filament/"

generic_pla_p1p = "Generic PLA @BBL P1P.json"
generic_pla = "Generic PLA.json"

merge_json(filament_p1p_path, filament_bbl_path, generic_pla_p1p,
           output_path="../assets/filament/")
merge_json(filament_bbl_path, filament_bbl_path, generic_pla,
           output_path="../assets/filament/")


machine_path = "BBL/machine/"

machines = [
    "Bambu Lab P1P 0.4 nozzle.json",
    "Bambu Lab P1S 0.4 nozzle.json",
]

for machine in machines:
    merge_json(machine_path, machine_path, machine,
               output_path="../assets/machine/")


process_path = "BBL/process/"

processes = sorted([
    s for s in os.listdir(process_path) if ("P1P" in s or "X1C" in s)
    and "nozzle" not in s
])

additional_process_params = {
    "enable_support": "1",
    "from": "User",
    "is_custom_defined": "0",
    "sparse_infill_density": "15",
    "support_type": "tree(auto)",
}

for process in processes:
    merge_json(process_path, process_path, process,
               output_path="../assets/process/",
               additional_params=additional_process_params)
