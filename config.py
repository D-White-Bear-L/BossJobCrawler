# -*- coding: utf-8 -*-
"""全局配置：城市 / 关键词 / 延迟 / 路径 / URL 均在此处配置。

设计原则（对应需求文档）：
- 城市、关键词必须配置化，不写死在核心逻辑里。
- 请求之间随机等待（MIN_DELAY ~ MAX_DELAY 秒）。
- 第一阶段 concurrency = 1，单浏览器单页面，不并发。
"""
import os

# 项目根目录（必须在任何使用 BASE_DIR 的配置之前定义）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# 采集目标（第二阶段：珠三角 9 城 + 多关键词）
# ---------------------------------------------------------------------------
CITIES = [
    "广州",
    "深圳",
    "佛山",
    "东莞",
    "珠海",
    "中山",
    "惠州",
    "江门",
    "肇庆",
]

KEYWORDS = [
    "Python",
    "Java",
    "后端开发",
    "大模型",
    "AI",
    "人工智能",
    "算法工程师",
    "数据开发",
    "数据分析",
    "全栈开发",
    "软件开发",
]

# 城市 -> BOSS 城市编码。第一阶段城市已配置；未来可继续追加。
# 说明：编码以 BOSS 实际页面为准，新增城市时建议先人工在页面确认一次。
CITY_CODES = {
    "广州": "101280100",
    "深圳": "101280600",
    "佛山": "101280800",
    "东莞": "101281600",
    "珠海": "101280700",
    "中山": "101281700",
    "惠州": "101280300",
    "江门": "101281100",
    "肇庆": "101280900",
    # 未来扩展（编码待现场核对）
    "北京": "101010100",
    "上海": "101020100",
    "杭州": "101210100",
    "成都": "101270100",
    "武汉": "101200100",
    "南京": "101190100",
    "西安": "101110100",
}

# ---------------------------------------------------------------------------
# 反爬友好参数
# ---------------------------------------------------------------------------
MIN_DELAY = 5      # 请求之间最小随机等待（秒）——调慢，减少触发安全校验
MAX_DELAY = 8      # 请求之间最大随机等待（秒）
CONCURRENCY = 1    # 固定为 1，不并发
MAX_PAGES = 3      # 每个「城市+关键词」最多翻页数（BOSS 单条件约上限 10 页）
FETCH_DETAIL = True  # 是否抓取岗位详情（JD/地址/招聘者）；关掉可大幅提速

# ---------------------------------------------------------------------------
# 浏览器
# ---------------------------------------------------------------------------
HEADLESS = False   # 真实采集需有头浏览器（扫码登录 + 减少被识别），保持 False
CHANNEL = "msedge"  # 使用本机已安装的 Edge，比 Playwright 自带 Chromium 更接近真实浏览器
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
VIEWPORT = {"width": 1366, "height": 900}

# 持久化登录态文件（首次登录后，cookie/localStorage 保存到此，后续免登录）
# 注意：不用 launch_persistent_context（会导致 BOSS 页面空白），改用 storage_state。
LOGIN_STATE_PATH = os.path.join(BASE_DIR, "state", "login_state.json")

# 登录相关
LOGIN_URL = "https://www.zhipin.com/web/user/"
LOGIN_TIMEOUT = 180  # 等待用户扫码登录的秒数

# ---------------------------------------------------------------------------
# URL
# ---------------------------------------------------------------------------
BASE_URL = "https://www.zhipin.com"
# 公开职位搜索页（城市用编码）
SEARCH_URL_TMPL = "https://www.zhipin.com/web/geek/job?query={keyword}&city={city_code}"
# 搜索列表接口（HTTP 优先验证用）
JOBLIST_API_TMPL = (
    "https://www.zhipin.com/wapi/zpgeek/search/joblist.json"
    "?query={keyword}&city={city_code}&page={page}&pageSize=30"
)
# 岗位详情页
JOB_DETAIL_URL_TMPL = "https://www.zhipin.com/job_detail/{job_id}.html"

# ---------------------------------------------------------------------------
# 路径（相对项目根目录）
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(BASE_DIR, "data")
DEBUG_DIR = os.path.join(BASE_DIR, "debug")
SCREENSHOT_DIR = os.path.join(DEBUG_DIR, "screenshot")
HTML_DIR = os.path.join(DEBUG_DIR, "html")
LOG_DIR = os.path.join(DEBUG_DIR, "logs")
STATE_DIR = os.path.join(BASE_DIR, "state")

CSV_PATH = os.path.join(DATA_DIR, "jobs.csv")
STATE_PATH = os.path.join(STATE_DIR, "state.json")

# CSV 字段（需求文档 第十三节）
CSV_FIELDS = [
    "job_id",
    "job_name",
    "job_url",
    "salary",
    "city",
    "district",
    "experience",
    "education",
    "job_tags",
    "job_description",
    "company_id",
    "company_name",
    "company_url",
    "company_industry",
    "company_scale",
    "company_financing",
    "company_address",
    "company_description",
    "recruiter_name",
    "recruiter_title",
    "source_keyword",
    "source_city",
    "crawl_time",
]

# ---------------------------------------------------------------------------
# 说明：本 MVP 最终采用「浏览器内 fetch 调用 wapi 接口」的方式采集（见 crawler/anti_bot.py、
# search.py、detail.py），而非解析 DOM。接口返回的字段在 crawler/mapper.py 中映射到 CSV_FIELDS。
# ---------------------------------------------------------------------------
