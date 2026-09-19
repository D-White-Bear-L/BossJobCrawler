# -*- coding: utf-8 -*-
"""岗位列表采集：通过浏览器内 fetch 调用 joblist.json（携带 stoken + 登录态）。"""
from crawler import logger
from crawler.anti_bot import is_blocked_response

SEARCH_API = "/wapi/zpgeek/search/joblist.json"


def fetch_joblist(anti_bot, keyword, city_code, page=1, page_size=30):
    """返回 (raw_jobs: list[dict], has_more: bool)；被拦截时返回 (None, False)。"""
    params = {
        "scene": "1",
        "query": keyword,
        "city": city_code,
        "page": str(page),
        "pageSize": str(page_size),
    }
    # 优先 fetch_api（带 scene=1 能拿到明文薪资 salaryDesc + 显式分页），
    # 拿不到数据时（限流/失败）再退回 search_via_ui（导航+拦截，但无薪资且分页不生效）
    data = anti_bot.fetch_with_retry(SEARCH_API, params, max_retries=3)
    if not (data.get("zpData") or {}).get("jobList"):
        data = anti_bot.search_via_ui(keyword, city_code, page_num=page)

    if is_blocked_response(data):
        logger.error(f"列表接口被拦截 code={data.get('code')} msg={data.get('message')}")
        return None, False

    zp = data.get("zpData") or {}
    jobs = zp.get("jobList") or []
    has_more = bool(zp.get("hasMore", False))
    if not jobs:
        logger.warn(
            f"列表接口返回空 code={data.get('code')} msg={data.get('message')} "
            f"zpData.keys={list(zp.keys())} resCount={zp.get('resCount')}"
        )
    return jobs, has_more
