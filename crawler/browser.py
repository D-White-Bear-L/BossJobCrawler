# -*- coding: utf-8 -*-
"""Playwright 浏览器生命周期：单实例、单页面、不并发。

登录态用 storage_state 持久化（cookie/localStorage 落盘到 config.LOGIN_STATE_PATH）。
注意：不用 launch_persistent_context —— 实测会导致 BOSS 页面渲染为空白(about:blank)。
"""
import os

from playwright.sync_api import sync_playwright

import config


class BrowserSession:
    """浏览器会话。用法：

        with BrowserSession() as session:
            session.page.goto(...)
            session.ensure_login()   # 未登录则等待扫码
            session.save_login_state()
    """

    def __init__(self):
        self._pw = None
        self._browser = None
        self._context = None
        self._page = None

    def __enter__(self):
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=config.HEADLESS,
            channel=config.CHANNEL,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-popup-blocking",
            ],
        )
        ctx_kwargs = dict(
            viewport=config.VIEWPORT,
            user_agent=config.UA,
        )
        if os.path.exists(config.LOGIN_STATE_PATH):
            ctx_kwargs["storage_state"] = config.LOGIN_STATE_PATH

        self._context = self._browser.new_context(**ctx_kwargs)
        # 隐藏自动化指纹（反爬核心，需用户授权）
        from crawler import anti_bot
        anti_bot.AntiBot(self._context, None).apply_stealth()
        # 第一阶段：默认只使用一个页面
        self._page = self._context.new_page()
        return self

    @property
    def page(self):
        return self._page

    @property
    def context(self):
        return self._context

    def save_login_state(self):
        """把当前登录态（cookie/localStorage）持久化到磁盘。"""
        os.makedirs(os.path.dirname(config.LOGIN_STATE_PATH), exist_ok=True)
        self._context.storage_state(path=config.LOGIN_STATE_PATH)

    def __exit__(self, exc_type, exc, tb):
        try:
            if self._context:
                self._context.close()
        except Exception:
            pass
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._pw:
                self._pw.stop()
        except Exception:
            pass
