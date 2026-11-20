require "json"
require "securerandom"
path = "/private/security-tokens.json"
if ENV["CLEANUP"] == "true"
  data = JSON.parse(File.read(path))
  Token::API.where(id: data.fetch("token_ids")).destroy_all
  User.find(data.fetch("outsider_id")).destroy!
  File.delete(path)
  puts "Temporary security-test credentials removed."
else
  raise "Previous security tokens need cleanup" if File.exist?(path)
  password = "Aa1!" + SecureRandom.hex(32)
  outsider = User.create!(login: "op-security-#{SecureRandom.hex(6)}", firstname: "Temporary", lastname: "Nonmember",
                          mail: "security-#{SecureRandom.hex(6)}@qldapm.local", status: :active,
                          password: password, password_confirmation: password)
  data = { "outsider_id" => outsider.id, "token_ids" => [], "tokens" => {} }
  users = %w[pm ba-pm be fe qa].map { |login| [login, User.find_by!(login:)] } + [["outsider", outsider]]
  users.each do |login, user|
    token = Token::API.create!(user:)
    data["token_ids"] << token.id
    data["tokens"][login] = token.plain_value
  end
  File.write(path, JSON.pretty_generate(data))
  puts "Temporary role and nonmember API tokens generated privately."
end
