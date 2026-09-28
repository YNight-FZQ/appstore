#!/usr/bin/env ruby
# frozen_string_literal: true

require 'fileutils'
require 'optparse'
require 'tmpdir'
require 'yaml'

repo_root = File.expand_path('../../../..', __dir__)
options = { output: File.join(repo_root, 'apps'), type: 'website' }
parser = OptionParser.new do |args|
  args.banner = '用法：ruby new_app.rb --key 标识 --name 名称 --version 版本 --image 镜像 --container-port 端口 --host-port 端口 --logo 图标 --tag 分类 --arch 架构'
  args.on('--key VALUE', '应用标识，例如 my-app') { |value| options[:key] = value }
  args.on('--name VALUE', '应用显示名称') { |value| options[:name] = value }
  args.on('--version VALUE', '应用包版本') { |value| options[:version] = value }
  args.on('--image VALUE', '已核实的容器镜像及标签') { |value| options[:image] = value }
  args.on('--container-port NUMBER', Integer, '容器内 HTTP 端口') { |value| options[:container_port] = value }
  args.on('--host-port NUMBER', Integer, '默认宿主机 HTTP 端口') { |value| options[:host_port] = value }
  args.on('--logo PATH', '应用自身的 PNG 图标') { |value| options[:logo] = value }
  args.on('--tag KEY', '仓库 data.yaml 中的分类键') { |value| options[:tag] = value }
  args.on('--arch LIST', '已核实的镜像架构，逗号分隔') { |value| options[:arch] = value }
  args.on('--description-zh VALUE', '中文简介') { |value| options[:description_zh] = value }
  args.on('--description-en VALUE', '英文简介，省略时使用中文') { |value| options[:description_en] = value }
  args.on('--type VALUE', '应用类型：website、tool、runtime 或 node') { |value| options[:type] = value }
  args.on('--website URL', '应用官网') { |value| options[:website] = value }
  args.on('--github URL', '应用官方仓库') { |value| options[:github] = value }
  args.on('--document URL', '应用官方文档') { |value| options[:document] = value }
  args.on('--output PATH', '输出 apps 目录，默认当前仓库的 apps') { |value| options[:output] = value }
  args.on('-h', '--help', '显示帮助') do
    puts args
    exit 0
  end
end

begin
  parser.parse!(ARGV)
  raise ArgumentError, "不认识的参数：#{ARGV.join(' ')}" unless ARGV.empty?

  required = %i[key name version image container_port host_port logo tag arch description_zh]
  missing = required.select { |key| options[key].nil? || options[key].to_s.empty? }
  raise ArgumentError, "缺少参数：#{missing.join('、')}" unless missing.empty?
  raise ArgumentError, '应用标识只能使用小写字母、数字和中划线' unless options[:key].match?(/\A[a-z0-9]+(?:-[a-z0-9]+)*\z/)
  raise ArgumentError, '版本不能包含路径字符' unless options[:version].match?(/\A[a-zA-Z0-9][a-zA-Z0-9._-]*\z/)
  raise ArgumentError, '应用类型无效' unless %w[website tool runtime node].include?(options[:type])
  %i[container_port host_port].each do |key|
    raise ArgumentError, "#{key} 必须在 1 到 65535 之间" unless (1..65_535).cover?(options[key])
  end
  raise ArgumentError, '图标文件不存在' unless File.file?(options[:logo])
  raise ArgumentError, '图标必须是 PNG 文件' unless File.binread(options[:logo], 8) == "\x89PNG\r\n\x1A\n".b

  architectures = options[:arch].split(',').map(&:strip).reject(&:empty?).uniq
  raise ArgumentError, '至少需要一个已核实的镜像架构' if architectures.empty?

  catalog = YAML.load_file(File.join(repo_root, 'data.yaml'))
  tags = catalog.dig('additionalProperties', 'tags') || []
  tag = tags.find { |item| item['key'] == options[:tag] }
  raise ArgumentError, "分类键不存在：#{options[:tag]}" unless tag

  output = File.expand_path(options[:output])
  FileUtils.mkdir_p(output)
  target = File.join(output, options[:key])
  raise ArgumentError, "应用目录已存在：#{target}" if File.exist?(target)

  description_en = options[:description_en] || options[:description_zh]
  properties = {
    'key' => options[:key], 'name' => options[:name], 'tags' => [options[:tag]],
    'shortDescZh' => options[:description_zh], 'shortDescEn' => description_en,
    'description' => { 'zh' => options[:description_zh], 'en' => description_en },
    'type' => options[:type], 'crossVersionUpdate' => false, 'limit' => 0,
    'recommend' => 0, 'architectures' => architectures
  }
  %i[website github document].each { |key| properties[key.to_s] = options[key] if options[key] }
  root_data = {
    'name' => options[:name], 'tags' => [tag['name']],
    'title' => options[:description_zh], 'description' => options[:description_zh],
    'additionalProperties' => properties
  }
  version_data = {
    'additionalProperties' => {
      'formFields' => [{
        'default' => options[:host_port], 'envKey' => 'PANEL_APP_PORT_HTTP',
        'edit' => true, 'required' => true, 'rule' => 'paramPort', 'type' => 'number',
        'labelZh' => 'HTTP 端口', 'labelEn' => 'HTTP Port',
        'label' => { 'zh' => 'HTTP 端口', 'en' => 'HTTP Port' }
      }]
    }
  }
  compose = {
    'services' => {
      options[:key] => {
        'image' => options[:image], 'container_name' => '${CONTAINER_NAME}',
        'restart' => 'unless-stopped',
        'ports' => ["${PANEL_APP_PORT_HTTP}:#{options[:container_port]}"],
        'networks' => ['1panel-network'], 'labels' => { 'createdBy' => 'Apps' }
      }
    },
    'networks' => { '1panel-network' => { 'external' => true } }
  }

  Dir.mktmpdir(".#{options[:key]}-", output) do |work_dir|
    package_dir = File.join(work_dir, options[:key])
    version_dir = File.join(package_dir, options[:version])
    FileUtils.mkdir_p(version_dir)
    File.write(File.join(package_dir, 'data.yml'), YAML.dump(root_data))
    File.write(File.join(version_dir, 'data.yml'), YAML.dump(version_data))
    File.write(File.join(version_dir, 'docker-compose.yml'), YAML.dump(compose))
    File.write(File.join(package_dir, 'README.md'), "## 产品介绍\n\n#{options[:description_zh]}\n")
    FileUtils.cp(options[:logo], File.join(package_dir, 'logo.png'))
    raise ArgumentError, "应用目录已存在：#{target}" if File.exist?(target)

    File.rename(package_dir, target)
  end
  puts "已创建：#{target}"
  puts '请根据应用官方部署资料补齐数据卷、环境变量、依赖和健康检查，再运行 check_app.rb。'
rescue OptionParser::ParseError, ArgumentError, Errno::ENOENT => error
  warn "错误：#{error.message}"
  warn parser
  exit 2
end
