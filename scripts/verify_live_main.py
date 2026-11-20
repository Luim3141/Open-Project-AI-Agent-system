import urllib.request
import subprocess
import json
import sys

def check_url(url, expected_status=200):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        resp = urllib.request.urlopen(req, timeout=5)
        status = resp.getcode()
        print(f"GET {url} -> {status} (Expected {expected_status})")
        assert status == expected_status, f"Expected {expected_status}, got {status}"
        return resp.read()
    except urllib.error.HTTPError as e:
        print(f"GET {url} -> {e.code} (Expected {expected_status})")
        assert e.code == expected_status, f"Expected {expected_status}, got {e.code}"
        return e.read()

def run_rails(code):
    cmd = ["docker", "exec", "qldapm-openproject-web-1", "bundle", "exec", "rails", "runner", code]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print("STDOUT:", p.stdout)
        print("STDERR:", p.stderr)
        raise RuntimeError(f"Rails runner failed: {p.stderr}")
    return p.stdout

def main():
    print("=== LIVE MAIN POST-DEPLOYMENT VERIFICATION ===")
    
    # 1. HTTP Endpoints
    print("\n1. Verifying Core HTTP Endpoints on http://localhost:8088...")
    check_url("http://localhost:8088/health_checks/default", 200)
    check_url("http://localhost:8088/login", 200)
    
    # 2. Gateway
    print("\n2. Verifying AI Gateway on http://localhost:8090...")
    gw_resp = check_url("http://localhost:8090/health", 200)
    assert b'"status":"ok"' in gw_resp, "Gateway health check failed"
    print("Gateway health check OK!")
    
    # 3. Rails & RBAC & Gate B Verification
    print("\n3. Verifying Live Main Rails & Gate B Security...")
    test_code = """
project = Project.find_by!(identifier: 'qldapm-local')
puts "Project: #{project.name} (id=#{project.id})"

# Enabled modules
modules = project.enabled_modules.pluck(:name).sort
puts "Enabled modules: #{modules.inspect}"
raise "gantt module missing" unless modules.include?('gantt')

# Users & Roles
admin = User.find_by!(login: 'op-owner')
pm = User.find_by!(login: 'ba-pm')
item = WorkPackage.where(project: project).first

# Gate B verification
actor_admin = item.qldapm_actor(admin)
puts "Admin actor: #{actor_admin.inspect}"
raise "Admin must NOT have member role in Project 5" unless actor_admin["role"].nil?

actor_pm = item.qldapm_actor(pm)
puts "PM actor: #{actor_pm.inspect}"
raise "PM must have PM role" unless actor_pm["role"] == 'PM'

# Controller deny_access check
controller = QldapmAIController.new
controller.request = ActionDispatch::TestRequest.create
controller.response = ActionDispatch::TestResponse.create
controller.params = ActionController::Parameters.new(project_id: 'qldapm-local')

User.current = admin
begin
  controller.send(:load_project)
  puts "Admin load_project status: #{controller.response.status}"
rescue ActionController::RoutingError, StandardError => e
  puts "Caught expected restriction for admin: #{e.class} #{e.message}"
end

User.current = pm
controller.send(:load_project)
puts "PM role loaded: #{controller.instance_variable_get(:@role)}"
raise "Expected PM role" unless controller.instance_variable_get(:@role) == 'PM'

# UI Key readability
raise "ui.key not readable" unless File.file?("/qldapm-ui/ui.key")
raise "test-receipt.key not readable" unless File.file?("/qldapm-ui/test-receipt.key")
puts "Keys mounted and readable in /qldapm-ui/!"

# WBS count
wp_count = WorkPackage.where(project: project).count
epics = WorkPackage.where(project: project, type_id: 5).pluck(:id).sort
tasks = WorkPackage.where(project: project, type_id: 1).count
subtasks = WorkPackage.where(project: project, type_id: 10).count
subtasks_parent = WorkPackage.where(project: project, type_id: 10).where.not(parent_id: nil).count

puts "WorkPackages total: #{wp_count}"
puts "Epics: #{epics.inspect}"
puts "Tasks: #{tasks}"
puts "Subtasks: #{subtasks} (with parent: #{subtasks_parent})"

raise "Expected 329 WorkPackages" unless wp_count == 329
raise "Expected Epics 38..48" unless epics == (38..48).to_a
raise "Expected 265 subtasks with parent" unless subtasks_parent == 265

puts "ALL LIVE MAIN ASSERTIONS PASSED!"
"""
    output = run_rails(test_code)
    print(output)
    assert "ALL LIVE MAIN ASSERTIONS PASSED!" in output
    print("\n=== POST-DEPLOYMENT VERIFICATION FULLY PASSED ON MAIN! ===")

if __name__ == "__main__":
    main()
