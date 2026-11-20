require 'digest'
require 'json'
require 'tmpdir'
require 'fileutils'
require_relative 'overlay/app/services/qldapm/application_qa_sources'

Dir.mktmpdir do |root|
  paths=Qldapm::ApplicationQaSources::PATHS
  paths.each do |path|
    target=File.join(root,path)
    FileUtils.mkdir_p(File.dirname(target))
    File.write(target,"fixture #{path}")
  end
  hashes=Qldapm::ApplicationQaSources.read(root)
  raise 'SOURCE_PATHS_CHANGED' unless hashes.keys.sort == paths.sort
  raise 'SOURCE_HASH_MISMATCH' unless hashes.all? { |path,hash| hash == Digest::SHA256.file(File.join(root,path)).hexdigest }
  File.delete(File.join(root,paths.first))
  begin
    Qldapm::ApplicationQaSources.read(root)
    raise 'MISSING_SOURCE_ACCEPTED'
  rescue Errno::ENOENT
  end
end
puts JSON.generate({application_qa_sources:'PASS', fixed_paths:true, missing_source_fails:true})
