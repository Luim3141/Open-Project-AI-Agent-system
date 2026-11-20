require "digest"
Dir.glob("/trusted/overlay/**/*").select { |path| File.file?(path) }.sort.each do |path|
  image_path = path.sub("/trusted/overlay/", "/app/")
  raise "IMAGE_SOURCE_MISMATCH: #{image_path}" unless File.file?(image_path) && Digest::SHA256.file(path).hexdigest == Digest::SHA256.file(image_path).hexdigest
end
puts "Immutable image overlay matches trusted candidate."
