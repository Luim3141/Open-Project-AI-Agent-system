import json

with open("docs/ai/GEMINI_FULL_FEATURE_COMPLETENESS_MATRIX.json", "r", encoding="utf-8") as f:
    data = json.load(f)

subsystems = data["subsystems"]
print(f"Total subsystems: {len(subsystems)}\n")

for idx, (k, v) in enumerate(subsystems.items()):
    name = v.get("name", k)
    status = v.get("status", "UNKNOWN")
    missing = v.get("missing_features", [])
    print(f"{idx+1:2d}. [{k}] - {name}")
    print(f"    Status: {status}")
    if missing:
        print(f"    Missing: {missing}")
    print()
