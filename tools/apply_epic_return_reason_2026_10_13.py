"""Apply only the owner's exact approved Return7 preview; guarded, no retries."""
import json
import jira_admin_mcp as admin

result = admin.apply_change('71c5c04c-95ae-4d96-afaf-ea972aa7c53b',
                          '80f931a5255e4fd8962000f901b380554fd692bca432d8bb39a39f5dda62afc5')
print(json.dumps({'status': result.get('status'),
                  'version': result.get('workflow', {}).get('workflows', [{}])[0].get('version')}))
