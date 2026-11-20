require 'active_support/all'
require 'base64'
require 'pg'

conn = PG.connect(host: 'qldapm-openproject-db-1', user: 'postgres', password: 'PUBLICATION_REDACTED', dbname: 'openproject')
res = conn.exec('SELECT id, data FROM sessions WHERE id = 184')
row = res[0]
data = Marshal.load(Base64.decode64(row['data']))
data['user_id'] = 18
new_raw = Base64.strict_encode64(Marshal.dump(data))
conn.exec_params('UPDATE sessions SET user_id = 18, data = $1 WHERE id = 184', [new_raw])
puts 'UPDATED SESSION 184 TO USER 18 SUCCESSFULLY!'
