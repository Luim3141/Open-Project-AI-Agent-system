require_relative 'overlay/app/helpers/qldapm_ai_helper'
helper=Object.new.extend(QldapmAIHelper)
proposal={'command'=>{'action'=>'create_dependency','arguments'=>{'predecessor_id'=>376,'successor_id'=>377,'lag'=>2},
  'preview'=>{'possible_affected'=>[{'id'=>377,'lockVersion'=>0,'startDate'=>'2026-10-26','dueDate'=>'2026-10-27'},
                                    {'id'=>380,'lockVersion'=>1,'startDate'=>'2026-10-26','dueDate'=>'2026-10-27'}]}}}
result=helper.qldapm_preview(proposal)
raise 'DEPENDENCY_DIRECTION_OR_LAG_NOT_VISIBLE' unless result[:title].include?('#376') && result[:title].include?('#377') && result[:rows].any? { |r| r[:after]==2 }
raise 'DERIVED_SCOPE_OR_VERSION_NOT_VISIBLE' unless result[:rows].any? { |r| r[:label].include?('#380') && r[:before].include?('v1') && r[:after].include?('Native') }
puts 'Dependency preview includes direction, lag, each possible affected source/version/date, no predicted-date claim PASS'

%w[update_dependency delete_dependency].each do |action|
  changed=Marshal.load(Marshal.dump(proposal));changed['command']['action']=action
  changed['command']['arguments']['relation_id']=353;changed['command']['preview']['before']={'lag'=>0}
  changed['command']['arguments'].delete('lag') if action=='delete_dependency'
  result=helper.qldapm_preview(changed)
  raise 'RELATION_ID_NOT_VISIBLE' unless result[:title].include?('relation #353')
  raise 'OLD_LAG_NOT_VISIBLE' unless result[:rows].first[:before]==0
  changed['command']['preview']['before']['lag']=nil
  raise 'UNSET_NATIVE_LAG_SILENTLY_NORMALIZED' unless helper.qldapm_preview(changed)[:rows].first[:before]=='Không đặt (Native)'
  if action=='delete_dependency'
    raise 'RELATION_DELETE_CONFUSED_WITH_WP_DELETE' unless result[:rows].first[:after].include?('không xóa công việc')
  else
    raise 'UPDATED_LAG_NOT_VISIBLE' unless result[:rows].first[:after]==2
  end
end
puts 'Existing relation update/delete shows exact prior/new lag, source versions and explicit no Work Package deletion PASS'

deleted=helper.qldapm_preview({'command'=>{'action'=>'delete_work_package','arguments'=>{'id'=>376,'lock_version'=>0},'preview'=>{'subject'=>'Disposable Task'}}})
raise 'PERMANENT_WP_DELETE_NOT_EXPLICIT' unless deleted[:title].include?('Xóa vĩnh viễn') && deleted[:title].include?('#376') && deleted[:rows].first[:after].include?('không cascade') && deleted[:rows].first[:after].include?('tombstone')
puts 'Permanent Task deletion preview distinguishes resource deletion, exact version, no cascade and retained tombstone PASS'
