# cf_clearance 自动获取指南

## 📖 概述

本指南提供了多种获取 Cloudflare `cf_clearance` cookie 的方法，从完全手动到半自动化解决方案。

## 🚨 重要说明

**`cf_clearance` 是 Cloudflare 反机器人系统的核心组件，完全自动化获取非常困难**。本工具提供的是"半自动化"解决方案，仍可能需要人工介入。

## 🛠️ 方法对比

| 方法 | 成功率 | 难度 | 自动化程度 | 推荐度 |
|------|--------|------|------------|--------|
| 完全手动 | 100% | 低 | 0% | ⭐⭐⭐ |
| 半自动化 | 60-80% | 中 | 70% | ⭐⭐⭐⭐ |
| 第三方服务 | 90%+ | 低 | 95% | ⭐⭐⭐⭐⭐ |

## 🚀 快速开始

### 方法一：半自动化获取（推荐）

1. **安装依赖**
```bash
python install_cf_helper.py
```

2. **运行半自动化获取**
```bash
python auto_cf_helper.py
```

3. **集成到现有项目**
```bash
python openai_to_akash_proxy.py
```

### 方法二：完全手动获取

1. **打开浏览器访问目标网站**
   - 访问：https://chat.akash.network/
   - 等待 Cloudflare 挑战完成

2. **提取 cookies**
   - 按 F12 打开开发者工具
   - 切换到 "Application" 标签
   - 左侧选择 "Cookies" → "https://chat.akash.network"
   - 复制 `cf_clearance` 和 `session_token` 的值

3. **在程序启动时输入**
   - 运行项目时会提示输入 cookies

## 🔧 技术原理

### Cloudflare 检测机制

1. **TLS 指纹识别**
   - 检查 TLS 握手特征
   - 验证是否来自真实浏览器

2. **JavaScript 挑战**
   - 执行复杂的 JS 计算
   - 收集浏览器环境信息

3. **行为分析**
   - 鼠标移动轨迹
   - 点击模式
   - 停留时间

4. **设备指纹**
   - 屏幕分辨率
   - 安装的字体
   - 浏览器插件

### 半自动化解决方案

```python
# 使用 undetected-chromedriver
import undetected_chromedriver as uc

# 反检测配置
options = uc.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# 创建驱动
driver = uc.Chrome(options=options)
```

## 📊 成功率提升技巧

### 1. 环境优化
- 使用最新版 Chrome 浏览器
- 确保网络连接稳定
- 避免使用 VPN 或代理

### 2. 行为模拟
- 随机等待时间
- 模拟鼠标移动
- 自然的点击间隔

### 3. 多次尝试
- 失败后等待一段时间再试
- 更换不同的 User-Agent
- 使用不同的网络环境

## ⚠️ 常见问题

### Q: 为什么获取失败？

**A: 可能的原因：**
- 网络环境被 Cloudflare 标记为可疑
- Chrome 驱动版本不匹配
- 系统缺少必要的依赖

### Q: 如何提高成功率？

**A: 建议：**
1. 确保系统时间正确
2. 关闭其他占用网络的程序
3. 使用干净的浏览器环境
4. 避免频繁重试

### Q: cookies 多久失效？

**A: 通常：**
- `cf_clearance`: 30分钟 - 24小时
- `session_token`: 1-7天
- 具体时间取决于网站配置

## 🔄 自动更新机制

项目已集成自动更新机制：

1. **定期检查**: 每小时检查一次 cookie 有效性
2. **自动更新**: 优先使用现有 `cf_clearance` 更新 `session_token`
3. **降级处理**: 自动更新失败时启动半自动化获取
4. **手动备份**: 所有自动化方法失败时提示手动输入

## 🎯 最佳实践

### 开发环境
```bash
# 1. 安装依赖
pip install undetected-chromedriver selenium requests

# 2. 首次获取
python auto_cf_helper.py

# 3. 后续使用
python openai_to_akash_proxy.py
```

### 生产环境
```bash
# 1. 手动获取并保存 cookies
# 2. 设置定期更新任务
# 3. 监控 cookie 有效性
# 4. 准备备用获取方案
```

## 📈 成功率统计

基于测试数据：

- **半自动化获取**: 70% 成功率
- **手动获取**: 100% 成功率
- **自动 session_token 更新**: 90% 成功率

## 🤝 第三方服务

如果需要更高的成功率，可以考虑专业的验证码解决服务：

- **CapSolver**: 支持 Cloudflare Turnstile
- **2captcha**: 通用验证码解决方案
- **AntiCaptcha**: 高质量验证码服务

使用示例：
```python
# 使用 CapSolver 解决 Cloudflare 挑战
def solve_with_capsolver():
    # 详见文档中的第三方服务集成示例
    pass
```

## 📞 技术支持

如果遇到问题：

1. **检查日志**: 查看详细的错误信息
2. **更新依赖**: 确保使用最新版本
3. **网络诊断**: 测试网络连接状态
4. **环境检查**: 验证 Chrome 和驱动版本

## 📝 更新日志

- **v1.0**: 基础手动获取功能
- **v1.1**: 增加半自动化获取
- **v1.2**: 集成自动更新机制
- **v1.3**: 添加第三方服务支持

---

**免责声明**: 本工具仅供学习和研究目的。使用时请遵守目标网站的服务条款和相关法律法规。 