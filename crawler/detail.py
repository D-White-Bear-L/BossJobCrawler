# -*- coding: utf-8 -*-
"""岗位详情采集：通过浏览器内 fetch 调用 detail.json 获取岗位描述与 HR 信息。"""
from crawler import logger
from crawler.anti_bot import is_blocked_response

DETAIL_API = "/wapi/zpgeek/job/detail.json"


def fetch_detail(anti_bot, security_id):
    """返回详情 dict（code==0 时含 zpData.jobInfo / zpData.bossInfo），失败返回 None。"""
    if not security_id:
        return None
    data = anti_bot.fetch_with_retry(DETAIL_API, {"securityId": security_id}, max_retries=3)
    if is_blocked_response(data) or data.get("code") != 0:
        logger.warn(f"详情接口失败 securityId={security_id[:20]}... code={data.get('code')}")
        return None
    return data
