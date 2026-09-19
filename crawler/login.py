# -*- coding: utf-8 -*-
"""手动登录支持：检测登录态 + 等待用户扫码登录。

对应需求文档第八节的合规要求：
- 不自动输入手机号、不自动获取验证码、不自动注册。
- 只做「打开登录页 -> 用户自己扫码 -> 等待登录态出现」。
"""
import time

import config
from crawler import logger


def is_logged_in(context):
    """通过 wt2 cookie（求职者登录态）判断是否已登录。"""
    try:
        cookies = context.cookies()
    except Exception:
        return False
    for c in cookies:
        if c.get("name") == "wt2" and c.get("value"):
            return True
    return False


def ensure_login(context, page, timeout=None):
    """确保已登录；未登录则打开登录页等待用户扫码。返回是否登录成功。"""
    timeout = timeout or config.LOGIN_TIMEOUT

    if is_logged_in(context):
        logger.info("检测到已登录（wt2 存在），跳过登录。")
        return True

    logger.info("未检测到登录态，打开登录页。")
    logger.info("=" * 60)
    logger.info("请在弹出的浏览器窗口里，用手机 BOSS 直聘 App 扫码登录。")
    logger.info("本程序只等待，不会自动输入手机号/验证码/注册。")
    logger.info("=" * 60)

    try:
        page.goto(config.LOGIN_URL, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        logger.warn(f"打开登录页异常: {e}")

    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(3)
        if is_logged_in(context):
            logger.info("登录成功。")
            return True

    logger.error(f"登录等待超时（{timeout}s），未检测到 wt2 登录态。")
    return False
