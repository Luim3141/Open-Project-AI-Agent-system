import json
import sys
from pathlib import Path
from gateway.native import Native, NativeError

runtime = Path(sys.argv[1]) / "stage"
credentials = json.loads((runtime / "test-credentials.json").read_text())
project = json.loads((runtime / "bootstrap.json").read_text())["project_id"]
results = {}
for role, credential in credentials.items():
    native = Native("http://127.0.0.1:18091", credential["token"], project)
    try:
        value = native.call("/api/v3/qldapm/configuration")
        assert role == "PM" and value["project_id"] == project and value["settings"]["login_required"]
        assert "password" not in value and "credentials" not in value
        results[role] = 200
    except NativeError as error:
        assert role != "PM" and error.status == 403, str(error)
        results[role] = 403
print(json.dumps({"passed": True, "synthetic_only": True, "configuration_roles": results}))
