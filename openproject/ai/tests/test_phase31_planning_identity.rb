require 'action_view'
require 'active_support/all'
require 'json'
require 'nokogiri'

path=File.expand_path('../core/overlay/app/views/qldapm_ai/_engineering_plans.html.erb',__dir__)
plans=[{'id'=>'plan-a','native_id'=>379,'native_units'=>{'csv'=>{'id'=>391}},'state'=>'PUBLISHED','created_at'=>1},
       {'id'=>'plan-b','native_id'=>379,'native_units'=>{'summary'=>{'id'=>390}},'state'=>'PUBLISHED','created_at'=>2}]
view=ActionView::Base.with_empty_template_cache.empty
html=view.render(inline:File.read(path),locals:{plans:plans,eng:{'backlog'=>[]},format_vn_time:->(_){'fixture-date'}})
doc=Nokogiri::HTML.fragment(html)
raise 'PLAN_GROUPED_BY_PARENT_INSTEAD_OF_CHILD' unless doc.css('h4').map(&:text).any?{|t|t.include?('WP #391')} && doc.css('h4').map(&:text).any?{|t|t.include?('WP #390')}
matches=doc.css('[data-plan-group]').select{|node|node['data-search'].include?('plan-a')}
raise 'SEARCH_SHOWS_UNRELATED_VERSION' unless matches.size==1 && !matches.first['data-search'].include?('plan-b')
raise 'BROKEN_PLAN_SEARCH_ATTRIBUTE' unless doc.css('article[data-plan-group][data-search]').size==2
puts 'PASS real ERB plan child identity, independent search rows and valid DOM attributes'
