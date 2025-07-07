import os
import yaml
import re
import glob
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOG_FILES = sorted(
    glob.glob(os.path.join(PROJECT_ROOT, "logs", "*_analyze*.txt"))
)

if not LOG_FILES:
    raise FileNotFoundError(f"❌ 没有找到任何日志文件: {os.path.join(PROJECT_ROOT, 'logs')}")
print(f"✅ 当前找到日志文件: {LOG_FILES}")

# 动态收集所有 config/fixed/3d/**/ 下的 YAML
test_files = []
for subdir in ["baiwei", "gewei", "shiwei"]:
    folder = os.path.join(PROJECT_ROOT, f"config/fixed/3d/{subdir}")
    if os.path.exists(folder):
        for name in os.listdir(folder):
            if name.endswith(".yaml") and name != "base.yaml":
                test_files.append(f"config/fixed/3d/{subdir}/{name}")

print("===== ✅ 当前 ENABLE_DINGWEI_SHA 初始值 =====")
for f in test_files:
    abs_f = os.path.join(PROJECT_ROOT, f)
    if os.path.exists(abs_f):
        with open(abs_f, encoding="utf-8") as fp:
            cfg = yaml.safe_load(fp)
            print(f"{f}: {cfg.get('ENABLE_DINGWEI_SHA')}")
print("===========================================")

print("\n===== 🔍 日志中找出与本地配置一致的【首个】完整命中统计块 =====")
for yaml_file in test_files:
    found = False
    yaml_path_part = "/".join(yaml_file.replace("\\", "/").split("/"))
    for log_file in LOG_FILES:
        with open(log_file, encoding="utf-8") as f:
            content = f.read()
            pattern = rf"🚀 Running config: ([^\n]+)"
            matches = re.finditer(pattern, content)
            for match in matches:
                path_line = match.group(1)
                if yaml_path_part in path_line:
                    start = match.end()
                    after_path = content[start:]
                    block_pattern = r"📉 共[^\n]*[\s\S]*?(?=📄 日志已保存至|$)"
                    block_match = re.search(block_pattern, after_path)
                    if block_match:
                        block = block_match.group(0)
                        print(f"\n=== 本地文件: {yaml_file}")
                        print(f"=== 日志路径: {path_line.strip()}")
                        print("--- 命中统计块 ---")
                        print(block.strip())
                        if "未命中次数：0" not in block:
                            lines = block.split("\n")
                            parsed = []
                            first_not_hit = None
                            for line in lines:
                                if "未命中排名位" in line:
                                    m2 = re.search(r"未命中排名位：([0-9]+)", line)
                                    if m2:
                                        first_not_hit = int(m2.group(1))
                                m = re.search(r"- 排名第 ([0-9]+) 位：([0-9]+) 次", line.strip())
                                if m:
                                    parsed.append((int(m.group(1)), int(m.group(2))))
                            print(f"DEBUG: parsed={parsed}")
                            if first_not_hit:
                                min_rank = first_not_hit
                                print(f"➡️ 用未命中排名位首值: ENABLE_DINGWEI_SHA: [{min_rank}]")
                            else:
                                parsed.sort(key=lambda x: x[1])
                                min_rank = parsed[0][0]
                                print(f"➡️ 最终准备写入: ENABLE_DINGWEI_SHA: [{min_rank}]")

                            abs_f = os.path.join(PROJECT_ROOT, yaml_file)
                            with open(abs_f, "r", encoding="utf-8") as fp:
                                lines = fp.readlines()
                            with open(abs_f, "w", encoding="utf-8") as fp:
                                for line in lines:
                                    if line.strip().startswith("ENABLE_DINGWEI_SHA"):
                                        fp.write(f"ENABLE_DINGWEI_SHA: [{min_rank}]\n")
                                    else:
                                        fp.write(line)
                            print(f"✅ 已仅更新: ENABLE_DINGWEI_SHA -> [{min_rank}] in {yaml_file}")
                        else:
                            print("\n无需更新，未命中次数=0")
                        found = True
                    break
            if found:
                break
    if not found:
        print(f"⚠️ {yaml_file} 未找到匹配")
print("===========================================")

# 新增：汇总各 YAML 的命中率
yaml_hit_stats = []

print("\n===== 📊 汇总各 YAML 命中率排行 =====")

for yaml_file in test_files:
    found = False
    yaml_path_part = "/".join(yaml_file.replace("\\", "/").split("/"))
    for log_file in LOG_FILES:
        with open(log_file, encoding="utf-8") as f:
            content = f.read()
            pattern = rf"🚀 Running config: ([^\n]+)"
            matches = re.finditer(pattern, content)
            for match in matches:
                path_line = match.group(1)
                if yaml_path_part in path_line:
                    start = match.end()
                    after_path = content[start:]
                    block_pattern = r"📉 共[^\n]*[\s\S]*?(?=📄 日志已保存至|$)"
                    block_match = re.search(block_pattern, after_path)
                    if block_match:
                        block = block_match.group(0)
                        total_match = re.search(r"📉 共 ?([0-9]+) 期", block)
                        miss_match = re.search(r"未命中次数：([0-9]+)", block)
                        if total_match and miss_match:
                            total = int(total_match.group(1))
                            miss = int(miss_match.group(1))
                            hit = total - miss
                            hit_rate = hit / total if total > 0 else 0
                            yaml_hit_stats.append((yaml_file, hit_rate, hit, miss, total))
                        found = True
                    break
            if found:
                break
    if not found:
        yaml_hit_stats.append((yaml_file, 0, 0, 0, 0))

# 排序：命中率从高到低
yaml_hit_stats.sort(key=lambda x: x[1], reverse=True)

print("\n=== 📈 命中率排行（高 → 低） ===")
for path, rate, hit, miss, total in yaml_hit_stats:
    rate_percent = f"{rate*100:.2f}%" if total > 0 else "N/A"
    print(f"{path} -> 命中率: {rate_percent} ({hit}/{total}，未命中:{miss})")

print("===========================================")
