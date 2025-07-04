import os

def generate_structure(path, indent=0):
    """
    递归生成文件夹结构字符串，indent 控制缩进的深度
    """
    structure = ""

    # 如果是目录，且不是需要排除的文件夹
    if os.path.isdir(path):
        # 排除 .idea、.venv 和 .git 目录
        if os.path.basename(path) in {'.idea', '.venv', '.git'}:
            return ""

        # 获取目录下的文件和文件夹列表
        items = sorted(os.listdir(path))
        for item in items:
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                # 为文件夹添加目录结构并递归
                structure += "│ " + " " * (indent - 1) + "├── " + item + "/\n"
                structure += generate_structure(item_path, indent + 4)
            else:
                # 为文件添加目录结构
                structure += "│ " + " " * (indent - 1) + "├── " + item + "\n"
    return structure

def write_project_structure_to_file():
    # 当前目录的路径
    current_dir = os.getcwd()

    # 生成目录结构
    structure = generate_structure(current_dir)

    # 输出到文件，使用 UTF-8 编码
    with open("Project Structure.txt", "w", encoding="utf-8") as f:
        f.write(f"{current_dir}/\n")
        f.write(structure)
        print("Project structure has been written to 'Project Structure.txt'.")

if __name__ == "__main__":
    write_project_structure_to_file()