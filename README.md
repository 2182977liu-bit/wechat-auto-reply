<div align="center">

# 🤖 微信自动回复 AI 机器人

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/wechat-4.x-brightgreen.svg" alt="WeChat">
</p>

基于 wxauto4 的微信自动回复机器人，支持联系人独立记忆、Flask Web 管理界面。

</div>

## ✨ 功能特性

- 🎯 **自动回复** - 监听联系人消息并自动回复
- 🧠 **独立记忆** - 每个联系人有独立的对话历史，持久化存储
- 💻 **Web 管理** - 简洁美观的 Flask 网页管理界面
- 🔒 **双重过滤** - 消息基线计数 + 内容追踪机制
- 📊 **记忆管理** - 查看、清除、管理各联系人记忆
- 📝 **实时日志** - 查看运行日志

## 🚀 快速开始

### 前置要求

- Python 3.8+
- 微信 4.x 版本
- Windows 10 或更高

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/2182977liu-bit/wechat-auto-reply.git
cd wechat-auto-reply
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置文件**

复制 `config.example.json` 为 `config.json`（首次运行会自动生成），填写：
```json
{
  "wechat": {
    "auto_connect": true,
    "target_contacts": ["联系人1", "联系人2"]
  },
  "ai": {
    "api_key": "你的 API Key",
    "base_url": "https://api.example.com/v1",
    "model": "模型名称",
    "system_prompt": "你是一个微信助手..."
  },
  "flask": {
    "host": "0.0.0.0",
    "port": 5000
  }
}
```

4. **运行**
```bash
# 仅运行机器人
python main.py

# 运行机器人 + Web 管理界面
python main.py --web
```

5. **访问 Web 界面**

打开浏览器访问：http://localhost:5000

## 📁 项目结构

```
wechat-auto-reply/
├── app.py              # Flask Web 应用
├── config.py           # 配置管理
├── detector.py         # 微信消息检测
├── main.py             # 主程序入口
├── memory.py           # SQLite 记忆管理
├── replier.py          # AI 回复生成
├── requirements.txt    # 依赖列表
├── templates/          # HTML 模板
│   ├── base.html
│   ├── index.html
│   ├── contacts.html
│   ├── ai_config.html
│   ├── logs.html
│   └── memory.html
├── data/               # 数据库存储（自动创建）
│   └── memory.db
└── logs/               # 日志文件（自动创建）
```

## 📖 使用说明

### Web 管理界面

1. **主页** - 启动/停止机器人
2. **联系人** - 管理需要监听的联系人
3. **AI 配置** - 配置 API Key 和提示词
4. **日志** - 查看运行日志
5. **记忆** - 查看和管理各联系人记忆

### 消息过滤机制

- **基线计数** - 跟踪每个联系人的消息数量变化
- **内容追踪** - 记录自己发送的消息，避免重复回复
- **双重保护** - 防止无限循环回复

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE)

---

<div align="center">
Made with ❤️ by 2182977liu-bit
</div>
