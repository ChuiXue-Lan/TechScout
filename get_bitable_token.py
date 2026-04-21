"""一次性工具：通过 wiki node token 获取真实的 bitable app_token"""
import os
import requests

APP_ID     = os.environ["FEISHU_APP_ID"]
APP_SECRET = os.environ["FEISHU_APP_SECRET"]
WIKI_TOKEN = os.environ["FEISHU_APP_TOKEN"]

# 1. 获取 tenant_access_token
r = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": APP_ID, "app_secret": APP_SECRET},
)
token = r.json()["tenant_access_token"]
print(f"tenant_access_token: {token[:10]}...")

# 2. 查询 wiki node
r = requests.get(
    "https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node",
    headers={"Authorization": f"Bearer {token}"},
    params={"token": WIKI_TOKEN},
)
print(f"响应: {r.status_code}")
print(r.text)
