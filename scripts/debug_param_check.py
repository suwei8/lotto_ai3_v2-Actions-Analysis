import os
import sys
import yaml
import json

# robust int 解析
def parse_int_env(key, default=None):
    val = os.getenv(key)
    if val is None or str(val).strip() == "" or str(val).lower() == "none":
        return None if default in (None, "None", "") else default
    try:
        return int(val)
    except Exception:
        return None if default in (None, "None", "") else default

# robust json解析
def safe_json_load(env_key, default):
    val = os.getenv(env_key)
    if val is None or val.strip() == "":
        return default
    try:
        return json.loads(val)
    except Exception:
        print(f"❌ 解析环境变量 {env_key} 失败，使用默认值: {default}")
        return default

# === 加载 config ===
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
yaml_path = os.path.join(base_dir, "config", "p5_config.yaml")
with open(yaml_path, encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)["DEFAULTS"]

_config_limit = CONFIG.get("ALL_MODE_LIMIT", None)
if _config_limit in ("None", ""):
    _config_limit = None
all_mode_limit = parse_int_env("ALL_MODE_LIMIT", _config_limit)

check_mode = os.getenv("CHECK_MODE") or CONFIG["CHECK_MODE"] if "CHECK_MODE" in CONFIG else "dingwei"
lottery_name = os.getenv("LOTTERY_NAME") or CONFIG["LOTTERY_NAME"]
analysis_mode = os.getenv("ANALYSIS_MODE") or CONFIG.get("ANALYSIS_MODE", "rank")
dingwei_sha_pos = parse_int_env("DINGWEI_SHA_POS", 0)
lookback_n = parse_int_env("LOOKBACK_N", 0)
enable_hit_check = str(os.getenv("ENABLE_HIT_CHECK") or CONFIG.get("ENABLE_HIT_CHECK", True)).lower() == "true"

query_issues_str = os.getenv("QUERY_ISSUES") or CONFIG.get("QUERY_ISSUES", "All")
if query_issues_str == "None":
    query_issues = [None]
elif query_issues_str == "All":
    query_issues = ["All"]
elif "," in query_issues_str:
    query_issues = query_issues_str.split(",")
else:
    query_issues = [query_issues_str]

query_playtype_name = os.getenv("QUERY_PLAYTYPE_NAME", "百位定1")
analyze_playtype_name = os.getenv("ANALYZE_PLAYTYPE_NAME", "百位定1")
hit_rank_list = safe_json_load("HIT_RANK_LIST", [1])
hit_count_conditions = safe_json_load("HIT_COUNT_CONDITIONS", {})

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
enable_dingwei_dan1 = os.getenv("ENABLE_DINGWEI_DAN1", "False").lower() == "true"

# ======== 打印所有核心参数和类型 =========
print("\n====== 配置参数检查模式 ======")
print(f"✅ CHECK_MODE: {check_mode} ({type(check_mode)})")
print(f"✅ LOTTERY_NAME: {lottery_name} ({type(lottery_name)})")
print(f"✅ analysis_mode: {analysis_mode} ({type(analysis_mode)})")
print(f"✅ all_mode_limit: {all_mode_limit} ({type(all_mode_limit)})")
print(f"✅ dingwei_sha_pos: {dingwei_sha_pos} ({type(dingwei_sha_pos)})")
print(f"✅ lookback_n: {lookback_n} ({type(lookback_n)})")
print(f"✅ enable_hit_check: {enable_hit_check} ({type(enable_hit_check)})")
print(f"✅ query_issues: {query_issues} ({type(query_issues)})")
print(f"✅ query_playtype_name: {query_playtype_name} ({type(query_playtype_name)})")
print(f"✅ analyze_playtype_name: {analyze_playtype_name} ({type(analyze_playtype_name)})")
print(f"✅ hit_rank_list: {hit_rank_list} ({type(hit_rank_list)})")
print(f"✅ hit_count_conditions: {hit_count_conditions} ({type(hit_count_conditions)})")
print(f"✅ enable_sha1: {enable_sha1} ({type(enable_sha1)})")
print(f"✅ enable_dingwei_sha: {enable_dingwei_sha} ({type(enable_dingwei_sha)})")
print("====== analysis_kwargs 参数预览 ======")
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
)
print(json.dumps(analysis_kwargs, ensure_ascii=False, indent=2))
print("====== 参数检查完成，未执行任何数据库分析 ======\n")

import platform
import multiprocessing
import psutil

print("====== 虚拟机硬件环境信息 ======")
print(f"操作系统: {platform.system()} {platform.release()}")
print(f"CPU 架构: {platform.machine()}")
print(f"CPU 核心数: {multiprocessing.cpu_count()}")
print(f"内存总量: {round(psutil.virtual_memory().total / 1024 / 1024 / 1024, 2)} GB")
print(f"可用内存: {round(psutil.virtual_memory().available / 1024 / 1024 / 1024, 2)} GB")
print(f"Python 版本: {platform.python_version()}")
print("======")
