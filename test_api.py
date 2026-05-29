"""测试所有API端点"""
import requests
import json

BASE = "http://localhost:5000"
results = []

def test(name, method, url, **kwargs):
    try:
        if method == "GET":
            r = requests.get(f"{BASE}{url}", timeout=5, **kwargs)
        elif method == "POST":
            r = requests.post(f"{BASE}{url}", timeout=5, **kwargs)
        elif method == "DELETE":
            r = requests.delete(f"{BASE}{url}", timeout=5, **kwargs)
        ok = r.status_code < 400
        results.append((name, ok, r.status_code, r.text[:80]))
    except Exception as e:
        results.append((name, False, 0, str(e)[:80]))

test("首页", "GET", "/")
test("状态API", "GET", "/api/status")
test("联系人页", "GET", "/contacts")
test("AI配置页", "GET", "/ai-config")
test("日志页", "GET", "/logs")
test("日志API", "GET", "/api/logs?lines=10")
test("联系人列表API", "GET", "/api/contacts")
test("停止系统", "POST", "/api/system/stop")

print(f"{'功能':<15} {'状态':<6} {'码':<5} {'响应'}")
print("-" * 70)
for name, ok, code, resp in results:
    s = "OK" if ok else "FAIL"
    print(f"{name:<15} {s:<6} {code:<5} {resp}")

print(f"\n总计: {sum(1 for _,ok,_,_ in results if ok)}/{len(results)} 通过")
