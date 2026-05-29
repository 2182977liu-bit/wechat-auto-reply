"""检查首页HTML内容"""
import requests

resp = requests.get("http://localhost:5000/", timeout=5)
print(resp.text[:2000])
