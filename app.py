"""
Web管理界面
提供API和页面用于配置和管理系统
"""

import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

from config import save_config, add_contact, remove_contact

# 项目根目录
ROOT = Path(__file__).parent


def create_app(bot) -> Flask:
    """创建Flask应用"""
    app = Flask(
        __name__,
        template_folder=str(ROOT / "templates"),
        static_folder=str(ROOT / "static")
    )
    CORS(app)

    @app.route("/")
    def index():
        return render_template("index.html", status=bot.get_status())

    @app.route("/contacts")
    def contacts_page():
        contacts = bot.config.get("wechat", {}).get("contacts", [])
        return render_template("contacts.html", contacts=contacts)

    @app.route("/ai-config")
    def ai_config_page():
        ai = bot.config.get("ai", {})
        return render_template("ai_config.html", ai=ai)

    @app.route("/logs")
    def logs_page():
        return render_template("logs.html")

    # ---- API ----

    @app.route("/api/status")
    def api_status():
        return jsonify(bot.get_status())

    @app.route("/api/system/<action>", methods=["POST"])
    def api_system(action):
        if action == "start":
            if not bot.running:
                threading.Thread(target=bot.start, daemon=True).start()
                return jsonify({"msg": "正在启动..."})
            return jsonify({"msg": "已在运行"})
        elif action == "stop":
            bot.stop()
            return jsonify({"msg": "已停止"})
        return jsonify({"error": "无效操作"}), 400

    @app.route("/api/contacts", methods=["GET"])
    def api_get_contacts():
        return jsonify({"contacts": bot.config.get("wechat", {}).get("contacts", [])})

    @app.route("/api/contacts", methods=["POST"])
    def api_add_contact():
        data = request.get_json()
        if not data or not data.get("name", "").strip():
            return jsonify({"error": "名称不能为空"}), 400
        add_contact(bot.config, data["name"].strip())
        return jsonify({"msg": f"已添加 {data['name']}"})

    @app.route("/api/contacts/<name>", methods=["DELETE"])
    def api_del_contact(name):
        remove_contact(bot.config, name)
        return jsonify({"msg": f"已删除 {name}"})

    @app.route("/api/ai-config/<model>", methods=["POST"])
    def api_update_ai(model):
        data = request.get_json()
        models = bot.config.setdefault("ai", {}).setdefault("models", {})
        models.setdefault(model, {}).update(data)
        save_config(bot.config)
        return jsonify({"msg": f"已更新 {model}"})

    @app.route("/api/ai-config/default", methods=["POST"])
    def api_switch_model():
        data = request.get_json()
        name = data.get("model", "")
        if bot.replier.switch_model(name):
            bot.config.setdefault("ai", {})["default_model"] = name
            save_config(bot.config)
            return jsonify({"msg": f"已切换到 {name}"})
        return jsonify({"error": "模型不可用"}), 400

    @app.route("/api/ai-config/test/<model>", methods=["POST"])
    def api_test_model(model):
        if bot.replier.test_model(model):
            return jsonify({"msg": "测试成功"})
        return jsonify({"error": "测试失败"}), 500

    @app.route("/api/ai-config/reply-mode", methods=["POST"])
    def api_reply_mode():
        data = request.get_json()
        mode = data.get("mode", "direct")
        if mode not in ["direct", "agent"]:
            return jsonify({"error": "无效的回复模式"}), 400
        bot.config.setdefault("ai", {})["reply_mode"] = mode
        save_config(bot.config)
        return jsonify({"msg": f"已切换到{mode}模式"})

    @app.route("/api/ai-config/add", methods=["POST"])
    def api_add_model():
        data = request.get_json()
        name = data.get("name", "").strip()
        if not name:
            return jsonify({"error": "模型名称不能为空"}), 400
        models = bot.config.setdefault("ai", {}).setdefault("models", {})
        models[name] = {
            "api_key": data.get("api_key", ""),
            "base_url": data.get("base_url", ""),
            "model": data.get("model", "")
        }
        save_config(bot.config)
        return jsonify({"msg": f"已添加 {name}"})

    @app.route("/api/ai-config/<model>", methods=["DELETE"])
    def api_delete_model(model):
        models = bot.config.get("ai", {}).get("models", {})
        if model in models:
            del models[model]
            save_config(bot.config)
            return jsonify({"msg": f"已删除 {model}"})
        return jsonify({"error": "模型不存在"}), 404

    @app.route("/api/ai-config/agent/add", methods=["POST"])
    def api_add_agent():
        data = request.get_json()
        name = data.get("name", "").strip()
        if not name:
            return jsonify({"error": "智能体名称不能为空"}), 400
        agents = bot.config.setdefault("ai", {}).setdefault("agents", {})
        agents[name] = {
            "api_key": data.get("api_key", ""),
            "base_url": data.get("base_url", ""),
            "model": data.get("model", "")
        }
        save_config(bot.config)
        return jsonify({"msg": f"已添加智能体 {name}"})

    @app.route("/api/ai-config/agent/<name>", methods=["DELETE"])
    def api_delete_agent(name):
        agents = bot.config.get("ai", {}).get("agents", {})
        if name in agents:
            del agents[name]
            save_config(bot.config)
            return jsonify({"msg": f"已删除智能体 {name}"})
        return jsonify({"error": "智能体不存在"}), 404

    @app.route("/api/ai-config/system-prompt", methods=["POST"])
    def api_system_prompt():
        data = request.get_json()
        prompt = data.get("prompt", "")
        bot.config.setdefault("ai", {})["system_prompt"] = prompt
        save_config(bot.config)
        if hasattr(bot.replier, 'system_prompt'):
            bot.replier.system_prompt = prompt
        return jsonify({"msg": "已保存系统提示词"})

    @app.route("/api/logs")
    def api_logs():
        lines = request.args.get("lines", 100, type=int)
        try:
            from config import LOG_PATH
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
            return jsonify({"logs": all_lines[-lines:]})
        except FileNotFoundError:
            return jsonify({"logs": []})

    # ---- 记忆管理 API ----

    @app.route("/memory")
    def memory_page():
        return render_template("memory.html")

    @app.route("/api/memory/stats")
    def api_memory_stats():
        return jsonify(bot.memory.get_stats())

    @app.route("/api/memory/contacts")
    def api_memory_contacts():
        return jsonify({"contacts": bot.memory.get_all_contacts()})

    @app.route("/api/memory/<contact>/messages")
    def api_memory_messages(contact):
        limit = request.args.get("limit", 50, type=int)
        return jsonify({"messages": bot.memory.get_recent_messages(contact, limit)})

    @app.route("/api/memory/<contact>", methods=["DELETE"])
    def api_memory_clear(contact):
        bot.memory.clear_contact(contact)
        return jsonify({"msg": f"已清除 [{contact}] 的记忆"})

    @app.route("/api/memory/<contact>/notes", methods=["POST"])
    def api_memory_notes(contact):
        data = request.get_json()
        notes = data.get("notes", "")
        bot.memory.update_notes(contact, notes)
        return jsonify({"msg": "已更新备注"})

    return app
