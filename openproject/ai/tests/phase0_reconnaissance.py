import subprocess

# 1. Check table names related to two_factor or devices or backup
res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-db-1", "psql", "-U", "postgres", "-d", "openproject", "-t", "-c",
     "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND (table_name LIKE '%two_factor%' OR table_name LIKE '%device%' OR table_name LIKE '%backup%' OR table_name LIKE '%otp%');"],
    capture_output=True, text=True
)
print("Matching tables:\n", res.stdout.strip())

# 2. Check structure of two_factor_authentication_devices
res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-db-1", "psql", "-U", "postgres", "-d", "openproject", "-c",
     "\\d two_factor_authentication_devices"],
    capture_output=True, text=True
)
print("two_factor_authentication_devices structure:\n", res.stdout.strip())

# 3. List all users and their two_factor_authentication_devices
query_users = """
SELECT 
    u.id,
    u.login,
    u.mail,
    u.status,
    u.admin,
    COALESCE(string_agg(DISTINCT r.name, ', '), 'No Membership') AS project_roles,
    COUNT(d.id) AS total_devices,
    COUNT(d.id) FILTER (WHERE d.type = 'TwoFactorAuthentication::Device::Totp' AND d.active = true) AS active_totp,
    COUNT(d.id) FILTER (WHERE d.type = 'TwoFactorAuthentication::Device::Totp' AND d.active = false) AS inactive_totp,
    COUNT(d.id) FILTER (WHERE d.type != 'TwoFactorAuthentication::Device::Totp') AS other_devices
FROM users u
LEFT JOIN members m ON m.user_id = u.id AND m.project_id = 3
LEFT JOIN member_roles mr ON mr.member_id = m.id
LEFT JOIN roles r ON r.id = mr.role_id
LEFT JOIN two_factor_authentication_devices d ON d.user_id = u.id
WHERE u.type = 'User'
GROUP BY u.id, u.login, u.mail, u.status, u.admin
ORDER BY u.id;
"""
res = subprocess.run(
    ["docker", "exec", "-i", "qldapm-ai-stage-db-1", "psql", "-U", "postgres", "-d", "openproject", "-c", query_users],
    capture_output=True, text=True
)
print("User Roster & 2FA Device Inventory:\n", res.stdout.strip())
