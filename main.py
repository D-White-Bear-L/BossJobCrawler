# -*- coding: utf-8 -*-
"""Boss 直聘招聘数据采集 —— 入口。

链路：登录态 -> 过 security-check 拿 stoken -> 多城市×多关键词×翻页 fetch 列表
      -> (可选) fetch 详情 -> 字段映射 -> 去重 -> 写 data/jobs.csv -> 断点续采。

反爬策略（已获用户授权）：stealth 隐藏自动化指纹 + security-check 生成 __zp_stoken__。
频率控制：每次请求前随机等待 MIN_DELAY~MAX_DELAY 秒，单浏览器单页面，不并发。

用法示例：
    python main.py                         # 按 config 全量（珠三角9城 × 11关键词 × 3页，抓详情）
    python main.py --no-detail             # 只抓列表（快，适合铺数据量）
    python main.py --pages 1 --no-detail   # 每关键词 1 页
    python main.py --cities 广州,深圳 --keywords Python,Java
    python main.py --no-resume             # 忽略断点，重新采集
"""
import argparse
import random
import time

import config
from crawler import logger
from crawler.browser import BrowserSession
from crawler.exporter import CsvExporter
from crawler.anti_bot import AntiBot, has_user_login, has_stoken
from crawler.state import Checkpoint
from crawler import login, search, detail, mapper


def random_delay():
    sec = random.uniform(config.MIN_DELAY, config.MAX_DELAY)
    logger.info(f"随机等待 {sec:.1f} 秒 ...")
    time.sleep(sec)


def collect_keyword_page(ab, exporter, city, city_code, keyword, page, fetch_detail):
    """采集一个「城市+关键词+页码」，返回 (该页新增条数, has_more)；被拦截返回 (-1, False)。"""
    raw_jobs, has_more = search.fetch_joblist(ab, keyword, city_code, page=page)
    if raw_jobs is None:
        return -1, False

    logger.info(f"发现岗位：{len(raw_jobs)}（hasMore={has_more}）")

    added = 0
    for job in raw_jobs:
        d = None
        if fetch_detail:
            random_delay()
            d = detail.fetch_detail(ab, job.get("securityId"))
        row = mapper.job_to_row(job, d, keyword, city)
        n, _ = exporter.add_many([row])
        added += n

    logger.info(f"第 {page} 页新增：{added}，CSV 累计：{exporter.total}")
    return added, has_more


def parse_args():
    p = argparse.ArgumentParser(description="BOSS 直聘招聘数据采集")
    p.add_argument("--cities", help="逗号分隔城市，默认用 config.CITIES")
    p.add_argument("--keywords", help="逗号分隔关键词，默认用 config.KEYWORDS")
    p.add_argument("--pages", type=int, default=None, help="每关键词最大页数，默认 config.MAX_PAGES")
    p.add_argument("--no-detail", action="store_true", help="不抓岗位详情（快）")
    p.add_argument("--no-resume", action="store_true", help="忽略断点，重新采集")
    return p.parse_args()


def main():
    args = parse_args()

    cities = args.cities.split(",") if args.cities else config.CITIES
    keywords = args.keywords.split(",") if args.keywords else config.KEYWORDS
    max_pages = args.pages if args.pages is not None else config.MAX_PAGES
    fetch_detail = config.FETCH_DETAIL and not args.no_detail

    logger.info("=" * 50)
    logger.info("BOSS 直聘招聘数据采集")
    logger.info(f"城市：{len(cities)} 个  关键词：{len(keywords)} 个  每关键词最多 {max_pages} 页")
    logger.info(f"抓详情：{'是' if fetch_detail else '否'}")
    logger.info("=" * 50)

    exporter = CsvExporter()
    ckpt = Checkpoint()

    with BrowserSession() as session:
        page = session.page
        ctx = session.context

        # 1) 登录态
        if not has_user_login(ctx.cookies()):
            logger.info("未检测到登录态，打开登录页等待扫码 ...")
            if not login.ensure_login(ctx, page):
                logger.error("未登录，无法采集。")
                return 1
            session.save_login_state()

        # 2) 反爬会话初始化
        ab = AntiBot(ctx, page)
        logger.info("会话初始化（security-check）...")
        ab.bootstrap_session()
        logger.info(
            f"stoken={'有' if has_stoken(ctx.cookies()) else '无'}, "
            f"登录={'是' if has_user_login(ctx.cookies()) else '否'}"
        )

        # 3) 采集
        blocked = False
        for city in cities:
            city_code = config.CITY_CODES.get(city)
            if not city_code:
                logger.error(f"未找到城市编码: {city}")
                continue
            for keyword in keywords:
                logger.info(f"城市：{city}  关键词：{keyword}")
                for page in range(1, max_pages + 1):
                    key = f"{city}|{keyword}|{page}"
                    if not args.no_resume and ckpt.is_done(key):
                        logger.info(f"已采集过，跳过：{key}")
                        continue

                    random_delay()
                    added, has_more = collect_keyword_page(
                        ab, exporter, city, city_code, keyword, page, fetch_detail
                    )
                    if added < 0:
                        blocked = True
                        break
                    ckpt.mark_done(key)
                    if not has_more:
                        logger.info("该关键词已无更多页，进入下一关键词。")
                        break
                if blocked:
                    break
            if blocked:
                break

    logger.info("采集结束。CSV 路径: %s，累计 %s 条" % (config.CSV_PATH, exporter.total))
    return 1 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
