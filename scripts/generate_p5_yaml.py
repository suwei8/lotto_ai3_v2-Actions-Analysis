import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
import pandas as pd
from utils.db import get_connection
from utils.expert_hit_analysis import run_hit_analysis_batch
from utils.logger import init_log_capture

# ✅ 位置映射
pos_map = {"万位": 0, "千位": 1, "百位": 2, "十位": 3, "个位": 4}

# ✅ position 英文到中文映射
POSITION_WORD_MAP = {
    'wanwei': '万位',
    'qianwei': '千位',
    'baiwei': '百位',
    'shiwei': '十位',
    'gewei': '个位'
}

def get_position_idx(playtype_name):
    for pos in pos_map:
        if pos in playtype_name:
            return pos_map[pos]
    return None

def get_playtypes_from_hit_stat(conn):
    sql = "SELECT DISTINCT playtype_name FROM expert_hit_stat_p5 WHERE hit_count > 0"
    df = pd.read_sql(sql, conn)
    return sorted(df['playtype_name'].dropna().unique())

def get_hit_rank_list_from_stat(conn, playtype_name):
    sql = f"SELECT MAX(hit_count) as max_hit FROM expert_hit_stat_p5 WHERE playtype_name = '{playtype_name}'"
    df = pd.read_sql(sql, conn)
    max_hit = df['max_hit'].iloc[0] or 1
    if max_hit >= 5:
        return [[1], [1,2], [1,2,3], [1,2,3,4]]
    elif max_hit >= 3:
        return [[1], [1,2], [1,2,3]]
    else:
        return [[1]]

def get_lookback_n_from_stat(conn):
    sql = "SELECT COUNT(DISTINCT issue_name) AS total_issues FROM expert_hit_stat_p5"
    df = pd.read_sql(sql, conn)
    total_issues = df['total_issues'].iloc[0] or 30
    base = []
    if total_issues >= 30:
        base.append(30)
    if total_issues >= 50:
        base.append(50)
    if total_issues >= 100:
        base.append(100)
    return [None] + base

def is_better(new, old):
    if not old:
        return True
    if new.get("命中率", 0) > old.get("命中率", 0):
        return True
    if new.get("命中率", 0) == old.get("命中率", 0) and new.get("跳过期数", 999) < old.get("跳过期数", 999):
        return True
    return False

def save_yaml(playtype_name, pos, lookback, hit_rank_list, enable_sha):
    config = {
        "DINGWEI_SHA_POS": pos,
        "QUERY_PLAYTYPE_NAME": playtype_name,
        "ANALYZE_PLAYTYPE_NAME": playtype_name,
        "LOOKBACK_N": lookback,
        "HIT_RANK_LIST": hit_rank_list,
        "ENABLE_DINGWEI_SHA": enable_sha
    }
    base_dir = f"config/fixed/p5/{playtype_name}"
    os.makedirs(base_dir, exist_ok=True)
    file_path = os.path.join(base_dir, f"sha_{pos}.yaml")
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True)
    print(f"✅ 已生成: {file_path}")

def main():
    # ✅ 解析 position 参数
    position_arg = None
    if len(sys.argv) > 1:
        position_arg = sys.argv[1]
    print(f"📝 Debug: 当前 position_arg = {position_arg}")

    init_log_capture("generate_p5_yaml.py", lottery_name="p5")
    conn = get_connection()
    playtype_names = get_playtypes_from_hit_stat(conn)
    lookback_n_list = get_lookback_n_from_stat(conn)

    print(f"🗂️ 查到玩法: {playtype_names}")

    if not playtype_names:
        print("❌ 未找到任何可用的 playtype_name")
        return

    for playtype_name in playtype_names:
        # ✅ 如果指定了 position，就只保留匹配的
        if position_arg and position_arg != 'all':
            expect_word = POSITION_WORD_MAP.get(position_arg)
            if expect_word not in playtype_name:
                continue

        pos_idx = get_position_idx(playtype_name)
        if pos_idx is None:
            print(f"⚠️ 未识别位置: {playtype_name}")
            continue

        hit_rank_list_options = get_hit_rank_list_from_stat(conn, playtype_name)
        ENABLE_DINGWEI_SHA_CANDIDATES = [[5], [8], [10], [12], [15]]

        for lookback in lookback_n_list:
            for hit_rank in hit_rank_list_options:
                best_result = None
                best_enable_sha = None
                for enable_sha in ENABLE_DINGWEI_SHA_CANDIDATES:
                    result = run_hit_analysis_batch(
                        conn,
                        lottery_name="排列5",
                        query_issues=["All"] if lookback is None else [],
                        enable_hit_check=True,
                        enable_track_open_rank=False,
                        dingwei_sha_pos=pos_idx,
                        check_mode="dingwei",
                        analysis_kwargs={
                            "query_playtype_name": playtype_name,
                            "analyze_playtype_name": playtype_name,
                            "hit_rank_list": hit_rank,
                            "lookback_n": lookback,
                            "enable_dingwei_sha": enable_sha
                        }
                    )
                    if result is not None:
                        hit_count = result.get("命中率", 0)
                        skip_count = result.get("跳过期数", 0)
                        # 模拟：直接用 is_better 逻辑
                        score_obj = {"命中率": hit_count, "跳过期数": skip_count}
                        if is_better(score_obj, best_result):
                            best_result = score_obj
                            best_enable_sha = enable_sha

                if best_result:
                    save_yaml(playtype_name, pos_idx, lookback, hit_rank, best_enable_sha)
    conn.close()

if __name__ == "__main__":
    main()
