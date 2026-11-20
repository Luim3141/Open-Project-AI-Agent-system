Rails.application.routes.routes.select { |r| r.path.spec.to_s.include?('qldapm') }.each do |r|
  puts "#{r.verb} #{r.path.spec.to_s} => #{r.defaults}"
end
