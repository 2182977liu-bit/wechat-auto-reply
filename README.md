# 微信自动回复 AI 机器人

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![WeChat](https://img.shields.io/badge/WeChat-4.2.0.53-07C160?style=for-the-badge&logo=wechat&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**基于开源逆向后端 wechatauto-replica 的智能微信自动回复机器人，支持联系人独立记忆 + 本地知识库 RAG**

</div>

---

## 功能特性

- **智能自动回复** - 增量监听微信新消息，自动调用 AI 生成回复
- **独立记忆系统** - 每个联系人独立对话历史，SQLite 持久化（`data/memory.db`）
- **本地知识库 RAG** - `knowledge/` 目录文档切块 + BM25 检索，回复前注入相关片段，离线可用
- **多 AI 模型** - DeepSeek / 通义千问 / 小米等 OpenAI 兼容接口
- **Web 控制台** - 启动/停止、联系人、AI 配置、记忆、日志、知识库管理

## 控制层后端（不再使用 wxauto / wxautox）

采用 GitHub 开源逆向项目 **[wechatauto-replica](https://github.com/fanyuantaier/wechatauto-replica)**（Apache-2.0，免费）：

- **读消息**：本地 SQLCipher4 数据库解密（`xwechat_files/<wxid>/db_storage/`），增量水位去重，不依赖 UI 控件树
- **发消息**：UIA 热激活 + 坐标/OCR 回退（`wechatauto.guia.quick_send`），发送后回读数据库校验
- **兼容**：微信 4.1.12+，已在 **4.2.0.53** 真机验证
- **要求**：微信**已登录**；本程序以**管理员权限**运行（读取进程内存提取密钥）；发送时微信窗口需在桌面可见

> 微信 4.x 主界面为自绘渲染，UI Automation 读不到消息，故旧版 wxauto 免费/Plus 均不适用；本后端用数据库解密绕开该限制。

---

## 快速开始

### 环境要求

```
✅ Windows 10/11
✅ Python 3.9+（本项目 venv 为 3.13）
✅ 微信 4.1.12+（已验证 4.2.0.53），并已登录
✅ 管理员权限运行本程序
✅ 网络（调用 AI API）
```

### 安装与运行

```bash
# 1. 安装依赖（含开源后端）
pip install -r requirements.txt

# 2. 以管理员身份打开终端，运行
python main.py          # 命令行模式
python main.py --web    # 带 Web 界面（推荐），访问 http://localhost:5000
```

首次运行自动生成 `config.json`。在 Web「AI 配置」填 API Key，「联系人」添加监控对象，回主页「启动」。

### 知识库

把资料（`.md` / `.txt`）放入 `knowledge/`，重启或 `POST /api/knowledge/reload` 生效。
配置在 `config.json → knowledge`：`enabled / dir / top_k / chunk_size`。
检索接口：`GET /api/knowledge/search?q=关键词`。

---

## 配置说明（节选）

```json
{
  "wechat": {
    "backend": "wechatauto-replica",
    "scan_interval": 5,
    "contacts": ["联系人1"],
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
  "knowledge": { "enabled": true, "dir": "knowledge", "top_k": 3, "chunk_size": 400 },
  "server": { "host": "0.0.0.0", "port": 5000 }
}
```

---

## 工作原理

```
微信新消息写入本地加密 DB
    ↓
后端解密读取 + 增量水位去重（跳过自己发的/非文本）
    ↓
知识库 BM25 检索相关片段 + 加载联系人记忆(最近20条)
    ↓
构建提示词 → 调用 AI API 生成回复
    ↓
quick_send 发送（UIA/OCR）+ 回读校验
    ↓
保存对话到记忆库
```

---

## 常见问题

- **找不到微信窗口 / 未找到数据库目录**：确认微信已登录、本程序以管理员运行。
- **权限不足**：读取微信进程内存需管理员权限，右键「以管理员身份运行」。
- **不回复**：检查联系人是否在监控列表、AI API Key 是否正确、网络是否通。
- **发送失败**：发送是 GUI 操作，需微信窗口在桌面可见、未锁屏；锁屏/最小化到托盘会失败。
- **知识库不生效**：确认 `knowledge.enabled=true`、目录有 `.md/.txt`、修改后重载。
- **备份记忆**：复制 `data/memory.db`。

---

## 项目结构

```
├── app.py            # Flask Web 应用
├── config.py         # 配置管理
├── detector.py       # 控制层（wechatauto-replica 后端）
├── knowledge.py      # 本地知识库 BM25 检索
├── main.py           # 主程序入口
├── memory.py         # SQLite 联系人记忆
├── replier.py        # AI 回复生成（记忆+知识库注入）
├── requirements.txt
├── knowledge/        # 知识库文档（.md/.txt）
├── templates/        # Web 模板
├── data/memory.db    # 记忆库（自动创建）
└── logs/wechat.log   # 日志（自动创建）
```

## 技术栈

Python 3.9+ · wechatauto-replica（开源逆向）· Flask · SQLite · OpenAI SDK · 本地 BM25 RAG

## 更新日志

### v2.0.0
- 🔁 控制层弃用 wxauto/wxautox，改用开源 wechatauto-replica（支持微信 4.2.0.53）
- ✨ 新增本地知识库 RAG（knowledge/ + BM25）并接入回复
- 🐛 修复 main.py 日志路径未导入导致的启动报错
- 🧹 清理 wxauto 残留与过时 UIA 调试脚本

### v1.0.0
- 基础自动回复、联系人记忆、Web 界面、多模型

## 许可证

MIT（本项目）；控制层后端 wechatauto-replica 为 Apache-2.0。
