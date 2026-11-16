#!/usr/bin/env ruby
# frozen_string_literal: true

require 'yaml'

package_dir = ARGV.fetch(0) do
  warn '用法：ruby check_app.rb apps/<应用标识>'
  exit 2
end
package_dir = File.expand_path(package_dir)
unless Dir.exist?(package_dir)
  warn "错误：应用目录不存在：#{package_dir}"
  exit 2
end
errors = []
warnings = []

read_yaml = lambda do |path|
  begin
    YAML.load_file(path)
  rescue Psych::Exception, Errno::ENOENT => error
    errors << "无法读取 #{path}：#{error.message}"
    nil
  end
end

root = read_yaml.call(File.join(package_dir, 'data.yml'))
logo = File.join(package_dir, 'logo.png')
errors << '缺少有效的 logo.png' unless File.file?(logo) && File.binread(logo, 8) == "\x89PNG\r\n\x1A\n".b
warnings << '缺少 README.md' unless File.file?(File.join(package_dir, 'README.md'))
if root.is_a?(Hash)
  properties = root['additionalProperties'] || {}
  errors << '根 data.yml 的 key 与目录名不一致' unless properties['key'] == File.basename(package_dir)
  errors << '根 data.yml 缺少 name' if properties['name'].to_s.empty?
  errors << '根 data.yml 缺少 tags' if !properties['tags'].is_a?(Array) || properties['tags'].empty?
end

versions = Dir.children(package_dir).select { |name| File.directory?(File.join(package_dir, name)) }.sort
errors << '至少需要一个版本目录' if versions.empty?
versions.each do |version|
  version_dir = File.join(package_dir, version)
  data = read_yaml.call(File.join(version_dir, 'data.yml'))
  compose_path = File.join(version_dir, 'docker-compose.yml')
  compose = read_yaml.call(compose_path)
  next unless data.is_a?(Hash) && compose.is_a?(Hash)

  fields = data.dig('additionalProperties', 'formFields')
  unless fields.is_a?(Array)
    errors << "#{version}：formFields 必须是数组"
    next
  end
  field_keys = []
  fields.each do |field|
    unless field.is_a?(Hash)
      errors << "#{version}：表单字段必须是映射"
      next
    end
    key = field['envKey']
    errors << "#{version}：envKey 无效：#{key.inspect}" unless key.is_a?(String) && key.match?(/\A[A-Za-z_][A-Za-z0-9_]*\z/)
    errors << "#{version}：字段含空值：#{key}" if field.values.any?(&:nil?)
    errors << "#{version}：重复的 envKey：#{key}" if field_keys.include?(key)
    field_keys << key
    type = field['type']
    errors << "#{version}：不支持的字段类型 #{type.inspect}：#{key}" unless %w[text number password select service apps].include?(type)
    if type == 'select' || type == 'apps'
      errors << "#{version}：#{key} 缺少 values" unless field['values'].is_a?(Array) && !field['values'].empty?
    end
    errors << "#{version}：#{key} 缺少服务 key" if type == 'service' && field['key'].to_s.empty?
    if type == 'apps'
      child = field['child']
      errors << "#{version}：#{key} 缺少 service 子字段" unless child.is_a?(Hash) && child['type'] == 'service' && child['envKey'].is_a?(String)
      field_keys << child['envKey'] if child.is_a?(Hash) && child['envKey'].is_a?(String)
    end
    if key.to_s.start_with?('PANEL_APP_PORT_') && (type != 'number' || field['rule'] != 'paramPort')
      warnings << "#{version}：#{key} 建议使用 number 与 paramPort"
    end
    # rule 必须是 1Panel 前端 form-rules.ts 中 CommonRule 已定义的键（v2.5.0），
    # 否则表单校验会把 undefined 当验证器调用并抛 TypeError。
    valid_rules = %w[
      paramCommon paramComplexity paramPort paramExtUrl
      paramSimple paramHttp phone vmName vmNetwork
      requiredInput requiredSelect requiredSelectBusiness
      noSpace simpleName simplePassword dbName composeName
      imageName volumeName name userName linuxName databaseName password
      databaseUsername email ip ipV6 ipv4 ipV4V6OrDomain
      host domain domainWithPort domainOrIP ipv4orV6 illegal
      appName containerName nginxDoc filePermission
    ]
    if field['rule'] && !valid_rules.include?(field['rule'])
      errors << "#{version}：#{key} 使用了不存在的 rule「#{field['rule']}」，1Panel 表单校验会抛 TypeError"
    end
    if type == 'password' && field['default'].to_s != ''
      warnings << "#{version}：#{key} 有非空默认密码，请确认它不是固定真实密钥"
    end
    if type == 'password' && field['random']
      # 官方模式：default 前缀 + '_' + 6 位随机串（params/index.vue）。random 依赖非空 default，
      # 且首字符必须是字母数字才能通过 paramComplexity 校验；空 default 会生成 '_xxxxxx' 导致表单报错。
      prefix = field['default'].to_s
      if prefix.empty? || !prefix.match?(/\A[a-zA-Z0-9]/)
        errors << "#{version}：#{key} 使用 random 时 default 必须是非空字母数字开头的前缀"
      else
        warnings << "#{version}：#{key} 的 random 只拼接 6 位随机串，非高强度密钥生成器"
      end
    end
  end

  services = compose['services']
  errors << "#{version}：Compose 缺少 services" unless services.is_a?(Hash) && !services.empty?
  if services.is_a?(Hash) && !services.values.any? { |service| service.is_a?(Hash) && service['container_name'] == '${CONTAINER_NAME}' }
    warnings << "#{version}：主服务建议使用 container_name: ${CONTAINER_NAME}"
  end
  external_network = compose.dig('networks', '1panel-network')
  warnings << "#{version}：建议声明外部网络 1panel-network" unless external_network.is_a?(Hash) && external_network['external'] == true
  # 所有服务容器都必须加入 1panel-network；1Panel 不会替应用包注入网络。
  # network_mode: host 的服务例外（1Panel 标记 HostMode）。
  if services.is_a?(Hash)
    services.each do |svc_name, svc|
      next unless svc.is_a?(Hash)
      next if svc['network_mode'] == 'host'
      svc_nets = svc['networks']
      joined = if svc_nets.is_a?(Array)
                 svc_nets.include?('1panel-network')
               elsif svc_nets.is_a?(Hash)
                 svc_nets.key?('1panel-network')
               end
      warnings << "#{version}：服务 #{svc_name} 未加入 1panel-network，跨应用容器名互访会失效" unless joined
    end
  end

  known = field_keys + %w[CONTAINER_NAME CPUS MEMORY_LIMIT HOST_IP PANEL_DB_PORT PANEL_DB_HOST_NAME DATABASE_NAME]
  # 生命周期脚本向 .env 写入的变量（如 ynight-hub 的 PANEL_ES_PASSWORD）视为已提供。
  # 匹配 shell 脚本中形如 VAR=... 的赋值输出行（awk print、echo、重定向写入）。
  %w[init.sh upgrade.sh uninstall.sh start.sh stop.sh restart.sh].each do |script_name|
    script_path = File.join(version_dir, 'scripts', script_name)
    next unless File.file?(script_path)
    File.read(script_path).scan(/\b([A-Z][A-Z0-9_]{2,})=/).each { |matched| known << matched }
  end
  known.uniq!
  variables = File.read(compose_path).scan(/\$\{([A-Za-z_][A-Za-z0-9_]*)[^}]*\}/).flatten.uniq
  (variables - known).each do |key|
    warnings << "#{version}：Compose 变量 #{key} 没有表单字段；请确认由 .env 或 init.sh 提供"
  end
end

warnings.each { |message| warn "提醒：#{message}" }
errors.each { |message| warn "错误：#{message}" }
if errors.empty?
  puts "静态检查通过：#{package_dir}（#{versions.length} 个版本，#{warnings.length} 条提醒）"
else
  exit 1
end
