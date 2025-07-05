# scripts/run_fixed_batch.py
import subprocess
import os
import glob
import platform
import re
import requests
import argparse
import time

from dotenv import load_dotenv
load_dotenv()

# ✅ 命令行参数解析
parser = argparse.ArgumentParser(description="批量定位杀号执行器")
parser.add_argument("--lottery", type=str, default="3d", help="彩种，如 3d / kl8")
parser.add_argument("--position", type=str, required=True, help="位置，如 baiwei / shiwei / gewei")
args = parser.parse_args()

query_issues_str = os.getenv("QUERY_ISSUES") or "None"
if query_issues_str == "None":
    query_issues = [None]
elif query_issues_str == "All":
    query_issues = ["All"]
else:
    query_issues = query_issues_str.split(",")
print(f"❓ 当前 query_issues 的值: {query_issues}")


LOTTERY = args.lottery
POSITION = args.position
# ✅ 新增：读取 GitHub Actions 的 CONFIG_FILE
CONFIG_FILE = os.getenv("CONFIG_FILE", "").strip()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ✅ 跨平台 Python
if os.getenv("GITHUB_ACTIONS", "") == "true":
    VENV_PYTHON = "python"
else:
    if platform.system() == "Windows":
        VENV_PYTHON = os.path.join(PROJECT_ROOT, '.venv', 'Scripts', 'python.exe')
    else:
        VENV_PYTHON = os.path.join(PROJECT_ROOT, '.venv', 'bin', 'python')

# ✅ CONFIGS 获取逻辑
if CONFIG_FILE:
    config_path = os.path.join(PROJECT_ROOT, f"config/fixed/{LOTTERY}/{POSITION}/{CONFIG_FILE}")
    if not os.path.exists(config_path):
        print(f"❌ 指定的 CONFIG_FILE 不存在: {config_path}")
        exit(1)
    CONFIGS = [config_path]
else:
    # 否则走批量
    CONFIGS = sorted(glob.glob(
        os.path.join(PROJECT_ROOT, f"config/fixed/{LOTTERY}/{POSITION}/sha_*.yaml")
    ))

start_time = time.time()
# 输出提示更清晰
if CONFIG_FILE:
    print(f"✅ [{LOTTERY}-{POSITION}] 执行单个配置文件：{CONFIGS[0]}")
else:
    print(f"✅ [{LOTTERY}-{POSITION}] 扫描到 {len(CONFIGS)} 个固定策略配置：")

for c in CONFIGS:
    print(f" - {c}")

outputs = []

for config in CONFIGS:
    print(f"\n🚀 Running config: {config}")
    env = os.environ.copy()
    env["STRATEGY_CONFIG_PATH"] = config
    env["LOTTERY"] = LOTTERY
    env["POSITION"] = POSITION

    print(env["STRATEGY_CONFIG_PATH"])

    process = subprocess.Popen(
        [VENV_PYTHON, "scripts/run_fixed.py"],
        env=env,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8"
    )
    out, _ = process.communicate()

    print(out)  # ⏪ 输出
    outputs.append(out)

print("\n========== Final Summary ==========")

final_lines = []
for idx, out in enumerate(outputs):
    lines = [line for line in out.splitlines() if "🔥" in line]
    if lines:
        final_lines.append(f"【{os.path.basename(CONFIGS[idx])}】")
        final_lines.extend(lines)

if final_lines:
    print("\n".join(final_lines))
else:
    print("⚠️ 本次没有检测到任何 🔥 行")

# ===============================
# 🔔 拼装企业微信消息（批量汇总）
# ===============================

final_blocks = []
merged_sha_nums = []
latest_issue = "未知"

for idx, out in enumerate(outputs):
    block = []
    block.append(f"【{os.path.basename(CONFIGS[idx])}】")

    lines = [line for line in out.splitlines() if "🔥" in line]
    result_lines = []
    for line in lines:
        # 只收含 [] 的最终推荐行
        if "[" in line and "]" in line:
            result_lines.append(line.strip())
            match = re.search(r"\[([0-9,\s]+)\]", line)
            if match:
                nums = [int(n.strip()) for n in match.group(1).split(",")]
                merged_sha_nums.extend(nums)

    if result_lines:
        for line in result_lines:
            block.append(f"   {line}")
    else:
        block.append("   ⚠️ 不杀！")

    final_blocks.append("\n".join(block))

    if latest_issue == "未知":
        m = re.search(r"🎯 查询期号: (\d+)", out)
        if m:
            latest_issue = m.group(1)

merged_sha_nums = sorted(set(merged_sha_nums))



end_time = time.time()
elapsed = int(end_time - start_time)
hours = elapsed // 3600
minutes = (elapsed % 3600) // 60

# === 定位位名称（对齐 utils 的映射思路） ===
position_name_map = {}
if LOTTERY in ["p5", "排列5", "排列五"]:
    position_name_map = {0: "万位", 1: "千位", 2: "百位", 3: "十位", 4: "个位"}
else:
    position_name_map = {0: "百位", 1: "十位", 2: "个位"}

pos_map = {
    "baiwei": 0,
    "shiwei": 1,
    "gewei": 2
}
pos_idx = pos_map.get(POSITION, 0)  # 默认百位
pos_name_cn = position_name_map.get(pos_idx, POSITION)
LOTTERY_DISPLAY_NAME = {
    "3d": "福彩3D",
    "p3": "排列3",
    "p5": "排列5",
    "kl8": "快乐8"
}
# === 拼装最终消息体 ===
msg = []
lottery_cn = LOTTERY_DISPLAY_NAME.get(LOTTERY, LOTTERY)
msg.append(f"【{lottery_cn}-{latest_issue}期-{pos_name_cn}杀号】")
msg.append(f"🏷️ Actions 运行编号: #{os.getenv('GITHUB_RUN_NUMBER', '0')}")
msg.append(f"🏷️ 总分析用时: {hours}小时{minutes}分钟")
msg.append(f"📦 固定策略配置: {len(CONFIGS)} 个")
msg.append("=============")
msg.append("📌 详细分期结果:")
msg.extend(final_blocks)
msg.append("=============")
msg.append(f"✅ 最终汇总结果（共 {len(merged_sha_nums)} 个）:\n")
msg.append(", ".join(str(n) for n in merged_sha_nums))

msg.append(f"🎯 {pos_name_cn} 杀：{', '.join(str(n) for n in merged_sha_nums)}")

# 最后拼接
msg_text = "\n".join(msg)

# === 推送到企业微信（分段+key） ===
wechat_api_url = os.getenv("WECHAT_API_URL")
MAX_LEN = 1800

def send_wechat_message(msg):
    payload = {"content": msg}
    headers = {"x-api-key": os.getenv("WECHAT_API_KEY")}
    try:
        resp = requests.post(wechat_api_url, json=payload, headers=headers, timeout=10)
        print(f"✅ 企业微信推送状态: {resp.status_code}")
        print(f"✅ 企业微信响应: {resp.text}")
    except Exception as e:
        print(f"❌ 企业微信消息推送失败: {e}")

# ✅ 只要是【实战模式】，即 query_issues = [None] 就发
if query_issues != ["All"]:
    if wechat_api_url:
        msg_lines = msg_text.splitlines()
        cur_msg = ""
        for line in msg_lines:
            if len(cur_msg) + len(line) + 1 > MAX_LEN:
                send_wechat_message(cur_msg)
                cur_msg = ""
            cur_msg += (line + "\n")
        if cur_msg.strip():
            send_wechat_message(cur_msg)
    else:
        print("❌ 未配置 WECHAT_API_URL，企业微信消息未发送")
else:
    print(f"🟢 【回测模式】【已跳过：批量汇总消息发送】，query_issues={query_issues}")
