# 调用页面:pages_scripts/3D/dan_expert_hit_analysis/baiwei-ding5_ding5-1.py
# 该脚本用于分析福彩3D中“百位定1”玩法在指定期号范围内的专家推荐表现，并提取定位杀号推荐数字。
import os
import builtins  # ✅ 必须引入
from utils.logger import log, save_log_file_if_needed, init_log_capture
from utils.db import get_connection
from utils.expert_hit_analysis import run_hit_analysis_batch
from utils.sound_utils import init_local_sound_map
init_local_sound_map()
# 顶部初始化日志捕获和替换
if "__print_original__" not in builtins.__dict__:
    builtins.__dict__["__print_original__"] = print
init_log_capture(script_name_hint=os.path.basename(__file__))
print = log


conn = get_connection()
lottery_name = "福彩3D"  # ✅ 彩票类型（支持如 "福彩3D"、"排列3" 等）
query_issues = [None]  # ✅ 要分析的期号列表:[None] =最新一期,["All"]=所有期号，指定多期:"2025159", "2025158", "2025157"
# query_issues = ["All"]
all_mode_limit = None           # ✅ 2=限制 ["All"] 模式最多分析最近2期（默认 None 表示不限制）

check_mode = "dingwei"  # ✅ 可选值："dingwei"（配合"dingwei_sha_pos"参数仅判断指定定位位），"all"（判断百十个位全部）
dingwei_sha_pos = 0  # ✅ 定位杀号位置（0=百位，1=十位，2=个位）
enable_track_open_rank = True
enable_hit_check = True
log_save_mode = False

# ✅ 分析参数配置（将统一传入 analyze_expert_hits 函数）
analysis_kwargs = dict(
    query_playtype_name="百位定1",  # ✅ 提取推荐记录的玩法
    analyze_playtype_name="百位定1",  # ✅ 用于命中分析的玩法
    mode="rank",  # # ✅ 分析模式："rank" = 命中数排名筛选，"hitcount" = 具体命中次数条件筛选
    hit_rank_list=[1],  # ✅ 命中排名筛选（仅 mode="rank" 时生效）  |  最多命中的专家（正数）,最少命中的专家（负数）,命中次数排名筛选列表：[1]=最多命中,[2]=第二多，可填多个如 [1,2]，命中数字数量模式：["hit+0"] 代表命中开奖号码数量 = 0；["hit+1"] 代表命中数量 = 1，依此类推。
    hit_count_conditions={"双胆": ("==", 0)},  # ✅ 命中次数筛选（仅 mode="hitcount" 时生效）|  命中数运算支持符： "==": 等于  |  ">=": 大于等于  |  "<=": 小于等于  |  ">" : 大于  |  "<" : 小于
    lookback_n=2,  # ✅ 回溯期数, |   None 表示不限期数，1 表示只分析上一期,2 表示只上两期作为历史期号
    lookback_start_offset=0,  # ✅ 回溯起点偏移  |  向前跳过2期，即回溯的是 query_issue -2 的那一期
    enable_sha1=[9],          # ✅杀号1 控制开关         #=======================================
    enable_sha2=False,          # ✅杀号2 控制开关         #  False=不启用
    enable_dan1=False,          # ✅定胆1 控制开关         #  [1]=启用并提取排名第一位的数字
    enable_dan2=False,          # ✅定胆2 控制开关         #  [1,2]=启用并提取排名第一位、第二位的两个数字
    enable_dingwei_sha=False,     # ✅定位杀号1 控制开关    #  [-1,-2]=启用并提取排名倒数第一位、第二的两个数字
    enable_dingwei_sha2=False,  # ✅定位杀号2 杀号控制开关   # [1, "prev+1", -1]=支持组合，["prev+1"]  = 以上期开奖号的定位位 +1 个推荐排名数字，["prev-1"]   =上期开奖号的定位位 -1 个推荐数字，["prev"] =  等价于 ["prev+0"]，即直接使用该数字本身
    enable_dingwei_sha3=False,   # ✅定位杀号3 杀号控制开关  #
    enable_dingwei_dan1=False,  # ✅ 定位定胆1，控制开关       #=======================================

    # ✅ 控制每个策略的跳过行为
    skip_if_few_sha1=False,
    skip_if_few_sha2=False,
    skip_if_few_dan1=False,
    skip_if_few_dan2=False,
    skip_if_few_dingwei_sha=False,     # 👈 推荐数少于5时跳过定位杀号1,True=开启/ False=关闭
    skip_if_few_dingwei_sha2=False,
    skip_if_few_dingwei_sha3=False,

    # ✅ 控制每个策略的“频次并列”行为
    resolve_tie_mode_sha1 = "False",
    resolve_tie_mode_sha2 = "False",
    resolve_tie_mode_dan1 = "False",
    resolve_tie_mode_dan2 = "False",           # 👈 在推荐数字频次排序中，如果指定提取位置上的数字出现“频次并列”，可以根据配置控制,False=关闭，Skip=跳过(不提取)，Next=向后找下一个不并列的数字
    resolve_tie_mode_dingwei_sha = "False",
    resolve_tie_mode_dingwei_sha2 = "False",
    resolve_tie_mode_dingwei_sha3 = "False",
    resolve_tie_mode_dingwei_dan1 = "False",

    # ✅ 并列频次触发反向提取控制项（新增）
    reverse_on_tie_dingwei_sha=False,
    reverse_on_tie_dingwei_sha2=False,
    reverse_on_tie_dingwei_sha3=False,
    reverse_on_tie_dingwei_dan1=False,
)

# ✅ 执行批量分析任务，输出每期推荐与命中结果统计
run_hit_analysis_batch(
    conn=conn,
    lottery_name=lottery_name,
    query_issues=query_issues,
    all_mode_limit=all_mode_limit,  # ✅ 新增参数
    enable_hit_check=enable_hit_check,
    enable_track_open_rank=enable_track_open_rank,
    dingwei_sha_pos=dingwei_sha_pos,
    check_mode=check_mode,
    analysis_kwargs=analysis_kwargs
)
save_log_file_if_needed(log_save_mode, script_name_hint=os.path.basename(__file__))


"""
功能特点：
- 支持传入单期、多期或 ["All"] 模式，批量分析福彩3D中指定玩法的推荐与命中情况；
- 内置回溯控制机制（lookback_n + lookback_start_offset），可灵活设定回溯区间；
- 支持两种专家筛选模式：
    1）命中排名模式（mode="rank"）：按命中次数排序提取前N名或后N名专家；
    2）命中次数模式（mode="hitcount"）：按玩法命中次数筛选符合条件的专家；
- 支持启用/关闭多种推荐策略（杀号、定胆、定位杀号、定位定胆），并精细指定频次位置（如排名第1、第2名）；
- 每种策略支持以下控制参数：
    - 推荐数不足时是否跳过；
    - 推荐频次并列时的处理方式（False/Skip/Next）；
- 支持启用杀号命中判断（check_mode="all"/"dingwei"），统计命中结果并输出结果详情；
- 支持追踪开奖号在推荐频次中的排名位置，辅助策略评估；
- 自动捕获所有日志输出（print/log），支持按脚本名保存为日志文件；
- 脚本可配合 WeCom 推送、定时任务、自动回测等系统使用，便于自动化分析部署。

使用场景：
- 福彩3D杀号策略效果验证与批量评估；
- 专家推荐命中筛选与历史数据回测；
- 高频定位杀号模型的离线调试与效果监控；
- 自动生成推荐报告或日志记录用于模型比对分析。
"""

# 📉 共 44 期，未命中次数：2 期，跳过 1 期
# ✅ 命中率：41 / 44
# 📊 开奖号码在推荐数字频次排序中的排名统计：
# - 排名第 1 位：3 次
# - 排名第 2 位：5 次
# - 排名第 3 位：5 次
# - 排名第 4 位：6 次
# - 排名第 5 位：2 次
# - 排名第 6 位：2 次
# - 排名第 7 位：3 次
# - 排名第 8 位：3 次
# - 排名第 9 位：1 次
# - 排名第 10 位：2 次