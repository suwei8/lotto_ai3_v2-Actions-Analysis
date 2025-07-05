import os
import re

def uncomment_lookback_n_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    changed = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        # 匹配 #LOOKBACK_N: 开头
        if re.match(r'^#\s*LOOKBACK_N\s*:', stripped):
            idx = line.find("#")
            new_line = line[:idx] + line[idx + 1:]
            new_lines.append(new_line)
            changed = True
        else:
            new_lines.append(line)

    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"✅ 已处理: {filepath}")

def main():
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".yaml") and file != "base.yaml":
                full_path = os.path.join(root, file)
                uncomment_lookback_n_in_file(full_path)

if __name__ == "__main__":
    main()
