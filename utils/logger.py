import os
import builtins
from datetime import datetime

# ✅ 确保原始 print 函数存在
if "__print_original__" not in builtins.__dict__:
    builtins.__dict__["__print_original__"] = builtins.print

# ✅ 日志缓存
_log_buffer = []
_current_log_file_path = None


def log(*args, sep=" ", end="\n", **kwargs):
    """
    替代 print 的日志函数：输出到控制台，同时写入缓存。
    自动兼容 print(file=...)、flush=... 等额外参数。
    """
    msg = sep.join(map(str, args)) + end
    _log_buffer.append(msg)
    builtins.__dict__["__print_original__"](*args, sep=sep, end=end, **kwargs)


def init_log_capture(script_name_hint=None):
    """
    初始化日志捕获，重定向 print，并记录日志文件路径
    """
    global _current_log_file_path
    if script_name_hint is None:
        script_name_hint = "unnamed_script"

    # 固定日志保存路径为项目根目录的 /log 目录
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    log_dir = os.path.join(project_root, "log")
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(script_name_hint)[0]
    _current_log_file_path = os.path.join(log_dir, f"{base_name}_{timestamp}.log")
    builtins._current_log_file_path = _current_log_file_path  # 👈 就是这行！
    _log_buffer.clear()

    # ✅ 日志头部加入脚本路径提示
    script_path_hint = f"📁 当前脚本路径: scripts/{script_name_hint}"
    _log_buffer.append(script_path_hint + "\n")
    builtins.__dict__["__print_original__"](script_path_hint + "\n")

    # ✅ 替换 print 函数为 log
    builtins.print = log


def save_log_file_if_needed(log_save_mode, script_name_hint="unnamed_script"):
    """
    根据 log_save_mode 决定是否保存日志文件
    :param log_save_mode: False / "All"
    """
    if not log_save_mode or not _log_buffer or not _current_log_file_path:
        return

    try:
        with open(_current_log_file_path, "w", encoding="utf-8") as f:
            f.writelines(_log_buffer)
        builtins.__dict__["__print_original__"](
            f"📄 日志已保存至: {_current_log_file_path}\n"
        )
    except Exception as e:
        builtins.__dict__["__print_original__"](
            f"❌ 日志保存失败: {e}\n"
        )
