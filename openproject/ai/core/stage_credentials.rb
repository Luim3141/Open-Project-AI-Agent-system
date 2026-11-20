require "json"
raise "STAGING_ONLY" unless User.exists?(login: "stage-owner") && !User.exists?(login: "op-owner")
project = Project.find_by!(identifier: "qldapm-local")
credentials = project.members.includes(:roles).to_h do |member|
  token = Token::API.create_and_return_value(member.principal)
  [member.roles.first.name.delete_prefix("QLDAPM "), {"id" => member.user_id, "token" => token}]
end
File.write("/private/test-credentials.json", JSON.generate(credentials))
puts "Synthetic staging API credentials prepared locally; no production credentials used."
