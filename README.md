# 微信自动回复 AI 机器人

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![WeChat](https://img.shields.io/badge/WeChat-4.x-07C160?style=for-the-badge&logo=wechat&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
![Stars](https://img.shields.io/github/stars/2182977liu-bit/wechat-auto-reply?style=for-the-badge)

**基于 wxauto4 的智能微信自动回复机器人，支持联系人独立记忆**

[功能特性](#功能特性) • [快速开始](#快速开始) • [详细安装](#详细安装) • [使用说明](#使用说明) • [配置说明](#配置说明) • [常见问题](#常见问题)

</div>

---

## 功能特性

### 🎯 核心功能

- **智能自动回复** - 实时监听微信消息，自动调用 AI 生成回复
- **独立记忆系统** - 每个联系人拥有独立的对话历史，SQLite 持久化存储
- **双重过滤机制** - 基线计数 + 内容追踪，防止重复回复和无限循环
- **多 AI 模型支持** - 支持 DeepSeek、阿里通义、 Xiaomi 等多种 AI 模型

### 💻 管理界面

- **Web 控制台** - 简洁美观的 Flask 网页管理界面
- **实时监控** - 一键启动/停止机器人，查看运行状态
- **联系人管理** - 添加/删除需要监控的联系人
- **记忆管理** - 查看、编辑、清除各联系人的对话记忆
- **日志查看** - 实时查看运行日志，方便调试

### 🛡️ 安全特性

- **消息过滤** - 不会对自己发送的消息进行回复
- **冷却机制** - 发送消息后有短暂冷却期，避免频繁回复
- **错误处理** - 完善的异常捕获和日志记录
- **本地存储** - 所有数据本地存储，保护隐私

---

## 快速开始

### 环境要求

```
✅ Python 3.8 或更高版本
✅ Windows 10 或更高版本
✅ 微信 4.x 版本（支持 Windows 客户端）
✅ 稳定的网络连接（用于调用 AI API）
```

### 安装步骤

#### 1. 克隆项目

打开命令行（CMD 或 PowerShell），执行：

```bash
git clone https://github.com/2182977liu-bit/wechat-auto-reply.git
cd wechat-auto-reply
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

#### 3. 首次运行

```bash
# 运行机器人（仅命令行模式）
python main.py

# 或运行机器人 + Web 管理界面（推荐）
python main.py --web
```

首次运行会自动生成 `config.json` 配置文件。

#### 4. 访问 Web 界面

打开浏览器，访问：**http://localhost:5000**

---

## 详细安装

### 方式一：命令行模式

仅运行自动回复功能，适合服务器或无界面环境：

```bash
python main.py
```

### 方式二：Web 管理模式（推荐）

同时运行自动回复和 Web 管理界面：

```bash
python main.py --web
```

启动后访问 http://localhost:5000

### 方式三：后台运行

使用 Python 的 `pyw` 模块实现后台运行：

```bash
pythonw main.py --web
```

### 方式四：Windows 服务

使用 NSSM 将程序注册为 Windows 服务：

```bash
# 1. 下载 NSSM
# 2. 执行以下命令注册服务
nssm install WeChatBot "pythonw.exe" "main.py --web"
nssm start WeChatBot
```

---

## 使用说明

### 首次配置

#### 1. 配置 AI API

首次运行后，打开 Web 界面（http://localhost:5000），在左侧菜单点击 **"AI 配置"**：

填写以下信息：
- **API Key** - 从你的 AI 服务提供商获取
- **Base URL** - API 端点地址
- **模型名称** - 如 `deepseek-chat`、`qwen-turbo` 等
- **系统提示词** - 设置 AI 的角色和行为（可选）

#### 2. 添加联系人

在左侧菜单点击 **"联系人"**，输入要监控的联系人微信昵称，点击添加。

> 💡 **提示**：联系人昵称必须与微信中显示的完全一致

#### 3. 启动机器人

返回 **"主页"**，点击 **"启动机器人"** 按钮。

### Web 界面功能

#### 📊 主页面

- 查看机器人运行状态（已连接/未连接）
- 启动/停止机器人
- 查看统计信息（已处理消息数、联系人数量等）

#### 👥 联系人管理

- 查看当前监控的所有联系人
- 添加新联系人
- 删除联系人
- 查看联系人的消息统计

#### 🤖 AI 配置

- 配置 AI 模型参数
- 测试 API 连接
- 自定义系统提示词
- 查看 API 使用情况

#### 📝 日志查看

- 实时查看运行日志
- 按级别筛选（INFO、WARNING、ERROR）
- 搜索日志内容
- 导出日志文件

#### 🧠 记忆管理

- 查看所有联系人的记忆统计
- 查看特定联系人的对话历史
- 清除单个联系人的记忆
- 导出对话记录

---

## 配置说明

### 配置文件结构

运行后会自动生成 `config.json`，内容如下：

```json
{
  "wechat": {
    "window_title": "微信",
    "scan_interval": 5,
    "contacts": ["联系人1", "联系人2"],
    "reply_all": false
  },
  "ai": {
    "default_model": "deepseek",
    "models": {
      "deepseek": {
        "api_key": "",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat"
      }
    }
  },
  "server": {
    "host": "0.0.0.0",
    "port": 5000
  }
}
```

### 配置项说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `window_title` | 微信窗口标题 | "微信" |
| `scan_interval` | 消息扫描间隔（秒） | 5 |
| `contacts` | 要监控的联系人列表 | [] |
| `reply_all` | 是否回复所有消息 | false |

### AI 模型配置

#### DeepSeek

```json
"deepseek": {
  "api_key": "你的 DeepSeek API Key",
  "base_url": "https://api.deepseek.com",
  "model": "deepseek-chat"
}
```

#### 阿里通义千问

```json
"qianwen": {
  "api_key": "你的阿里云 API Key",
  "base_url": "https://dashscope.aliyuncs.com",
  "model": "qwen-turbo"
}
```

#### Xiaomi MiMo

```json
"xiaomi": {
  "api_key": "你的 Xiaomi API Key",
  "base_url": "https://api.xiaomi.com",
  "model": "MiLM"
}
```

---

## 工作原理

### 消息检测机制

1. **窗口激活** - 使用 Windows UI Automation 激活微信窗口
2. **消息读取** - 调用 wxauto4 的 `GetAllMessage()` 获取聊天记录
3. **基线计数** - 记录每个联系人的消息数量基线
4. **变化检测** - 通过消息数量变化判断是否有新消息
5. **内容过滤** - 排除自己发送的消息

### AI 回复流程

```
用户发送消息
    ↓
检测到新消息
    ↓
加载联系人记忆（最近20条对话）
    ↓
构建 AI 提示词
    ↓
调用 AI API 生成回复
    ↓
发送回复到微信
    ↓
保存对话到记忆库
    ↓
更新消息基线
```

### 双重过滤机制

- **基线过滤** - 跳过已处理的历史消息
- **内容过滤** - 跳过自己发送的消息内容
- **双重保障** - 确保每条消息只回复一次

---

## 常见问题

### Q1: 启动时报错 "找不到微信窗口"

**原因**：微信窗口未打开或窗口标题不匹配

**解决方法**：
1. 确保微信已登录并打开
2. 检查 `config.json` 中的 `window_title` 是否与微信窗口标题一致
3. 默认窗口标题是 "微信"

### Q2: 机器人不回复消息

**可能原因**：
1. 联系人未添加到监控列表
2. AI API 未配置或配置错误
3. 网络连接问题

**解决方法**：
1. 在 Web 界面添加联系人
2. 检查 AI 配置，确保 API Key 正确
3. 检查网络连接

### Q3: 无限回复循环

**原因**：消息过滤机制失效

**解决方法**：
1. 重启机器人程序
2. 检查日志，查看是否有异常
3. 清除该联系人的记忆后重试

### Q4: API 调用失败

**可能原因**：
1. API Key 错误或过期
2. API 配额用尽
3. 网络问题

**解决方法**：
1. 检查 API Key 是否正确
2. 登录 AI 服务平台检查配额
3. 等待网络恢复或切换网络

### Q5: 如何停止机器人？

**方法一**：Web 界面停止
- 访问 http://localhost:5000
- 点击 "停止机器人" 按钮

**方法二**：命令行停止
- 按 `Ctrl + C`

**方法三**：强制终止
- 打开任务管理器
- 结束 `python.exe` 进程

### Q6: 如何查看日志？

1. Web 界面 - 点击左侧 "日志" 菜单
2. 日志文件 - 查看 `logs/wechat.log`
3. 控制台输出 - 如果在命令行运行，日志会直接输出到终端

### Q7: 如何备份记忆数据？

记忆数据存储在 `data/memory.db`，直接复制该文件即可备份。

---

## 项目结构

```
wechat-auto-reply/
├── app.py              # Flask Web 应用
├── config.py           # 配置管理模块
├── detector.py         # 微信消息检测核心
├── main.py             # 主程序入口
├── memory.py           # SQLite 记忆管理
├── replier.py          # AI 回复生成
├── requirements.txt    # Python 依赖列表
├── README.md           # 项目说明文档
├── .gitignore          # Git 忽略配置
├── templates/          # HTML 模板目录
│   ├── base.html       # 基础模板
│   ├── index.html      # 主页
│   ├── contacts.html   # 联系人管理
│   ├── ai_config.html  # AI 配置页面
│   ├── logs.html       # 日志页面
│   └── memory.html     # 记忆管理页面
├── data/               # 数据存储目录（自动创建）
│   └── memory.db       # SQLite 数据库
└── logs/               # 日志目录（自动创建）
    └── wechat.log      # 运行日志
```

---

## 技术栈

- **Python 3.8+** - 编程语言
- **wxauto4** - 微信 Windows 客户端自动化
- **Flask** - Web 框架
- **SQLite** - 持久化存储
- **OpenAI SDK** - AI API 调用
- **Windows UI Automation** - 窗口控制

---

## 更新日志

### v1.0.0 (2024-05-29)
- ✨ 实现基础的自动回复功能
- ✨ 添加联系人独立记忆系统
- ✨ 开发 Web 管理界面
- ✨ 实现双重消息过滤机制
- ✨ 支持多种 AI 模型

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE)

---

## 联系方式

- **GitHub Issues**: https://github.com/2182977liu-bit/wechat-auto-reply/issues
- **作者**: 2182977liu-bit

---

<div align="center">

**如果这个项目对你有帮助，请给它一个 ⭐**

</div>
