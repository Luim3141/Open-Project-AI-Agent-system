# frozen_string_literal: true

require 'uri'
require 'commonmarker'
require 'rails-html-sanitizer'
require 'json'

module QldapmReportReaderHelper
  def qldapm_report_document(data)
    raw = qldapm_report_narrative(data)
    if raw.empty? && data.is_a?(Hash) && data['report_type']=='WORKFLOW_AUDIT' && !data['data_hidden']
      audit = data.select { |key,_| %w[id project_id title generated_at report_type narrative_status facts provenance].include?(key) }
      raw = "# Bản ghi audit đã lưu\n\nBáo cáo này không có narrative. Dưới đây là facts và provenance đã lưu, không phải nhận định AI.\n\n" + JSON.pretty_generate(audit).lines.map { |line| "    #{line}" }.join
    end
    html = Commonmarker.to_html(raw, options: {render: {unsafe: false}, extension: {table: true}}, plugins: {syntax_highlighter: nil})
    safe = Rails::Html::SafeListSanitizer.new.sanitize(html,
      tags: %w[h1 h2 h3 h4 h5 h6 p br strong em del ul ol li table thead tbody tr th td a pre code blockquote hr],
      attributes: %w[href title start colspan rowspan])
    document = Nokogiri::HTML.fragment(safe)
    document.css('a').each do |link|
      href = link['href'].to_s
      uri = URI.parse(href) rescue nil
      native = href.match?(%r{\A/(?:work_packages/[1-9]\d*(?:/activity)?|projects/[a-zA-Z0-9_-]+(?:/work_packages)?)\z})
      github = uri && uri.scheme == 'https' && uri.host == 'github.com' && uri.userinfo.nil? && uri.port == 443 && uri.query.nil?
      if native || github
        link['rel'] = 'noopener noreferrer'
      else
        link.remove_attribute('href')
      end
    end
    document.css('h1,h2,h3,h4,h5,h6').each_with_index { |heading, index| heading['id'] = "report-section-#{index + 1}" }
    {'raw_markdown' => raw, 'rendered_html' => document.to_html, 'rendering' => 'COMMONMARK_SANITIZED'}
  end

  private

  def qldapm_report_narrative(data)
    return data == 'Không có nội dung chi tiết.' ? '' : data if data.is_a?(String)
    return '' unless data.is_a?(Hash)
    %w[narrative document content text].each do |key|
      found = qldapm_report_narrative(data[key])
      return found unless found.empty?
    end
    ''
  end
end
