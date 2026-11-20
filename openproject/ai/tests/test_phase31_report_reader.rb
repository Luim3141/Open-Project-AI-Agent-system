require 'commonmarker'
require 'action_view'
require 'nokogiri'
require_relative '../core/overlay/app/helpers/qldapm_report_reader_helper'

reader = Object.new.extend(QldapmReportReaderHelper)
text = "# Báo cáo\n\n## Kết quả\n\n**Đã lưu** và *chờ kiểm tra*.\n\n1. Một\n2. Hai\n\n- Task\n\n| WP | Status |\n| --- | --- |\n| 391 | BLOCKED |\n\n> Chưa hoàn tất\n\n```ruby\nputs '<script>'\n```\n\n---\n\n[WP](/work_packages/391) [PR](https://github.com/a/b/pull/1) [bad](javascript:alert(1))\n\n<script>alert('x')</script> <img src=x onerror=alert(1)>\n"
result = reader.qldapm_report_document({'document' => {'narrative' => text}})
raise 'RAW_NOT_PRESERVED' unless result['raw_markdown'] == text
doc = Nokogiri::HTML.fragment(result['rendered_html'])
%w[h1 h2 strong em ol ul table blockquote pre code hr].each { |tag| raise "MISSING_#{tag}" unless doc.at_css(tag) }
raise 'XSS' if doc.at_css('script,img,iframe,[onerror],[onclick],style')
raise 'UNSAFE_LINK' if doc.css('a[href]').any? { |a| a['href'].match?(/javascript:|data:|\/\//) && !a['href'].start_with?('https://github.com/') }
raise 'GOOD_LINK_REMOVED' unless doc.at_css('a[href="/work_packages/391"]') && doc.at_css('a[href="https://github.com/a/b/pull/1"]')
raise 'TOC_IDS_MISSING' unless doc.css('h1,h2,h3').map { |h| h['id'] } == ['report-section-1', 'report-section-2']
bad = reader.qldapm_report_document({'narrative' => "## [broken\n\n[credentials](https://user:secret@github.com/a) [foreign](https://evil.example/) [relative](//evil.example/) [op](/work_packages/391/activity)"})
bad_doc = Nokogiri::HTML.fragment(bad['rendered_html'])
raise 'CREDENTIAL_OR_FOREIGN_LINK' unless bad_doc.css('a[href]').map { |a| a['href'] } == ['/work_packages/391/activity']
raise 'EMPTY_NARRATIVE' unless reader.qldapm_report_document({})['raw_markdown'] == ''
audit={'id'=>'audit','report_type'=>'WORKFLOW_AUDIT','title'=>'Native audit','narrative'=>nil,'facts'=>{'native_id'=>395,'lock_version'=>3,'note'=>'<script>unsafe</script>'},'provenance'=>{'correlation_id'=>'trace-fixture'}}
audit_render=reader.qldapm_report_document(audit)
raise 'AUDIT_FACTS_MISSING' unless audit_render['rendered_html'].include?('lock_version') && audit_render['rendered_html'].include?('trace-fixture')
raise 'AUDIT_FACTS_UNSAFE' if Nokogiri::HTML.fragment(audit_render['rendered_html']).at_css('script')
raise 'AUDIT_WAS_MUTATED' unless audit['narrative'].nil?
raise 'HIDDEN_AUDIT_LEAKED' unless reader.qldapm_report_document(audit.merge('data_hidden'=>true))['raw_markdown']==''
long = "# Long report\n\n" + (1..80).map { |n| "## Phần #{n}\n\n" + ('Nội dung tiếng Việt **có nguồn**. ' * 15) + "\n\n| ID | Status |\n| --- | --- |\n| #{n} | UNKNOWN |\n" }.join("\n")
long_doc = Nokogiri::HTML.fragment(reader.qldapm_report_document({'narrative' => long})['rendered_html'])
raise 'LONG_DOCUMENT_TRUNCATED' unless long.size > 10_000 && long_doc.css('h2').size == 80 && long_doc.css('table').size == 80
puts 'PASS Markdown structure, tables, exact raw, TOC headings, malformed Markdown, HTML/XSS and URL allowlist'
