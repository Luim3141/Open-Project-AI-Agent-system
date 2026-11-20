import subprocess

sql = """
UPDATE user_passwords SET hashed_password = 'PUBLICATION_REDACTED' WHERE user_id = 5;
UPDATE users SET failed_login_count = 0 WHERE id = 5;
"""

res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-db-1", "psql", "-U", "postgres", "-d", "openproject"],
    input=sql, text=True, capture_output=True, check=True
)
print("STDOUT:", res.stdout)
