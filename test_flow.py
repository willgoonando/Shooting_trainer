"""
射击训练器 APP 后端 —— 完整流程测试
运行方式：cd ~/Desktop/shooting_trainer && source venv/bin/activate && python test_flow.py
"""
import os
import sys
import json
import random
import numpy as np
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE = "http://127.0.0.1:8000/api/v1"
BASE_PAGE = "http://127.0.0.1:8000/api"  # page 接口在 /api/page/ 下
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
    # 模拟 IMU 数据（120采样点 = 300ms @ 400Hz，真实密度）
    # 击发前 0-80 采样点（200ms 稳定瞄准），击发时刻 ~80，击发后 80-120（100ms 后坐力+恢复）
    def make_imu():
        accel, gyro = [], []
        for j in range(120):
            t = j / 400.0  # 秒
            if t < 0.2:  # 击发前：稳定瞄准，小幅度抖动
                ax = random.gauss(0, 0.02) + 0.005 * np.sin(j*0.3)
                ay = random.gauss(0, 0.02) + 0.005 * np.cos(j*0.3)
                az = random.gauss(0, 0.01) + 0.01 * np.sin(j*0.2)
                gx = random.gauss(0, 0.003)
                gy = random.gauss(0, 0.003)
                gz = random.gauss(0, 0.001)
            elif t < 0.205:  # 击发瞬间：Jerk 尖峰
                mag = random.uniform(3.0, 8.0)
                ax = mag * 0.3
                ay = mag * 0.5
                az = mag
                gx = random.uniform(0.2, 0.5)
                gy = random.uniform(0.1, 0.3)
                gz = random.uniform(0.05, 0.1)
            else:  # 击发后：衰减振荡
                decay = np.exp(-(t - 0.205) * 30)
                ax = random.gauss(0, 0.3) * decay
                ay = random.gauss(0, 0.3) * decay
                az = random.gauss(0, 0.5) * decay
                gx = random.gauss(0, 0.1) * decay
                gy = random.gauss(0, 0.1) * decay
                gz = random.gauss(0, 0.05) * decay
            accel.append([round(ax, 4), round(ay, 4), round(az, 4)])
            gyro.append([round(gx, 4), round(gy, 4), round(gz, 4)])
        return accel, gyro

    accel, gyro = make_imu()
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

# ===== Step 9: 页面级聚合接口（文档 9.0） =====
step(9, "测试页面聚合接口 /api/page/*")
# page 接口在 /api/page/ 下，BASE_PAGE 而非 BASE
def req_page(method, path, token=None):
    url = f"{BASE_PAGE}{path}"
    body = json.dumps({}).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = Request(url, data=body, headers=headers, method=method)
    resp = urlopen(r)
    return json.loads(resp.read())

resp = req_page("GET", f"/page/training-result/full/?session_id={SESSION_ID}", token=TOKEN)
print(f"  training-result-full: 评分={resp['overall_score']['total_score']}, 图表数据={len(resp.get('score_curve', []))}条")
resp = req_page("GET", "/page/history/records/", token=TOKEN)
print(f"  history: {len(resp.get('history', []))} 条记录, 等级={resp.get('skill_level')}")
resp = req_page("GET", "/page/home/summary/", token=TOKEN)
print(f"  home: 总训练={resp['total_sessions']}次, 总枪数={resp['total_shots']}")

print(f"\n{'='*60}")
print(f"  ✅ 完整流程测试成功！")
print(f"  Session ID: {SESSION_ID}")
print(f"{'='*60}")
