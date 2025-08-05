import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd
from collections import Counter
from functools import reduce
from dotenv import load_dotenv
from utils.db import get_connection


# 导入企业微信发送模块
import requests

load_dotenv()
conn = get_connection()

# ========== 参数 ==========
ENABLE_BACKTEST = os.getenv("ENABLE_BACKTEST", "false").lower() == "true"
BACKTEST_NUM = os.getenv("BACKTEST_NUM", "10")
OFFSET = int(os.getenv("OFFSET", 1))
POSITION = int(os.getenv("POSITION", 0))  # 百位=0，十位=1，个位=2
LOTTERY_NAME = os.getenv("LOTTERY_NAME", "福彩3D")
PLAYTYPE_LIST = ["百位定3"]
RUN_NUMBER = os.getenv("GITHUB_RUN_NUMBER", "N/A")
# ========== 企业微信发送函数 ==========
def send_wechat_msg(msg):
    wechat_api_url = os.getenv("WECHAT_API_URL")
    wechat_api_key = os.getenv("WECHAT_API_KEY")
    if not wechat_api_url or not wechat_api_key:
        print("❌ 未配置企业微信发送参数，跳过发送")
        return
    payload = {"content": msg}
    headers = {"x-api-key": wechat_api_key}
    try:
        resp = requests.post(wechat_api_url, json=payload, headers=headers, timeout=10)
        print(f"✅ 企业微信推送状态: {resp.status_code}")
        print(f"✅ 企业微信响应: {resp.text}")
    except Exception as e:
        print(f"❌ 企业微信消息推送失败: {e}")

# ========== 工具函数 ==========
def get_open_code(conn, issue):
    sql = "SELECT open_code FROM lottery_results_3d WHERE issue_name = %s"
    df = pd.read_sql(sql, conn, params=(issue,))
    if df.empty:
        return []
    return df.iloc[0]["open_code"].split(",")

def get_rank(conn, issue, playtype):
    sql = """
        SELECT numbers FROM expert_predictions_3d
        WHERE issue_name = %s AND playtype_name = %s
    """
    df = pd.read_sql(sql, conn, params=(issue, playtype))
    counter = Counter()
    for nums in df["numbers"]:
        for n in nums.split(","):
            n = n.strip()
            if n.isdigit():
                counter[n] += 1
    return [num for num, _ in counter.most_common()], counter

def print_rank(rank, counter):
    for num in rank:
        print(f"数字 {num}: 出现 {counter[num]} 次")

# ========== 获取回测期号 ==========
if ENABLE_BACKTEST:
    sql = "SELECT DISTINCT issue_name FROM expert_predictions_3d ORDER BY issue_name DESC"
    issue_df = pd.read_sql(sql, conn)
    issue_list = issue_df["issue_name"].tolist()
    if BACKTEST_NUM.upper() == "ALL":
        backtest_issues = issue_list
    else:
        backtest_issues = issue_list[:int(BACKTEST_NUM)]
else:
    curr_issue = os.getenv("CURR_ISSUE", "2025190")
    backtest_issues = [curr_issue]

# ========== 回测计数器 ==========
success_count = 0
fail_count = 0
skip_count = 0

# ========== 主流程 ==========
for curr_issue in backtest_issues:
    prev_issue = str(int(curr_issue) - 1)
    print("\n" + "="*40)
    print(f"🎯 当前期号: {curr_issue}，上一期号: {prev_issue}")
    curr_open = get_open_code(conn, curr_issue)
    prev_open = get_open_code(conn, prev_issue)

    if not curr_open or not prev_open:
        print("⚠️ 当前期或上一期开奖号码缺失，跳过")
        skip_count += 1
        continue

    print(f"🎯 当前期开奖号码: {','.join(curr_open)}")
    print(f"🎯 上一期开奖号码: {','.join(prev_open)}")

    filtered_sets = []

    for playtype_name in PLAYTYPE_LIST:
        print(f"\n🎯 分析玩法：{playtype_name}")
        curr_rank, curr_counter = get_rank(conn, curr_issue, playtype_name)
        prev_rank, prev_counter = get_rank(conn, prev_issue, playtype_name)

        print(f"📊 当前期排行榜:")
        print_rank(curr_rank, curr_counter)
        print(f"\n📊 上一期排行榜:")
        print_rank(prev_rank, prev_counter)

        if POSITION >= len(prev_open):
            print(f"❌ 上期开奖号不足以判断第 {POSITION} 位")
            filtered_rank = curr_rank
        else:
            prev_digit = prev_open[POSITION]
            if prev_digit not in prev_rank:
                print(f"✅ 上期开奖号码第 {POSITION} 位数字 {prev_digit} 不在排行榜中，无需排除")
                filtered_rank = curr_rank
            else:
                hit_index = prev_rank.index(prev_digit)
                print(f"🔥 上期开奖号第 {POSITION} 位为 {prev_digit}，在排行榜中位置：第 {hit_index+1} 名")
                target_index = hit_index + OFFSET
                if target_index >= len(curr_rank):
                    print(f"⚠️ 当前排行榜长度不足，无法排除偏移位置：第 {target_index+1} 名")
                    filtered_rank = curr_rank
                else:
                    to_remove = curr_rank[target_index]
                    print(f"❌ 排除本期排行榜第 {target_index+1} 名数字：{to_remove}")
                    filtered_rank = [n for i, n in enumerate(curr_rank) if i != target_index]

        print(f"✅ 排除后排行榜: {''.join(filtered_rank)}")
        filtered_sets.append(set(filtered_rank))

    if not filtered_sets:
        print("❌ 没有可用的排行榜结果，跳过")
        skip_count += 1
        continue

    final_set = sorted(reduce(set.intersection, filtered_sets), key=lambda x: int(x))
    print("\n🎯 最终排除后结果:")
    print(f"✅ 最终排除后结果（{len(final_set)}个）:")
    print("".join(final_set))

    if POSITION >= len(curr_open):
        print("⚠️ 当前开奖号码不足，无法判断杀号成功与否")
        skip_count += 1
        continue

    target_digit = curr_open[POSITION]
    if target_digit in final_set:
        print(f"✅ 杀号成功：开奖号码 {target_digit} 仍在最终结果中")
        success_count += 1
    else:
        print(f"❌ 杀号失败：开奖号码 {target_digit} 被错误排除")
        fail_count += 1

# ========== 回测统计输出 ==========
if ENABLE_BACKTEST:
    total = success_count + fail_count
    print("\n==============================")
    print("📊 回测统计结果：")
    print(f"✅ 杀号成功期数：{success_count}")
    print(f"❌ 杀号失败期数：{fail_count}")
    print(f"📉 跳过期数：{skip_count}")
    print(f"🎯 成功率：{success_count}/{total} = {success_count/total:.2%}" if total else "⚠️ 无有效回测数据")

    if total:
        first_issue = backtest_issues[-1]
        last_issue = backtest_issues[0]
        msg = f"""📊 上期杀本期1码（Run #{RUN_NUMBER}）
        回测统计结果：
        分析玩法：{PLAYTYPE_LIST[0]}
        期号范围: {last_issue} ~ {first_issue}
        ✅ 杀号成功期数：{success_count}
        ❌ 杀号失败期数：{fail_count}
        📉 跳过期数：{skip_count}
        🎯 成功率：{success_count}/{total} = {success_count/total:.2%}"""
        send_wechat_msg(msg)
