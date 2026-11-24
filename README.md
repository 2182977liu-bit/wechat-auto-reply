# 微信自动回复 AI 机器人

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![WeChat](https://img.shields.io/badge/WeChat-4.2.0.53-07C160?style=for-the-badge&logo=wechat&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**纯 UI 自动化的智能微信自动回复机器人：不读进程内存、不解密数据库，支持联系人独立记忆 + 本地知识库 RAG**

</div>

---

## 功能特性

- **智能自动回复** - 增量监听微信新消息，自动调用 AI 生成回复
- **独立记忆系统** - 每个联系人独立对话历史，SQLite 持久化（`data/memory.db`）
- **本地知识库 RAG** - `knowledge/` 目录文档切块 + BM25 检索，回复前注入相关片段，离线可用
- **多 AI 模型** - DeepSeek / 通义千问 / 小米等 OpenAI 兼容接口
- **Web 控制台** - 启动/停止、联系人、AI 配置、记忆、日志、知识库管理

## 控制层后端（纯 UI 自动化，不再使用 wxauto / wxautox）

复用开源项目 **[wechatauto-replica](https://github.com/fanyuantaier/wechatauto-replica)**（Apache-2.0）的**纯 UIA 子模块**：

- **读消息**：`ui.main.WeChatMainWnd` + `ChatBox.get_msgs()` 读取 UIA 控件树，快照差分去重（跳过自己发的/非文本）
- **发消息**：模拟键鼠逐字输入 + UIA 热激活；发送后 **UIA 回读**最后一条自己消息确认落地
- **安全红线**：**不读取微信进程内存、不解密本地数据库**（`WeChatDB` 一律不实例化，`quick_send` 强制 `verify=False`）
- **要求**：微信**已登录**、主窗口存在；**无需管理员权限**；运行期间微信窗口会被置前/切换会话，请勿同时手动操作微信

> ⚠️ 背景：早期版本用"读进程内存 + 解密 SQLCipher 数据库"收消息，实测触发风控导致账号被强制下线。现已整体改为纯 UI 自动化路线，与真人操作官方客户端的路径一致。**该路线的消息读取能力仍需在目标微信版本上真机确认**（部分 4.x 版本主界面自绘渲染，UIA 可能读不到消息控件）。

---

## 快速开始

### 环境要求

```
✅ Windows 10/11
✅ Python 3.9+（本项目 venv 为 3.13）
✅ 微信 4.x 并已登录（主窗口存在）
✅ 无需管理员权限（纯 UI 自动化，不读进程内存）
✅ 网络（调用 AI API）
```

### 安装与运行

```bash
# 1. 安装依赖（含开源后端）
pip install -r requirements.txt

# 2. 运行（无需管理员）
python main.py          # 命令行模式
python main.py --web    # 带 Web 界面（推荐），访问 http://localhost:5000
```

Windows 可直接双击 **`启动.bat`**（自动使用项目内 `.venv`）。

首次运行自动生成 `config.json`，并**自动生成 Web 访问密码**（打印在运行日志，存于 `config.json → server.password`）。打开控制台需先登录。在「AI 配置」填 API Key，「联系人」添加监控对象，回主页「启动」。

> 安全提示：控制台默认绑定 `0.0.0.0`，局域网可访问，**务必保管好访问密码**；API Key 不会回显到页面，留空保存即保留原密钥。

### 知识库

把资料（`.md` / `.txt`）放入 `knowledge/`，重启或 `POST /api/knowledge/reload` 生效。
配置在 `config.json → knowledge`：`enabled / dir / top_k / chunk_size`。
检索接口：`GET /api/knowledge/search?q=关键词`。

---

## 配置说明（节选）

```json
{
  "wechat": {
    "backend": "wechatauto-replica (UIA only)",
    "scan_interval": 5,
    "contacts": ["联系人1"],
    "reply_cooldown_seconds": 10,
    "max_replies_per_hour": 60,
    "max_replies_per_day": 200,
    "quiet_hours": { "start": "23:00", "end": "07:00" },
    "max_consecutive_failures": 3,
    "input_mode": "typing"
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
  "server": { "host": "0.0.0.0", "port": 5000, "password": "自动生成" }
}
```

**风控参数**：同一联系人冷却期内消息合并回复；每小时/每日回复上限（滚动窗口）；夜间静默时段不回复；回复延迟随内容长度变化 + 轮询随机抖动；连续发送失败自动停机；微信断线自动重连并重建基线。

---

## 工作原理

```
切换到目标会话（UIA）→ 读取消息控件树
    ↓
快照差分识别新消息（跳过自己发的/非文本）
    ↓
知识库 BM25 检索相关片段 + 加载联系人记忆(最近20条)
    ↓
构建提示词 → 调用 AI API 生成回复
    ↓
校验目标会话 → 模拟逐字输入发送 → UIA 回读确认
    ↓
保存对话到记忆库
```

---

## 常见问题

- **打开网页要密码**：首次启动自动生成，见运行日志或 `config.json → server.password`，可自行修改。
- **找不到微信窗口 / 未找到已登录主窗口**：确认微信已登录（停在登录二维码界面不算）；纯 UIA 路线无需管理员。
- **连接成功但不回复**：部分微信 4.x 版本主界面自绘渲染，UIA 读不到消息控件——需真机确认；另检查联系人是否在监控列表、是否处于夜间静默时段、AI Key 是否正确。
- **发送失败**：发送是 GUI 操作，需微信窗口在桌面可见、未锁屏；锁屏/最小化到托盘会失败。运行期间请勿手动操作微信。
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

### v3.0.0
- 🛡️ **安全整改**：账号被风控强制下线后，整体弃用"读进程内存 + 解密数据库"，改为**纯 UI 自动化**收发（不实例化 `WeChatDB`，发送强制 `verify=False`）
- 🔐 Web 控制台新增**访问密码鉴权**；API Key 不再回显到页面，留空保存保留原密钥
- 🎯 发送前**强校验目标会话**防止回错人；发送后 **UIA 回读确认**，已投递未确认时禁止重发
- 🔌 微信断线**自动重连**并重建基线
- ⏱️ 风控补全：每日回复上限、夜间静默时段、回复延迟随长度变化、轮询随机抖动
- 🧰 日志轮转（5MB×3）、配置原子写入、`启动.bat` 纳入版本库、无需管理员权限

### v2.0.0
- 🔁 控制层弃用 wxauto/wxautox，改用开源 wechatauto-replica（支持微信 4.2.0.53）
- ✨ 新增本地知识库 RAG（knowledge/ + BM25）并接入回复
- 🐛 修复 main.py 日志路径未导入导致的启动报错
- 🧹 清理 wxauto 残留与过时 UIA 调试脚本

### v1.0.0
- 基础自动回复、联系人记忆、Web 界面、多模型

## 许可证

MIT（本项目）；控制层后端 wechatauto-replica 为 Apache-2.0。
