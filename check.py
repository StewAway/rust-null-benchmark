import os
import json

base_dirs = ["results_none", "results_mq"]
patterns = ["seq_read", "seq_write", "rand_read", "rand_write"]
block_sizes = ["4k", "8k", "16k", "32k", "64k", "128k"]
numjobs = ["1", "2", "3", "4"]
drivers = ["c", "rust"]


errors = []

for base in base_dirs:
    for pattern in patterns:
        for bs in block_sizes:
            for nj in numjobs:
                for drv in drivers:
                    fname = f"{drv}_bs{bs}_jobs{nj}.json"
                    fpath = os.path.join(os.path.expanduser("."), base, pattern, fname)
                    if not os.path.exists(fpath):
                        errors.append((base, pattern, bs, nj, drv, "Missing file"))
                        continue
                    try:
                        with open(fpath) as f:
                            data = json.load(f)
                            if "jobs" not in data or "read" not in data["jobs"][0]:
                                errors.append((base, pattern, bs, nj, drv, "Missing read stats"))
                    except Exception as e:
                        errors.append((base, pattern, bs, nj, drv, f"JSON error: {str(e)}"))

if not errors:
    print("ALl FIO runs completed successfully!")
else:
    print(f"Detected {len(errors)} problems: \n");
    for sched, pattern, bs, nj, drv, msg in errors:
        print(f"[{sched}] {pattern}, bs={bs}, jobs={nj}, driver={drv} -> {msg}")
