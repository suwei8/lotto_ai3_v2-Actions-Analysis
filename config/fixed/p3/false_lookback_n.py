import os
import re

def comment_lookback_n_in_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    changed = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        # 匹配含 LOOKBACK_N: 的行（不管是否注释）
        if re.match(r'^#?\s*LOOKBACK_N\s*:', stripped):
            # 不重复加注释
            if not stripped.startswith("#"):
                idx = line.find("LOOKBACK_N")
                new_line = line[:idx] + "#" + line[idx:]
                new_lines.append(new_line)
                changed = True
            else:
                new_lines.append(line)
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
                comment_lookback_n_in_file(full_path)

if __name__ == "__main__":
    main()
