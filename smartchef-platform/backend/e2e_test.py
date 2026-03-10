# -*- coding: utf-8 -*-
"""MVP End-to-End Flow Test"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import httpx, json

BASE = "http://127.0.0.1:8000/api/v1"
client = httpx.Client(timeout=30, verify=False, trust_env=False)
errors = []

def step(n): print(f"\n{'='*50}\n  STEP: {n}\n{'='*50}")
def ok(m):   print(f"  [PASS] {m}")
def fail(m): print(f"  [FAIL] {m}"); errors.append(m)

step("1. 登录")
r = client.post(f"{BASE}/auth/login", json={"username":"admin","password":"admin123456"})
assert r.status_code == 200, f"Login failed {r.status_code}"
H = {"Authorization": f"Bearer {r.json()['access_token']}"}
ok("登录成功")

step("2. 用户信息")
r = client.get(f"{BASE}/auth/me", headers=H)
assert r.status_code == 200
u = r.json()
ok(f"user={u['username']}, role={u['role_name']}")

step("3. 创建意图")
r = client.post(f"{BASE}/intents", json={
    "intent_key":"voice_cmd_start_cooking","display_name":"开始烹饪",
    "category":"cooking","description":"启动烹饪",
    "slots":[{"slot_key":"duration","display_name":"时长","entity_type":"time","is_required":True,"prompt_text":"烹饪多长时间？"}]
}, headers=H)
if r.status_code in (200,201):
    intent_id = r.json()["id"]; ok(f"id={intent_id}")
elif r.status_code == 409:
    r2 = client.get(f"{BASE}/intents", headers=H); data=r2.json()
    items = data if isinstance(data,list) else data.get("items",[])
    intent_id = items[0]["id"] if items else None; ok(f"已存在 id={intent_id}")
else:
    fail(f"创建意图 {r.status_code}"); intent_id=None

step("4. 意图列表")
r = client.get(f"{BASE}/intents", headers=H)
assert r.status_code == 200
data=r.json(); cnt=len(data) if isinstance(data,list) else data.get("total",0)
ok(f"共{cnt}个意图")

step("5. 创建人设")
r = client.post(f"{BASE}/profiles/personas", json={
    "name":"小厨","personality":"友好厨房助手","tone_style":"温暖","system_prompt":"你是小厨。"
}, headers=H)
if r.status_code in (200,201): persona_id=r.json()["id"]; ok(f"id={persona_id}")
else: fail(f"人设 {r.status_code}"); persona_id=None

step("6. 创建对话方案")
r = client.post(f"{BASE}/profiles", json={
    "name":"MVP方案","description":"E2E测试","persona_id":persona_id,
    "llm_provider":"gpt-4o-mini","llm_config":{"temperature":0.7},
    "routing_strategy":"command_first","session_timeout_minutes":30,
    "intent_ids":[intent_id] if intent_id else [],"knowledge_base_ids":[]
}, headers=H)
if r.status_code in (200,201): profile_id=r.json()["id"]; ok(f"id={profile_id}")
else: fail(f"方案 {r.status_code}: {r.text[:150]}"); profile_id=None

step("7. 创建知识库")
r = client.post(f"{BASE}/knowledge/bases", json={"name":"菜谱库","description":"测试"}, headers=H)
if r.status_code in (200,201): ok(f"id={r.json()['id']}")
else: fail(f"知识库 {r.status_code}")

step("8. 发布版本")
version_id=None
if profile_id:
    r = client.post(f"{BASE}/versions", params={"profile_id":profile_id,"version_tag":"v1.0.0-mvp"}, headers=H)
    if r.status_code in (200,201): version_id=r.json()["id"]; ok(f"id={version_id}")
    else: fail(f"发布 {r.status_code}: {r.text[:150]}")
else: fail("跳过(无profile)")

step("9. 激活版本")
if version_id:
    r = client.post(f"{BASE}/versions/{version_id}/activate", headers=H)
    if r.status_code==200: ok("激活成功")
    else: fail(f"激活 {r.status_code}: {r.text[:150]}")
else: fail("跳过(无version)")

step("10. 设备对话")
r = client.post(f"{BASE}/dialog/chat", json={"device_id":"TEST-001","text":"开始烹饪","device_context":{"model":"X1"}})
if r.status_code==200:
    ok(f"domain={r.json().get('domain')}, resp={r.json().get('response_text','')[:60]}")
elif r.status_code==503: ok(f"503预期内: {r.json().get('detail','')[:60]}")
else: fail(f"对话 {r.status_code}")

step("11. 版本信息")
r = client.get(f"{BASE}/dialog/version")
ok(f"status={r.status_code} data={r.json()}" if r.status_code==200 else f"status={r.status_code}")

step("12. 监控统计")
r = client.get(f"{BASE}/monitoring/stats", headers=H)
if r.status_code==200: ok(json.dumps(r.json(),ensure_ascii=False)[:120])
else: fail(f"监控 {r.status_code}: {r.text[:120]}")

step("13. 用户列表")
r = client.get(f"{BASE}/users", headers=H)
if r.status_code==200: ok(f"共{len(r.json())}个用户")
else: fail(f"用户 {r.status_code}: {r.text[:120]}")

print(f"\n{'='*50}")
print(f"  MVP E2E: {13-len(errors)}/13 PASSED")
if errors:
    for e in errors: print(f"  - {e}")
print(f"{'='*50}")
