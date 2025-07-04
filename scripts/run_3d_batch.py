# scripts/run_3d_batch.py
import subprocess
import os
import glob

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_PYTHON = os.path.join(PROJECT_ROOT, '.venv', 'Scripts', 'python.exe')

CONFIGS = sorted(glob.glob(os.path.join(PROJECT_ROOT, "config/3d/fixed_*.yaml")))

print(f"✅ 扫描到 {len(CONFIGS)} 个固定策略配置：")
for c in CONFIGS:
    print(f" - {c}")

outputs = []

for config in CONFIGS:
    print(f"\n🚀 Running config: {config}")
    env = os.environ.copy()
    env["STRATEGY_CONFIG_PATH"] = config
    print(env["STRATEGY_CONFIG_PATH"])

    process = subprocess.Popen(
        [VENV_PYTHON, "scripts/run_3d.py"],
        env=env,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8"
    )
    out, _ = process.communicate()

    print(out)  # ⏪ 立刻输出，保证看得到
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
