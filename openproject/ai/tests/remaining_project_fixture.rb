# New synthetic project only, for a real actor who belongs to two projects.
require 'json'
raise 'ISOLATED_ONLY' unless ENV['QLDAPM_QUALIFICATION']=='remaining-20261018' && URI(ENV.fetch('DATABASE_URL')).host=='rd-db'
data=JSON.parse(File.read('/qa/fixture-credentials.json'))
user=User.find(data.fetch('users').find{|r|r['role']=='PM'}.fetch('id'))
raise 'SYNTHETIC_USER_REQUIRED' unless user.login=='rd-fixture-pm' && !user.admin?
source=Project.find(data.fetch('project_id'))
project=Project.find_by(identifier:'rd-fixture-other')
ActiveRecord::Base.transaction do
  project ||= Project.create!(name:'RD Fixture Other',identifier:'rd-fixture-other',workspace_type:'project',public:false)
  source.project_types.each do |entry|
    ProjectType.find_or_create_by!(project:project,type:entry.type)
  end
  project.enabled_module_names=source.enabled_module_names
  project.work_package_custom_fields=source.work_package_custom_fields
  Member.create!(project:project,principal:user,roles:[Role.find_by!(name:'QLDAPM PM')]) unless Member.exists?(project:project,user_id:user.id)
end
File.write('/qa/other-project.json',JSON.generate({project_id:project.id,actor_id:user.id}))
puts 'NEW_PROJECT_FIXTURE_READY'
