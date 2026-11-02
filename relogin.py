# -*- coding: utf-8 -*-
"""重新登录刷新会话 + 验证薪资是否恢复。

过程：备份旧登录态 -> 弹出浏览器等你扫码 -> 保存新登录态 -> 抓一页验证 salaryDesc。
"""
import os

import config
from crawler import logger
from crawler.browser import BrowserSession
from crawler.anti_bot import AntiBot, has_user_login, has_stoken
from crawler import login, search


def main():
    # 备份并移除旧登录态，强制重新登录
    if os.path.exists(config.LOGIN_STATE_PATH):
        os.replace(config.LOGIN_STATE_PATH, config.LOGIN_STATE_PATH + ".old")
        logger.info("旧登录态已备份为 state/login_state.json.old")

    with BrowserSession() as session:
        page = session.page
        ctx = session.context

        logger.info("请在弹出的浏览器窗口扫码登录（刷新会话）...")
        if not login.ensure_login(ctx, page, timeout=240):
            logger.error("登录失败或超时")
            return 1
        session.save_login_state()
        logger.info("新登录态已保存到 state/login_state.json")

        # 验证薪资
        ab = AntiBot(ctx, page)
        ab.bootstrap_session()
        logger.info(f"stoken={'有' if has_stoken(ctx.cookies()) else '无'}")

        jobs, has_more = search.fetch_joblist(ab, "Python", "101280600", page=1)
        if jobs:
            sal = sum(1 for j in jobs if j.get("salaryDesc"))
            logger.info(f"薪资验证：{len(jobs)} 条中 {sal} 条有薪资")
            for j in jobs[:5]:
                logger.info(f"  样例：{j.get('jobName')!r} salaryDesc={j.get('salaryDesc')!r}")
        else:
            logger.warn("薪资验证：未拿到数据")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
