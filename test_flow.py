"""
射击训练器 APP 后端 —— 完整流程测试
运行方式：cd ~/Desktop/shooting_trainer && source venv/bin/activate && python test_flow.py
"""
import os
import sys
import json
import random
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE = "http://127.0.0.1:8000/api/v1"
EMAIL = f"test_{random.randint(1000,9999)}@example.com"
PASSWORD = "123456"
SN = f"SN{random.randint(10000,99999)}"

def req(method, path, data=None, token=None):
    """发送 HTTP 请求"""
    url = f"{BASE}{path}"
    body = json.dumps(data).encode() if data else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = Request(url, data=body, headers=headers, method=method)
    try:
        resp = urlopen(r)
        return json.loads(resp.read())
    except HTTPError as e:
        return json.loads(e.read())

def step(n, title):
    print(f"\n{'='*60}")
    print(f"  Step {n}: {title}")
    print(f"{'='*60}")

# ===== Step 1: 注册 =====
step(1, "注册用户")
resp = req("POST", "/accounts/auth/register/", {"email": EMAIL, "password": PASSWORD, "code": "000000"})
print(f"  用户: {resp['user']['email']}")
TOKEN = resp['access']
print(f"  Token: {TOKEN[:40]}...")

# ===== Step 2: 创建靶纸 =====
step(2, "创建靶纸模板")
ring_defs = [{"ring": r, "radius_mm": r*5} for r in range(10, 0, -1)]
resp = req("POST", "/targets/templates/", {"name": "标准10环靶", "ring_count": 10, "ring_definitions": ring_defs}, TOKEN)
TARGET_ID = resp['id']
print(f"  靶纸ID: {TARGET_ID}")

# ===== Step 3: 绑定设备 =====
step(3, "绑定设备")
resp = req("POST", "/devices/", {"device_sn": SN, "device_name": "射击训练器-001", "firmware_version": "1.0.0", "battery_level": 85, "is_active": True, "mac_address": "AA:BB:CC:DD:EE:FF"}, TOKEN)
DEVICE_ID = resp['id']
print(f"  设备ID: {DEVICE_ID}")

# ===== Step 4: 创建 Session =====
step(4, "创建训练 Session")
resp = req("POST", "/training/sessions/", {"distance_meters": 10.0, "notes": "测试训练"}, TOKEN)
SESSION_ID = resp['id']
print(f"  Session ID: {SESSION_ID}")

# ===== Step 5: 开始训练 =====
step(5, "开始训练")
resp = req("POST", f"/training/sessions/{SESSION_ID}/start/", token=TOKEN)
print(f"  状态: {resp['status']}")

# ===== Step 6: 上传 15 枪模拟数据 =====
step(6, "上传 15 枪模拟 Shot 数据")
shots = []
for i in range(1, 16):
    hx = round(random.gauss(0, 15), 2)
    hy = round(random.gauss(0, 15), 2)
    dist = (hx**2 + hy**2)**0.5
    ring = max(1, min(10, 10 - int(dist / 5)))
    # 模拟 IMU 数据（12个采样点 = ~300ms @ 400Hz）
    accel = [[0.01,0.02,1.0],[0.02,0.01,0.98],[0.05,0.03,0.95],[0.1,0.05,0.9],
             [0.15,0.08,0.87],[0.2,0.1,0.85],[0.5,0.3,0.7],[2.0,1.5,3.0],
             [5.0,3.0,8.0],[2.0,1.0,3.5],[0.5,0.3,1.5],[0.1,0.05,1.0]]
    gyro = [[0.001,0.002,0.],[0.002,0.001,0.],[0.005,0.003,0.01],[0.01,0.005,0.02],
            [0.015,0.008,0.03],[0.02,0.01,0.05],[0.05,0.03,0.15],[0.2,0.15,0.8],
            [0.5,0.3,1.5],[0.2,0.1,0.8],[0.05,0.02,0.3],[0.01,0.005,0.1]]
    shots.append({"shot_number": i, "hit_x": hx, "hit_y": hy, "hit_ring": ring,
                  "imu_data": {"accel": accel, "gyro": gyro}})

resp = req("POST", f"/training/sessions/{SESSION_ID}/upload_shots/", {"shots": shots}, TOKEN)
print(f"  已上传: {resp.get('count', 0)} 枪")

# ===== Step 7: 结束训练（触发 AI） =====
step(7, "结束训练 & 触发 AI 分析")
resp = req("POST", f"/training/sessions/{SESSION_ID}/end/", token=TOKEN)
print(f"  状态: {resp['status']}, 总枪数: {resp['total_shots']}, 时长: {resp.get('duration_seconds', '?')}秒")

# ===== Step 8: 查看 AI 结果 =====
step(8, "查看 AI 分析结果")
resp = req("GET", f"/ai/results/session_result/?session_id={SESSION_ID}", token=TOKEN)
print(f"  总枪数: {resp['total_shots']}")
ms = resp.get('motion_score') or {}
print(f"  动作评分: Trigger={ms.get('trigger_control','?')}, Stability={ms.get('stability','?')}, Total={ms.get('total_score','?')}")
acc = resp.get('accuracy_score') or {}
print(f"  准度评分: Ring={acc.get('ring_score','?')}, Group={acc.get('group_score','?')}, Total={acc.get('total_score','?')}")
ov = resp.get('overall_score') or {}
print(f"  综合评分: {ov.get('total_score', '?')}")
diag = resp.get('diagnosis') or {}
issues = diag.get('issues', [])
if issues:
    print(f"  诊断问题:")
    for iss in issues:
        print(f"    - {iss['label']}: {iss['description']}")
rec = resp.get('recommendation') or {}
recs = rec.get('items', [])
if recs:
    print(f"  训练建议:")
    for r in recs:
        print(f"    - {r['drill']} ({r['duration_minutes']}分钟): {r['description']}")

print(f"\n{'='*60}")
print(f"  ✅ 完整流程测试成功！")
print(f"  Session ID: {SESSION_ID}")
print(f"{'='*60}")
