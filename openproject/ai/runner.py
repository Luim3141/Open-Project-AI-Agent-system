"""Host-only fixed-suite runner with a disposable database containing synthetic staging data."""
import json
import re
import subprocess
import time
from pathlib import Path


def isolated_core(snapshot, identifier, runtime, images=None, suite="core-integration"):
    scripts = {"core-integration": "/trusted/integration.rb",
               "jira-sync-configuration": "/trusted/jira_sync_configuration_test.rb"}
    if suite not in scripts:
        raise ValueError("FIXED_TEST_SUITE_REQUIRED")
    if not re.fullmatch(r"[a-f0-9-]{36}", identifier):
        raise ValueError("INVALID_RUN_ID")
    root = Path(__file__).resolve().parent
    images = images or json.loads((Path(runtime) / "image-lock.json").read_text())
    if (not re.fullmatch(r"sha256:[a-f0-9]{64}", images["CORE_IMAGE"]) or
            not re.fullmatch(r"(?:postgres@)?sha256:[a-f0-9]{64}", images["POSTGRES_IMAGE"])):
        raise ValueError("PINNED_TEST_IMAGES_REQUIRED")
    name = "qldapm-ai-test-" + identifier
    database, network = name + "-db", name + "-net"
    created_database = created_network = False

    def command(argv, **kwargs):
        result = subprocess.run(argv, capture_output=True, timeout=600, **kwargs)
        if result.returncode:
            details = result.stderr.decode(errors="replace")
            raise RuntimeError("SANDBOX_COMMAND_FAILED: " + details[:2500] + "\n...\n" + details[-1000:])
        return result.stdout

    try:
        labels = command(["docker", "inspect", "--format", '{{index .Config.Labels "com.docker.compose.project"}}',
                          "qldapm-ai-stage-db-1"]).decode().strip()
        if labels != "qldapm-ai-stage":
            raise ValueError("SYNTHETIC_STAGE_DATABASE_REQUIRED")
        dump = command(["docker", "exec", "qldapm-ai-stage-db-1", "pg_dump", "-U", "postgres", "-Fc", "openproject"])
        command(["docker", "network", "create", "--internal", "--label", "org.qldapm.test=" + identifier, network])
        created_network = True
        command(["docker", "run", "-d", "--rm", "--name", database, "--label", "org.qldapm.test=" + identifier,
                 "--network", network, "--network-alias", "testdb", "--user", "postgres", "--read-only",
                 "--tmpfs", "/tmp:size=512m,mode=1777", "--tmpfs", "/var/run/postgresql:mode=1777",
                 "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true", "--memory", "768m", "--cpus", "1",
                 "--pids-limit", "128", "-e", "PGDATA=/tmp/postgres", "-e", "POSTGRES_DB=openproject",
                 "-e", "POSTGRES_HOST_AUTH_METHOD=trust", images["POSTGRES_IMAGE"]])
        created_database = True
        for attempt in range(60):
            ready = subprocess.run(["docker", "exec", database, "pg_isready", "-U", "postgres", "-d", "openproject"],
                                   capture_output=True, timeout=10)
            if ready.returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError("TEST_DATABASE_TIMEOUT")
        command(["docker", "exec", "-i", database, "pg_restore", "-U", "postgres", "--no-owner", "--exit-on-error",
                 "-d", "openproject"], input=dump)
        base = ["docker", "run", "--rm", "--name", name, "--label", "org.qldapm.test=" + identifier,
                "--network", network, "--user", "1000:1000", "--read-only", "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges:true", "--cpus", "2", "--memory", "4g", "--pids-limit", "256",
                "--tmpfs", "/tmp:size=128m,mode=1777", "--tmpfs", "/app/tmp:size=128m,mode=1777",
                "--tmpfs", "/app/log:size=32m,mode=1777", "-e", "QLDAPM_TEST_ONLY=true", "-e", "RAILS_ENV=production",
                "-e", "DATABASE_URL=postgres://postgres@testdb/openproject", "-e", "OPENPROJECT_HOST__NAME=localhost:8088",
                "-e", "OPENPROJECT_RAILS__CACHE__STORE=file_store", "-e", "SECRET_KEY_BASE=synthetic-disposable-test-only-" + "0" * 96,
                "--mount", f"type=bind,source={root / 'core'},target=/trusted,readonly", "--entrypoint", "bundle"]
        if suite == "core-integration":
            for folder in ("app", "config", "db", "lib", "lib_static"):
                base += ["--mount", f"type=bind,source={Path(snapshot) / folder},target=/app/{folder},readonly"]
        # Configuration rehearsal qualifies the pinned running image, not a
        # Windows checkout (whose CRLF templates are not a build artifact).
        # The base image pins dependencies; actor-authored Compose/commands/Gemfiles are never executed by the broker.
        command(base + [images["CORE_IMAGE"], "exec", "rails", "db:migrate"])
        output = command(base + [images["CORE_IMAGE"], "exec", "rails", "runner", scripts[suite]])
        return output.decode(errors="replace")[-64000:]
    finally:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=30)
        if created_database:
            subprocess.run(["docker", "rm", "-f", database], capture_output=True, timeout=30)
        if created_network:
            subprocess.run(["docker", "network", "rm", network], capture_output=True, timeout=30)
