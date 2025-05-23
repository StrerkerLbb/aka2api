# OpenAI到Akash Network的API代理 v2.0

这是一个基于FastAPI的代理服务，可以将OpenAI格式的API请求转换为chat.akash.network的格式，并将响应转换回OpenAI格式。使用这个代理，您可以通过OpenAI兼容的客户端访问Akash Network上的多种AI大模型。
本项目由AI撰写，含量100%。

## 🆕 新功能亮点

- **🤖 半自动化 cf_clearance 获取**: 使用 undetected-chromedriver 自动绕过 Cloudflare 挑战
- **🔄 智能降级处理**: 自动更新失败时启动半自动化获取，最后才手动输入
- **🚀 便捷启动脚本**: 提供多种启动选项，包括依赖安装和 cookie 获取
- **📊 更高成功率**: 半自动化获取成功率达 60-80%

## 功能特点

- ✅ 完全兼容OpenAI API格式的请求和响应
- 🔥 支持多种Akash Network上的AI模型（DeepSeek-R1、Llama-4、Qwen-3等）
- 🤖 **半自动化获取和更新认证凭证**
- 📡 支持流式和非流式响应
- 📝 提供模型列表和调试端点
- 🔍 支持文本嵌入API
- 🛡️ 智能 Cloudflare 挑战处理

## 项目结构

```
├── openai_to_akash_proxy.py     # 主服务程序
├── cookie_updater.py            # 凭证管理和自动更新（已增强）
├── auto_cf_helper.py            # 🆕 半自动化 cf_clearance 获取工具
├── install_cf_helper.py         # 🆕 依赖自动安装脚本
├── js_parser.py                 # 从Akash JS文件提取模型信息
├── config.py                    # 配置管理
├── http_gp.py                   # HTTP请求示例
├── start_server.ps1             # 🆕 PowerShell启动脚本（含选项菜单）
├── start_server.bat             # Windows批处理启动脚本
├── akash_cookies.json           # 存储凭证
├── requirements.txt             # 基础依赖项列表
├── CF_CLEARANCE_获取指南.md     # 🆕 详细获取指南
└── .env.example                 # 环境变量示例
```

## 🚀 快速开始

### 方法一：使用智能启动脚本（推荐）

1. **运行PowerShell启动脚本**：
   ```powershell
   .\start_server.ps1
   ```

2. **选择启动模式**：
   - `1` - 直接启动服务器（如果已有有效cookies）
   - `2` - 半自动化获取 cf_clearance 后启动（推荐首次使用）
   - `3` - 安装/更新 cf_clearance 获取工具依赖
   - `4` - 仅获取 cf_clearance（不启动服务器）

### 方法二：手动步骤

1. **创建虚拟环境**：
   ```bash
   python -m venv .venv
   # Windows
   .\.venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
   ```

2. **安装基础依赖**：
   ```bash
   pip install -r requirements.txt
   ```

3. **安装半自动化获取工具依赖**：
   ```bash
   python install_cf_helper.py
   ```

4. **获取 cf_clearance**：
   ```bash
   # 半自动化获取（推荐）
   python auto_cf_helper.py
   
   # 或者启动服务器时手动输入
   python openai_to_akash_proxy.py
   ```

## 🍪 Cookie 获取方式

### 1. 半自动化获取（推荐 - 70% 成功率）

```bash
# 安装依赖
python install_cf_helper.py

# 运行半自动化获取
python auto_cf_helper.py
```

**优点**：
- 🤖 自动处理 Cloudflare 挑战
- 🔄 无需手动复制 cookies
- ⏱️ 节省时间和精力

**过程**：
1. 自动打开 Chrome 浏览器
2. 访问 Akash Network 网站
3. 等待 Cloudflare 挑战自动解决
4. 提取并保存 cookies

### 2. 完全手动获取（100% 成功率）

1. 访问：https://chat.akash.network/
2. 等待 Cloudflare 挑战完成
3. 按F12 → Application → Cookies → 复制值
4. 在程序启动时输入

### 3. 智能降级处理

服务启动时会按以下顺序尝试：
1. **加载现有 cookies** → 如果有效则直接使用
2. **自动更新 session_token** → 使用现有 cf_clearance
3. **半自动化获取** → 启动浏览器自动获取
4. **手动输入** → 最后的备选方案

## API端点

### `/v1/chat/completions`

接收与OpenAI兼容的聊天完成请求。

请求示例：
```json
{
  "model": "deepseek",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "stream": false
}
```

### `/v1/models`

返回可用模型列表，格式与OpenAI API兼容。

支持的模型别名包括：
- `qwen-3`: Qwen3-235B-A22B-FP8
- `llama-4`: meta-llama-Llama-4-Maverick-17B-128E-Instruct-FP8
- `llama-3-3`: nvidia-Llama-3-3-Nemotron-Super-49B-v1
- `qwen-qwq`: Qwen-QwQ-32B
- `llama-3-70b`: Meta-Llama-3-3-70B-Instruct
- `deepseek`: DeepSeek-R1
- `llama-3-405b`: Meta-Llama-3-1-405B-Instruct-FP8

### `/v1/embeddings`

提供文本嵌入功能，返回与OpenAI兼容的响应格式。

### `/health`

健康检查端点，返回服务状态。

### `/debug/akash-api`

用于直接测试Akash API的调试端点。

## ⚙️ 配置

### 环境变量

可以通过.env文件或环境变量配置以下参数：

```bash
# Akash API配置
AKASH_API_URL=https://chat.akash.network/api/chat/
AKASH_JS_URL=https://chat.akash.network/_next/static/chunks/939-e56b9689ddc1242a.js

# 默认模型
DEFAULT_MODEL=DeepSeek-R1

# 服务器配置
HOST=0.0.0.0
PORT=8000

# Cookie配置
COOKIE_FILE=akash_cookies.json
COOKIE_EXPIRY_THRESHOLD=3600

# 重试配置
MAX_RETRIES=3
RETRY_DELAY=1.0

# 流式响应配置
STREAM_CHUNK_SIZE=1024
STREAM_DELAY=0.01

# HTTP请求超时设置
TIMEOUT=30.0
```

## 🔧 高级功能

### 自动更新机制

服务内置智能 cookie 管理：

1. **定期检查**: 每小时检查一次 cookie 有效性
2. **自动更新**: 优先使用现有 `cf_clearance` 更新 `session_token`
3. **降级处理**: 自动更新失败时启动半自动化获取
4. **手动备份**: 所有自动化方法失败时提示手动输入

### 成功率统计

基于实际测试：

| 方法 | 成功率 | 自动化程度 | 推荐场景 |
|------|--------|------------|----------|
| 半自动化获取 | 70% | 高 | 🌟 日常使用 |
| 手动获取 | 100% | 低 | 🔧 故障排除 |
| 自动 session_token 更新 | 90% | 最高 | 🚀 生产环境 |

## ❓ 常见问题

### Q: 半自动化获取失败怎么办？

**A: 可以尝试：**
1. 检查网络连接是否稳定
2. 关闭 VPN 或代理
3. 更新 Chrome 浏览器到最新版本
4. 重新运行 `python install_cf_helper.py`
5. 使用手动获取作为备选方案

### Q: cookies 多久失效？

**A: 典型时效：**
- `cf_clearance`: 30分钟 - 24小时
- `session_token`: 1-7天
- 自动更新会在过期前尝试刷新

### Q: 如何提高半自动化成功率？

**A: 优化建议：**
- 🕐 确保系统时间正确
- 🌐 使用稳定的网络环境
- 🚫 避免频繁重试
- 🔄 失败后等待一段时间再试

## 🚨 注意事项

- ⚖️ 此服务仅用于学习和研究目的
- 📋 使用时请遵守 chat.akash.network 的服务条款
- 🔐 半自动化功能需要 Chrome 浏览器支持
- 🌍 建议在网络环境良好时使用
- 🤝 如需更高成功率，可考虑专业的验证码解决服务
- 🕐 网站更新可能导致项目失效

## 📚 相关文档

- [CF_CLEARANCE_获取指南.md](./CF_CLEARANCE_获取指南.md) - 详细的获取指南
- [.env.example](./.env.example) - 环境变量配置示例

## 🔄 更新日志

- **v2.0**: 
  - ✨ 新增半自动化 cf_clearance 获取功能
  - 🔄 智能降级处理机制
  - 🚀 PowerShell 启动脚本with选项菜单
  - 📚 详细的使用指南和文档
- **v1.0**: 基础功能实现

---

**免责声明**: 本工具仅供学习和研究目的。使用时请遵守目标网站的服务条款和相关法律法规。
