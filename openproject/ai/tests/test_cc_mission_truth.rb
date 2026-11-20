require 'erb'
source=STDIN.read
card=source.split('          <!-- Card 3 -->',2).last.split('          <!-- Card 4 -->',2).first
prs=[{'is_merged'=>true,'merge_target'=>'MAIN','state'=>'closed'}, {'is_merged'=>true,'merge_target'=>'FEATURE_BRANCH (test)','state'=>'closed'}, {'is_merged'=>false,'state'=>'open'}]
html=ERB.new(card).result_with_hash(github_prs:prs)
raise 'HARDCODED_PR_COUNTS' unless html.include?('1 merged main') && html.include?('1 merged feature') && html.include?('1 open')
raise 'HARDCODED_PIPELINE_SUCCESS' if source.include?('Pipeline Healthy') || source.include?('WP #384 Patch') || source.include?('CITATIONS OK')
puts 'PASS Mission PR counts derive from data; no unconditional pipeline/Native/RAG success'
