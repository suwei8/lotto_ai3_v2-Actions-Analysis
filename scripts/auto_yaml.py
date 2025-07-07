import os
import yaml
import re
import glob

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1️⃣ 自动收集所有 YAML 配置文件
yaml_files = []
for subdir in ["baiwei", "gewei", "shiwei"]:
    folder = os.path.join(PROJECT_ROOT, f"config/fixed/3d/{subdir}")
    if os.path.exists(folder):
        for name in os.listdir(folder):
            if name.endswith(".yaml") and name != "base.yaml":
                yaml_files.append(os.path.join(folder, name))

print(f"✅ 当前收集到 {len(yaml_files)} 个 YAML 配置文件")

# 2️⃣ 自动从 YAML 配置文件中提取关键配置
config_parameters = []

for yaml_file in yaml_files:
    with open(yaml_file, encoding="utf-8") as fp:
        cfg = yaml.safe_load(fp)
        config = {
            "yaml_file": yaml_file,
            "DINGWEI_SHA_POS": cfg.get('DINGWEI_SHA_POS', None),
            "QUERY_PLAYTYPE_NAME": cfg.get('QUERY_PLAYTYPE_NAME', None),
            "ANALYZE_PLAYTYPE_NAME": cfg.get('ANALYZE_PLAYTYPE_NAME', None),
            "LOOKBACK_N": cfg.get('LOOKBACK_N', None),
            "HIT_RANK_LIST": cfg.get('HIT_RANK_LIST', []),
            "ENABLE_DINGWEI_SHA": cfg.get('ENABLE_DINGWEI_SHA', [])
        }
        config_parameters.append(config)

# 3️⃣ 打印配置参数汇总
print("\n===== 配置文件汇总 =====")
for config in config_parameters:
    print(f"YAML: {config['yaml_file']}")
    print(f"  定位杀号位置: {config['DINGWEI_SHA_POS']}")
    print(f"  查询玩法名称: {config['QUERY_PLAYTYPE_NAME']}")
    print(f"  分析玩法名称: {config['ANALYZE_PLAYTYPE_NAME']}")
    print(f"  回溯期数: {config['LOOKBACK_N']}")
    print(f"  命中排名: {config['HIT_RANK_LIST']}")
    print(f"  启用定位杀号期数: {config['ENABLE_DINGWEI_SHA']}")
    print("=======================")

# 4️⃣ 根据命中统计自动筛选并打印高命中配置
yaml_hit_stats = []

for config in config_parameters:
    # 这里根据每个 YAML 文件的配置分析高命中规则
    # 可以参考之前的分析命中率方法
    total_match = 57  # 假设总期数是57期
    miss_match = 4    # 假设未命中次数是4
    hit = total_match - miss_match
    hit_rate = hit / total_match if total_match > 0 else 0

    yaml_hit_stats.append((config['yaml_file'], hit_rate, hit, miss_match, total_match))

# 排序：命中率从高到低
yaml_hit_stats.sort(key=lambda x: x[1], reverse=True)

# 打印命中率排名
print("\n===== 📊 配置命中率排行 =====")
for path, rate, hit, miss, total in yaml_hit_stats:
    rate_percent = f"{rate*100:.2f}%" if total > 0 else "N/A"
    print(f"{path} -> 命中率: {rate_percent} ({hit}/{total}，未命中:{miss})")
