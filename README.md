# 微信自动回复 AI 机器人

<div align="center">

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![WeChat](https://img.shields.io/badge/WeChat-4.2.0.53-07C160?style=for-the-badge&logo=wechat&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**纯 UI 自动化的智能微信自动回复机器人：不读进程内存、不解密数据库，支持联系人独立记忆 + 本地知识库 RAG**

</div>

---

## ⚠️ 项目现状（2026-11-24 · 架构过渡期，暂不可开箱即用）

本项目处于**控制层重构的过渡阶段**，开源目的是记录方案演进与风控教训。当前代码在新版微信（`Weixin.exe`）上**收不到消息，因此不会自动回复**；AI 回复、知识库 RAG、联系人记忆、Web 控制台等外围模块完整可用。

收消息链路经历了三代，前两代都已因安全原因废弃：

| 代际 | 方案 | 结局 |
| --- | --- | --- |
| v1 | 读进程内存取密钥 + SQLCipher 数据库解密 | 功能可用，但实测**触发腾讯风控，账号被强制下线**，废弃 |
| v2 | UIA 控件树读取 | 新版微信**不对外暴露消息控件**；后端库的"热激活"本质是向进程写入一个字节（WriteProcessMemory）强制开启无障碍树，**仍属内存篡改**，弃用 |
| v3 | OCR 识屏（截图 + 系统 OCR + 模拟键鼠，零进程入侵） | **方向已确定，尚未实现**，见路线图 |

---

## 功能特性

- **智能自动回复** - 增量监听微信新消息，自动调用 AI 生成回复
- **独立记忆系统** - 每个联系人独立对话历史，SQLite 持久化（`data/memory.db`）
- **本地知识库 RAG** - `knowledge/` 目录文档切块 + BM25 检索，回复前注入相关片段，离线可用
- **多 AI 模型** - DeepSeek / 通义千问 / 小米等 OpenAI 兼容接口
- **Web 控制台** - 启动/停止、联系人、AI 配置、记忆、日志、知识库管理

## 控制层后端（演进说明）

控制层复用开源项目 **[wechatauto-replica](https://github.com/fanyuantaier/wechatauto-replica)**（Apache-2.0）的部分组件，**不再使用 wxauto / wxautox**。

- **收消息**：处于重构期，见上方「项目现状」。目标是 OCR 识屏：截图 + Windows 系统 OCR 还原消息气泡，按坐标区分自己/对方，快照差分识别新消息。
- **发消息**：模拟键鼠逐字输入（SendInput），已实现；发送后回读确认。
- **安全红线**：不读进程内存、不写进程内存、不解密数据库。注意：后端库的 UIA 驱动会"热激活"（写 Weixin.dll 的无障碍标志位），**纯安全模式下必须整条禁用 UIA 引擎**，仅复用其 OCR / 键鼠 / 布局组件。
- **运行要求**：微信已登录、窗口在桌面可见；运行期间不能手动操作微信。

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

## 工作原理（目标流程，收消息段待实现）

```
切换到目标会话 → 截图 + 系统 OCR 读取消息气泡（按坐标区分自己/对方）
    ↓
快照差分 + 模糊去重识别新消息（跳过自己发的/非文本）
    ↓
知识库 BM25 检索相关片段 + 加载联系人记忆(最近20条)
    ↓
构建提示词 → 调用 AI API 生成回复
    ↓
校验目标会话 → 模拟逐字输入发送 → 回读确认
    ↓
保存对话到记忆库
```

---

## 常见问题

- **打开网页要密码**：首次启动自动生成，见运行日志或 `config.json → server.password`，可自行修改。
- **找不到微信窗口 / 未找到已登录主窗口**：当前收消息控制层处于重构期，新版微信上属预期现象，见「项目现状」。
- **连接成功但不回复**：同上；另检查联系人是否在监控列表、是否处于夜间静默时段、AI Key 是否正确。
- **发送失败**：发送是 GUI 操作，需微信窗口在桌面可见、未锁屏；锁屏/最小化到托盘会失败。运行期间请勿手动操作微信。
- **知识库不生效**：确认 `knowledge.enabled=true`、目录有 `.md/.txt`、修改后重载。
- **备份记忆**：复制 `data/memory.db`。

---

## 已知问题

- **收消息控制层待重写为 OCR**（当前在新版微信上收不到消息，见「项目现状」）
- 群聊未适配：@消息、群内发送者识别、群/个人区分均缺失
- 联系人页只能读取当前会话列表，无法搜索未在列表中的联系人
- 监控依赖真实窗口切换：运行时不能手动操作微信，且会把未读会话点成已读
- OCR 路线的固有难点（设计阶段已识别）：识别文本抖动需要模糊去重、仅一屏消息可见、窗口必须前台可见、回复延迟高于控件方案

## 路线图

1. OCR 收消息控制层，含**只读试运行模式**（先只记录识别结果不自动回复，确认稳定后再开发送）
2. 发送后 OCR 回读确认完善
3. 群聊支持
4. 商用客服部署场景建议评估**企业微信官方 API**——个人微信没有官方消息接口，这是合规与稳定性的根本解法

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

### v3.0.1
- 📖 开源收尾：补充「项目现状 / 已知问题 / 路线图 / 免责声明」，明确当前为架构过渡期、暂不可开箱即用
- 🧾 修正文档中对 UIA 方案的过度承诺：热激活本质是写进程内存，已弃用，方向改为 OCR 识屏
- ⚖️ 补充 MIT LICENSE；确认密钥、密码、配置文件从未入库

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

## 免责声明

仅供学习与技术研究。微信官方未开放个人号自动化接口，任何形式的客户端自动化都可能违反使用协议并导致账号受限或被强制下线（本项目实测遭遇过）。请自行评估风险、不要使用主号测试，一切后果由使用者自负。

## 许可证

MIT（本项目）；控制层后端 wechatauto-replica 为 Apache-2.0。
