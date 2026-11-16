#!/usr/bin/env node
// 1Panel 本地应用包静态检查器（Node.js 版，等价于 check_app.rb）。
// 用法：node .agents/skills/1panel-app/scripts/check_app.mjs apps/<应用标识>
// 依赖：yaml（npm 包）。若未安装，先在任意目录执行 npm install yaml 并设置 NODE_PATH。

import { readFileSync, existsSync, statSync, readdirSync } from 'node:fs';
import { join, resolve, basename } from 'node:path';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
let YAML;
try {
  YAML = require('yaml');
} catch {
  console.error('错误：缺少 yaml 模块。请运行 npm install yaml 后重试。');
  process.exit(2);
}

const packageDir = process.argv[2];
if (!packageDir) {
  console.error('用法：node check_app.mjs apps/<应用标识>');
  process.exit(2);
}
const rootDir = resolve(packageDir);
if (!existsSync(rootDir) || !statSync(rootDir).isDirectory()) {
  console.error(`错误：应用目录不存在：${rootDir}`);
  process.exit(2);
}

const errors = [];
const warnings = [];

function readYaml(path) {
  try {
    return YAML.parse(readFileSync(path, 'utf8'));
  } catch (error) {
    errors.push(`无法读取 ${path}：${error.message}`);
    return null;
  }
}

// ---- 根 data.yml ----
const rootData = readYaml(join(rootDir, 'data.yml'));
const logoPath = join(rootDir, 'logo.png');
let logoOk = false;
if (existsSync(logoPath)) {
  const head = readFileSync(logoPath).subarray(0, 8);
  logoOk = head.equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]));
}
if (!logoOk) errors.push('缺少有效的 logo.png');
if (!existsSync(join(rootDir, 'README.md'))) warnings.push('缺少 README.md');

if (rootData && typeof rootData === 'object') {
  const props = rootData.additionalProperties || {};
  if (props.key !== basename(rootDir)) errors.push('根 data.yml 的 key 与目录名不一致');
  if (!props.name || String(props.name).trim() === '') errors.push('根 data.yml 缺少 name');
  if (!Array.isArray(props.tags) || props.tags.length === 0) errors.push('根 data.yml 缺少 tags');
}

// ---- 版本目录 ----
const versions = readdirSync(rootDir)
  .filter((name) => statSync(join(rootDir, name)).isDirectory())
  .sort();
if (versions.length === 0) errors.push('至少需要一个版本目录');

const KNOWN_VARS = new Set([
  'CONTAINER_NAME', 'CPUS', 'MEMORY_LIMIT', 'HOST_IP',
  'PANEL_DB_PORT', 'PANEL_DB_HOST_NAME', 'DATABASE_NAME',
]);

// 1Panel 前端 form-rules.ts 中 CommonRule 的有效 rule 键（v2.5.0 / dev-v2 @ 0b0c8cb）。
const VALID_RULES = new Set([
  'paramCommon', 'paramComplexity', 'paramPort', 'paramExtUrl',
  'paramSimple', 'paramHttp', 'phone', 'vmName', 'vmNetwork',
  'requiredInput', 'requiredSelect', 'requiredSelectBusiness',
  'noSpace', 'simpleName', 'simplePassword', 'dbName', 'composeName',
  'imageName', 'volumeName', 'name', 'userName', 'linuxName', 'databaseName', 'password',
  'databaseUsername', 'email', 'ip', 'ipV6', 'ipv4', 'ipV4V6OrDomain',
  'host', 'domain', 'domainWithPort', 'domainOrIP', 'ipv4orV6', 'illegal',
  'appName', 'containerName', 'nginxDoc', 'filePermission',
  'integerNumber', 'integerNumberWith0', 'floatNumber', 'number',
]);

for (const version of versions) {
  const versionDir = join(rootDir, version);
  const data = readYaml(join(versionDir, 'data.yml'));
  const composePath = join(versionDir, 'docker-compose.yml');
  const compose = readYaml(composePath);
  if (!data || !compose) continue;

  const fields = data?.additionalProperties?.formFields;
  if (!Array.isArray(fields)) {
    errors.push(`${version}：formFields 必须是数组`);
    continue;
  }

  const fieldKeys = [];
  for (const field of fields) {
    if (!field || typeof field !== 'object') {
      errors.push(`${version}：表单字段必须是映射`);
      continue;
    }
    const key = field.envKey;
    if (!(typeof key === 'string' && /^[A-Za-z_][A-Za-z0-9_]*$/.test(key))) {
      errors.push(`${version}：envKey 无效：${JSON.stringify(key)}`);
    }
    if (Object.values(field).some((v) => v === null)) errors.push(`${version}：字段含空值：${key}`);
    if (fieldKeys.includes(key)) errors.push(`${version}：重复的 envKey：${key}`);
    fieldKeys.push(key);

    const type = field.type;
    if (!['text', 'number', 'password', 'select', 'service', 'apps'].includes(type)) {
      errors.push(`${version}：不支持的字段类型 ${JSON.stringify(type)}：${key}`);
    }
    if ((type === 'select' || type === 'apps') && !(Array.isArray(field.values) && field.values.length > 0)) {
      errors.push(`${version}：${key} 缺少 values`);
    }
    if (type === 'service' && String(field.key ?? '') === '') {
      errors.push(`${version}：${key} 缺少服务 key`);
    }
    if (type === 'apps') {
      const child = field.child;
      if (!(child && typeof child === 'object' && child.type === 'service' && typeof child.envKey === 'string')) {
        errors.push(`${version}：${key} 缺少 service 子字段`);
      }
      if (child && typeof child.envKey === 'string') fieldKeys.push(child.envKey);
    }
    if (String(key).startsWith('PANEL_APP_PORT_') && (type !== 'number' || field.rule !== 'paramPort')) {
      warnings.push(`${version}：${key} 建议使用 number 与 paramPort`);
    }
    // rule 必须是 1Panel 前端 Rules 中已定义的键，否则会被 push 成 undefined 并让表单校验抛异常。
    // 依据 frontend/src/global/form-rules.ts 的 CommonRule 接口。
    if (field.rule && !VALID_RULES.has(field.rule)) {
      errors.push(`${version}：${key} 使用了不存在的 rule「${field.rule}」，1Panel 表单校验会抛 TypeError`);
    }
    if (type === 'password' && String(field.default ?? '') !== '') {
      warnings.push(`${version}：${key} 有非空默认密码，请确认它不是固定真实密钥`);
    }
    if (type === 'password' && field.random) {
      // 官方模式：default 前缀 + '_' + 6 位随机串（params/index.vue）。random 依赖非空 default，
      // 且首字符必须是字母数字才能通过 paramComplexity 校验；空 default 会生成 '_xxxxxx' 导致表单报错。
      const prefix = String(field.default ?? '');
      if (prefix === '' || !/^[a-zA-Z0-9]/.test(prefix)) {
        errors.push(`${version}：${key} 使用 random 时 default 必须是非空字母数字开头的前缀`);
      } else {
        warnings.push(`${version}：${key} 的 random 只拼接 6 位随机串，非高强度密钥生成器`);
      }
    }
  }

  const services = compose.services;
  if (!(services && typeof services === 'object' && Object.keys(services).length > 0)) {
    errors.push(`${version}：Compose 缺少 services`);
  } else if (!Object.values(services).some((s) => s && s.container_name === '${CONTAINER_NAME}')) {
    warnings.push(`${version}：主服务建议使用 container_name: \${CONTAINER_NAME}`);
  }

  const net = compose?.networks?.['1panel-network'];
  if (!(net && net.external === true)) {
    warnings.push(`${version}：建议声明外部网络 1panel-network`);
  }
  // 所有服务容器都必须加入 1panel-network；1Panel 不会替应用包注入网络。
  // network_mode: host 的服务例外（1Panel 标记 HostMode）。
  if (services && typeof services === 'object') {
    for (const [svcName, svc] of Object.entries(services)) {
      if (!svc || typeof svc !== 'object') continue;
      if (svc.network_mode === 'host') continue;
      const svcNets = svc.networks;
      const joined = Array.isArray(svcNets)
        ? svcNets.includes('1panel-network')
        : svcNets && typeof svcNets === 'object' && '1panel-network' in svcNets;
      if (!joined) {
        warnings.push(`${version}：服务 ${svcName} 未加入 1panel-network，跨应用容器名互访会失效`);
      }
    }
  }

  const known = new Set([...fieldKeys, ...KNOWN_VARS]);
  // 生命周期脚本向 .env 写入的变量（如 ynight-hub 的 PANEL_ES_PASSWORD）视为已提供。
  // 匹配 shell 脚本中形如 VAR=... 的赋值输出行（awk print、echo、重定向写入）。
  for (const scriptName of ['init.sh', 'upgrade.sh', 'uninstall.sh', 'start.sh', 'stop.sh', 'restart.sh']) {
    const scriptPath = join(versionDir, 'scripts', scriptName);
    if (!existsSync(scriptPath)) continue;
    const scriptText = readFileSync(scriptPath, 'utf8');
    for (const match of scriptText.matchAll(/\b([A-Z][A-Z0-9_]{2,})=/g)) {
      known.add(match[1]);
    }
  }
  const text = readFileSync(composePath, 'utf8');
  const variables = new Set(
    [...text.matchAll(/\$\{([A-Za-z_][A-Za-z0-9_]*)[^}]*\}/g)].map((m) => m[1])
  );
  for (const variable of variables) {
    if (!known.has(variable)) {
      warnings.push(`${version}：Compose 变量 ${variable} 没有表单字段；请确认由 .env 或 init.sh 提供`);
    }
  }
}

for (const message of warnings) console.error(`提醒：${message}`);
for (const message of errors) console.error(`错误：${message}`);

if (errors.length === 0) {
  console.log(`静态检查通过：${rootDir}（${versions.length} 个版本，${warnings.length} 条提醒）`);
} else {
  process.exit(1);
}
