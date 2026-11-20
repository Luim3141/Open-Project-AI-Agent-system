import json
import subprocess

def inspect_container(name):
    r = subprocess.run(["docker", "inspect", name], capture_output=True, text=True, check=True)
    info = json.loads(r.stdout)[0]
    return {
        "Name": info.get("Name"),
        "Id": info.get("Id"),
        "Created": info.get("Created"),
        "Image": info.get("Image"),
        "ConfigImage": info.get("Config", {}).get("Image"),
        "Status": info.get("State", {}).get("Status"),
        "Health": info.get("State", {}).get("Health", {}).get("Status"),
        "Ports": info.get("NetworkSettings", {}).get("Ports"),
        "RestartPolicy": info.get("HostConfig", {}).get("RestartPolicy"),
        "Mounts": [{"Source": m.get("Source"), "Destination": m.get("Destination"), "Mode": m.get("Mode"), "RW": m.get("RW")} for m in info.get("Mounts", [])]
    }

ps = subprocess.run(["docker", "ps", "--format", "{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"], capture_output=True, text=True).stdout
print("=== DOCKER PS ===")
print(ps)

print("=== INSPECT GATEWAY ===")
print(json.dumps(inspect_container("qldapm-ai-gateway-1"), indent=2))

print("=== INSPECT CORE (OPENPROJECT WEB) ===")
print(json.dumps(inspect_container("qldapm-openproject-web-1"), indent=2))
