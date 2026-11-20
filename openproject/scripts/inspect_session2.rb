session_class = ActionDispatch::Session::ActiveRecordStore::Session
puts "Session model: #{session_class}"
# Let's inspect an existing session
s = session_class.where(user_id: 18).last
if s
  puts "Found session: #{s.session_id}"
  puts "Data: #{s.data.inspect}"
end
