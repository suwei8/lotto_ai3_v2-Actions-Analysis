# scripts/run_3d.py
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
import yaml
import builtins
from utils.logger import log, save_log_file_if_needed, init_log_capture
from utils.db import get_connection
from utils.expert_hit_analysis import run_hit_analysis_batch

def parse_int_env(key, default=None):
    val = os.getenv(key)
    # 如果 val 本身是 None 或空或"None"字符串
    if val is None or str(val).strip() == "" or str(val).lower() == "none":
        return None if default in (None, "None", "") else default
    try:
        return int(val)
    except Exception:
        return None if default in (None, "None", "") else default



# === 加载 config ===
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
yaml_path = os.path.join(base_dir, "config", "3d_config.yaml")

with open(yaml_path, encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)["DEFAULTS"]


# === 统一变量 ===
check_mode = os.getenv("CHECK_MODE") or "dingwei"
lottery_name = os.getenv("LOTTERY_NAME") or CONFIG["LOTTERY_NAME"]
analysis_mode = os.getenv("ANALYSIS_MODE") or CONFIG["ANALYSIS_MODE"]
QUERY_ISSUES = os.getenv("QUERY_ISSUES") or CONFIG["QUERY_ISSUES"]
# 先强制 config 默认值变成 NoneType
_config_limit = CONFIG.get("ALL_MODE_LIMIT", None)
if _config_limit in ("None", ""):
    _config_limit = None

all_mode_limit = parse_int_env("ALL_MODE_LIMIT", _config_limit)
enable_hit_check = str(os.getenv("ENABLE_HIT_CHECK") or CONFIG["ENABLE_HIT_CHECK"]).lower() == "true"

print(f"✅ CHECK_MODE: {check_mode}")
print(f"✅ LOTTERY_NAME: {lottery_name}")
print(f"✅ QUERY_ISSUES: {QUERY_ISSUES}")
# === 初始化 ===

if "__print_original__" not in builtins.__dict__:
    builtins.__dict__["__print_original__"] = print
init_log_capture(script_name_hint=os.path.basename(__file__))
print = log

conn = get_connection()

# === 其它参数 ===
def safe_json_load(env_key, default):
    val = os.getenv(env_key)
    if val is None or val.strip() == "":
        return default
    try:
        return json.loads(val)
    except Exception as e:
        print(f"❌ 解析环境变量 {env_key} 失败，使用默认值: {default}，错误: {e}")
        return default

query_issues_str = os.getenv("QUERY_ISSUES") or CONFIG["QUERY_ISSUES"]
if query_issues_str == "None":
    query_issues = [None]
elif query_issues_str == "All":
    query_issues = ["All"]
elif "," in query_issues_str:
    query_issues = query_issues_str.split(",")
else:
    query_issues = [query_issues_str]

dingwei_sha_pos = parse_int_env("DINGWEI_SHA_POS", 0)
enable_track_open_rank = str(os.getenv("ENABLE_TRACK_OPEN_RANK") or CONFIG["ENABLE_TRACK_OPEN_RANK"]).lower() == "true"
log_save_mode = str(os.getenv("LOG_SAVE_MODE") or CONFIG["LOG_SAVE_MODE"]).lower() == "true"

query_playtype_name = os.getenv("QUERY_PLAYTYPE_NAME", "百位定1")
analyze_playtype_name = os.getenv("ANALYZE_PLAYTYPE_NAME", "百位定1")

hit_rank_list = safe_json_load("HIT_RANK_LIST", [1])
hit_count_conditions = safe_json_load("HIT_COUNT_CONDITIONS", {})

lookback_n = parse_int_env("LOOKBACK_N", 0)

# ENABLE_SHA1 兼容数组或布尔字符串
enable_sha1_str = os.getenv("ENABLE_SHA1", "[]")
try:
    enable_sha1 = json.loads(enable_sha1_str) if enable_sha1_str.strip() else []
except Exception:
    enable_sha1 = enable_sha1_str.lower() == "true"

enable_sha2 = os.getenv("ENABLE_SHA2", "False").lower() == "true"
enable_dan1 = os.getenv("ENABLE_DAN1", "False").lower() == "true"
enable_dan2 = os.getenv("ENABLE_DAN2", "False").lower() == "true"

enable_dingwei_sha_str = os.getenv("ENABLE_DINGWEI_SHA", "False")
if enable_dingwei_sha_str in ["True", "False"]:
    enable_dingwei_sha = enable_dingwei_sha_str == "True"
else:
    try:
        enable_dingwei_sha = json.loads(enable_dingwei_sha_str)
    except Exception:
        enable_dingwei_sha = False

enable_dingwei_sha2 = os.getenv("ENABLE_DINGWEI_SHA2", "False").lower() == "true"
enable_dingwei_sha3 = os.getenv("ENABLE_DINGWEI_SHA3", "False").lower() == "true"
# ✅ 更智能的解析，支持 "[1]" / "True" / "False" 等
enable_dingwei_dan1_raw = os.getenv("ENABLE_DINGWEI_DAN1", "False")
try:
    enable_dingwei_dan1 = json.loads(enable_dingwei_dan1_raw)
except Exception:
    enable_dingwei_dan1 = enable_dingwei_dan1_raw.lower() == "true"


skip_if_few_sha1 = os.getenv("SKIP_IF_FEW_SHA1", "False").lower() == "true"
skip_if_few_sha2 = os.getenv("SKIP_IF_FEW_SHA2", "False").lower() == "true"
skip_if_few_dan1 = os.getenv("SKIP_IF_FEW_DAN1", "False").lower() == "true"
skip_if_few_dan2 = os.getenv("SKIP_IF_FEW_DAN2", "False").lower() == "true"
skip_if_few_dingwei_sha = os.getenv("SKIP_IF_FEW_DINGWEI_SHA", "False").lower() == "true"
skip_if_few_dingwei_sha2 = os.getenv("SKIP_IF_FEW_DINGWEI_SHA2", "False").lower() == "true"
skip_if_few_dingwei_sha3 = os.getenv("SKIP_IF_FEW_DINGWEI_SHA3", "False").lower() == "true"

resolve_tie_mode_sha1 = os.getenv("RESOLVE_TIE_MODE_SHA1", "False")
resolve_tie_mode_sha2 = os.getenv("RESOLVE_TIE_MODE_SHA2", "False")
resolve_tie_mode_dan1 = os.getenv("RESOLVE_TIE_MODE_DAN1", "False")
resolve_tie_mode_dan2 = os.getenv("RESOLVE_TIE_MODE_DAN2", "False")
resolve_tie_mode_dingwei_sha = os.getenv("RESOLVE_TIE_MODE_DINGWEI_SHA", "False")
resolve_tie_mode_dingwei_sha2 = os.getenv("RESOLVE_TIE_MODE_DINGWEI_SHA2", "False")
resolve_tie_mode_dingwei_sha3 = os.getenv("RESOLVE_TIE_MODE_DINGWEI_SHA3", "False")
resolve_tie_mode_dingwei_dan1 = os.getenv("RESOLVE_TIE_MODE_DINGWEI_DAN1", "False")

reverse_on_tie_dingwei_sha = os.getenv("REVERSE_ON_TIE_DINGWEI_SHA", "False").lower() == "true"
reverse_on_tie_dingwei_sha2 = os.getenv("REVERSE_ON_TIE_DINGWEI_SHA2", "False").lower() == "true"
reverse_on_tie_dingwei_sha3 = os.getenv("REVERSE_ON_TIE_DINGWEI_SHA3", "False").lower() == "true"
reverse_on_tie_dingwei_dan1 = os.getenv("REVERSE_ON_TIE_DINGWEI_DAN1", "False").lower() == "true"

analysis_kwargs = dict(
    query_playtype_name=query_playtype_name,
    analyze_playtype_name=analyze_playtype_name,
    mode=analysis_mode,
    hit_rank_list=hit_rank_list,
    hit_count_conditions=hit_count_conditions,
    lookback_n=lookback_n,
    lookback_start_offset=0,
    enable_sha1=enable_sha1,
    enable_sha2=enable_sha2,
    enable_dan1=enable_dan1,
    enable_dan2=enable_dan2,
    enable_dingwei_sha=enable_dingwei_sha,
    enable_dingwei_sha2=enable_dingwei_sha2,
    enable_dingwei_sha3=enable_dingwei_sha3,
    enable_dingwei_dan1=enable_dingwei_dan1,
    skip_if_few_sha1=skip_if_few_sha1,
    skip_if_few_sha2=skip_if_few_sha2,
    skip_if_few_dan1=skip_if_few_dan1,
    skip_if_few_dan2=skip_if_few_dan2,
    skip_if_few_dingwei_sha=skip_if_few_dingwei_sha,
    skip_if_few_dingwei_sha2=skip_if_few_dingwei_sha2,
    skip_if_few_dingwei_sha3=skip_if_few_dingwei_sha3,
    resolve_tie_mode_sha1=resolve_tie_mode_sha1,
    resolve_tie_mode_sha2=resolve_tie_mode_sha2,
    resolve_tie_mode_dan1=resolve_tie_mode_dan1,
    resolve_tie_mode_dan2=resolve_tie_mode_dan2,
    resolve_tie_mode_dingwei_sha=resolve_tie_mode_dingwei_sha,
    resolve_tie_mode_dingwei_sha2=resolve_tie_mode_dingwei_sha2,
    resolve_tie_mode_dingwei_sha3=resolve_tie_mode_dingwei_sha3,
    resolve_tie_mode_dingwei_dan1=resolve_tie_mode_dingwei_dan1,
    reverse_on_tie_dingwei_sha=reverse_on_tie_dingwei_sha,
    reverse_on_tie_dingwei_sha2=reverse_on_tie_dingwei_sha2,
    reverse_on_tie_dingwei_sha3=reverse_on_tie_dingwei_sha3,
    reverse_on_tie_dingwei_dan1=reverse_on_tie_dingwei_dan1,
)
print(f"DEBUG: ALL_MODE_LIMIT={os.getenv('ALL_MODE_LIMIT')}, parsed={all_mode_limit}, type={type(all_mode_limit)}")
assert (all_mode_limit is None or isinstance(all_mode_limit, int)), f"all_mode_limit 类型不对: {all_mode_limit}, type={type(all_mode_limit)}"

run_hit_analysis_batch(
    conn=conn,
    lottery_name=lottery_name,
    query_issues=query_issues,
    all_mode_limit=all_mode_limit,
    enable_hit_check=enable_hit_check,
    enable_track_open_rank=enable_track_open_rank,
    dingwei_sha_pos=dingwei_sha_pos,
    check_mode=check_mode,
    analysis_kwargs=analysis_kwargs
)

save_log_file_if_needed(log_save_mode)

import time; time.sleep(1)

import re
import glob
import requests

# ==== 1. 自动定位最新日志文件 ====
log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "log"))
log_pattern = os.path.join(log_dir, "run_3d_*.log")
log_files = glob.glob(log_pattern)
if not log_files:
    print("❌ 未找到任何日志文件，无法推送企业微信")
    exit(1)

latest_log = max(log_files, key=os.path.getmtime)
print(f"✅ 找到最新日志文件: {latest_log}")

with open(latest_log, "r", encoding="utf-8") as f:
    log_text = f.read()

# ==== 2. 结构化提取关键信息 ====
lottery = re.search(r"✅ 彩票类型: (.+)", log_text)
periods = re.findall(r"🎯 查询期号: \d+", log_text)
back_playtype = re.search(r"✅ 回溯玩法: (.+)", log_text)
analyze_playtype = re.search(r"✅ 分析玩法: (.+)", log_text)
hit_rate = re.search(r"✅ 命中率：(.+)", log_text)
miss_info = re.search(r"📉 共 (\d+) 期，未命中次数：(\d+) 期，跳过 (\d+) 期", log_text)
rank_stats = re.findall(r"- 排名第 (\d+) 位：(\d+) 次", log_text)
not_hit_ranks = re.search(r"- 未命中排名位：([0-9,]+)", log_text)

# ==== 3. 组装企业微信内容 ====
msg = []
run_number = os.getenv("GITHUB_RUN_NUMBER")
if run_number:
    msg.append(f"🎰 {lottery.group(1)}-策略分析")
msg.append(f"【Actions 运行编号:#{run_number}】\n")
period_list = [int(re.search(r"\d+", p).group()) for p in periods]
if period_list:
    min_issue = min(period_list)
    max_issue = max(period_list)
    msg.append(f"📅 分析期号范围: {max_issue}-{min_issue}")
msg.append(f"📅 分析期数: {len(periods)}")

if back_playtype: msg.append(f"✅ 回溯玩法: {back_playtype.group(1)}")
if analyze_playtype: msg.append(f"✅ 分析玩法: {analyze_playtype.group(1)}")

msg.append(f"启用定位杀号位置: {analysis_kwargs.get('enable_dingwei_sha', '未启用')}")
msg.append(f"启用定位定胆: {analysis_kwargs.get('enable_dingwei_dan1')}")
msg.append(f"遇到频次并列时: {analysis_kwargs.get('resolve_tie_mode_dingwei_sha', '未设置')}")
msg.append(f"跳过推荐不足: {'启用' if analysis_kwargs.get('skip_if_few_dingwei_sha') else '未启用'}")
msg.append("=============")
msg.append("分析参数配置")
msg.append(f"分析模式: {analysis_kwargs.get('mode', '')}")
msg.append(f"回溯期数: {analysis_kwargs.get('lookback_n', '')}")
msg.append(f"回溯偏移: {analysis_kwargs.get('lookback_start_offset', '')}")
msg.append(f"定位杀号位: {dingwei_sha_pos if dingwei_sha_pos is not None else 'None'}")
msg.append(f"杀号判断模式: {'定位位判断' if check_mode=='dingwei' else '全位判断'}")
for k in ['enable_sha1', 'enable_sha2', 'enable_dan1', 'enable_dan2', 'enable_dingwei_sha', 'enable_dingwei_sha2', 'enable_dingwei_sha3', 'enable_dingwei_dan1']:
    if analysis_kwargs.get(k):
        msg.append(f"策略类型: {k}")
        msg.append(f"取值配置: {analysis_kwargs.get(k)}")
msg.append(f"🎯 命中次数筛选命中值: {analysis_kwargs.get('hit_rank_list', '')}")
msg.append(f"📈 命中排名筛选：{analysis_kwargs.get('hit_rank_list', '')}")
if miss_info:
    total_periods, miss_count, skip_count = miss_info.groups()
    msg.append(f"📉 共 {total_periods} 期，未命中次数：{miss_count} 期，跳过 {skip_count} 期")
if hit_rate: msg.append(f"✅ 命中率：{hit_rate.group(1)}")
msg.append("📊 开奖号码在推荐数字频次排序中的排名：")
if not_hit_ranks:
    msg.append(f"   - 未命中排名位：{not_hit_ranks.group(1)}")
for rank, times in rank_stats:
    msg.append(f"   - 排名第 {rank} 位：{times} 次")

msg_text = "\n".join(msg)

# ===== 发送到企业微信（自动分段） =====
wechat_api_url = os.getenv("WECHAT_API_URL")
MAX_LEN = 1800  # 单条消息最大字符数

def send_wechat_message(msg):
    payload = {"content": msg}
    headers = {"x-api-key": os.getenv("WECHAT_API_KEY")}
    try:
        resp = requests.post(wechat_api_url, json=payload, headers=headers, timeout=10)
        print(f"✅ 企业微信推送状态: {resp.status_code}")
        print(f"✅ 企业微信响应: {resp.text}")
    except Exception as e:
        print(f"❌ 企业微信消息推送失败: {e}")

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