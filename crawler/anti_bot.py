# -*- coding: utf-8 -*-
"""反爬处理（移植自已验证的 BossWork 方案）：
1. stealth：隐藏 navigator.webdriver 等自动化指纹；
2. security-check：从 code=37 响应提取 seed/name/ts，访问 security-check.html 生成 __zp_stoken__；
3. 浏览器内 fetch：携带完整请求头，模拟页面 XHR 调用 wapi 接口。

注意：本模块的 stealth 属于「修改浏览器指纹绕过风控」，仅在用户明确确认后使用。
"""
import random
import time
from urllib.parse import quote

ANTI_BOT_CODES = {37, 35, 121}

# Playwright / Chrome 自动化特征隐藏
STEALTH_INIT_SCRIPT = """
(() => {
  Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
  Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
  Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });

  window.chrome = window.chrome || { runtime: {} };

  const originalQuery = window.navigator.permissions.query;
  window.navigator.permissions.query = (parameters) =>
    parameters.name === 'notifications'
      ? Promise.resolve({ state: Notification.permission })
      : originalQuery(parameters);

  delete window.__playwright;
  delete window.__pwInitScripts;
})();
"""

# 浏览器内 fetch 模板（携带完整请求头，模拟页面 XHR）
BROWSER_FETCH_SCRIPT = """
async ({ apiPath, params }) => {
  const query = new URLSearchParams(params).toString();
  const origin = window.location.origin.includes('zhipin.com')
    ? window.location.origin
    : 'https://www.zhipin.com';
  const url = origin + apiPath + '?' + query;
  const resp = await fetch(url, {
    method: 'GET',
    credentials: 'include',
    headers: {
      'Accept': 'application/json, text/plain, */*',
      'X-Requested-With': 'XMLHttpRequest',
      'Referer': origin + '/web/geek/jobs',
      'sec-fetch-dest': 'empty',
      'sec-fetch-mode': 'cors',
      'sec-fetch-site': 'same-origin',
    },
  });
  return await resp.json();
}
"""


def is_blocked_response(data):
    if not isinstance(data, dict):
        return True
    code = data.get("code")
    if code in ANTI_BOT_CODES:
        return True
    if code not in (0, None):
        msg = str(data.get("message") or "")
        if any(k in msg for k in ("异常", "频繁", "验证", "安全")):
            return True
    return False


def extract_security_params(data):
    zp = data.get("zpData") or {}
    seed = zp.get("seed")
    ts = zp.get("ts")
    name = zp.get("name")
    if seed and ts and name:
        return {"seed": seed, "ts": str(ts), "name": name}
    return None


def has_stoken(cookies):
    return any(c.get("name") == "__zp_stoken__" and c.get("value") for c in cookies)


def has_user_login(cookies):
    for name in ("wt2", "geek_zp_token", "zp_token"):
        if any(c.get("name") == name and c.get("value") for c in cookies):
            return True
    return False


class AntiBot:
    """反爬处理器：stealth、security-check、fetch。"""

    SECURITY_CHECK_URL = "https://www.zhipin.com/web/common/security-check.html"
    JOBS_URL = "https://www.zhipin.com/web/geek/jobs"
    COOLDOWN_SEC = 20

    def __init__(self, context, page):
        self.context = context
        self.page = page
        self._last_security_key = None
        self._last_security_at = 0.0

    # ------------------------------------------------------------------
    def apply_stealth(self):
        self.context.add_init_script(STEALTH_INIT_SCRIPT)

    @staticmethod
    def human_delay(page, base_ms=800, jitter_ms=1200):
        page.wait_for_timeout(base_ms + random.randint(0, jitter_ms))

    def simulate_human_activity(self):
        """模拟鼠标移动 + 滚动，降低行为检测风险。"""
        try:
            width = self.page.viewport_size["width"] if self.page.viewport_size else 1440
            height = self.page.viewport_size["height"] if self.page.viewport_size else 900
            for _ in range(random.randint(1, 3)):
                self.page.mouse.move(
                    random.randint(80, width - 80),
                    random.randint(80, height - 80),
                    steps=random.randint(8, 20),
                )
                self.page.wait_for_timeout(random.randint(200, 600))
            self.page.evaluate("window.scrollBy(0, arguments[0])", random.randint(120, 480))
            self.page.wait_for_timeout(random.randint(300, 800))
        except Exception:
            pass

    # ------------------------------------------------------------------
    def bootstrap_session(self):
        """打开 jobs 页，若没有 stoken 则反复触发 security-check 直到生成。"""
        self._safe_goto(self.JOBS_URL)
        time.sleep(2)
        self.simulate_human_activity()

        for _ in range(3):
            if has_stoken(self.context.cookies()):
                return
            self._trigger_security_via_search_probe()
            self._wait_for_stoken(20)
            if has_stoken(self.context.cookies()):
                return
            time.sleep(3)

        self._wait_for_stoken(10)

    def ensure_stoken(self):
        if has_stoken(self.context.cookies()):
            return True
        self._trigger_security_via_search_probe()
        self._wait_for_stoken(20)
        return has_stoken(self.context.cookies())

    # ------------------------------------------------------------------
    def fetch_api(self, api_path, params):
        try:
            return self.page.evaluate(
                BROWSER_FETCH_SCRIPT,
                {"apiPath": api_path, "params": params},
            )
        except Exception as e:
            return {"code": -1, "message": str(e), "zpData": {}}

    def _ensure_stable_page(self):
        """确保页面稳定在 zhipin 域（不在 security-check 循环 / about:blank）。"""
        url = self.page.url or ""
        if "zhipin.com" not in url or "_security_check" in url or url == "about:blank":
            self._safe_goto(self.JOBS_URL)
            time.sleep(2)

    def _safe_goto(self, url, timeout=60000):
        """导航并吞掉被拦截/abort 的异常（风控中止导航不抛错）。"""
        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            return True
        except Exception:
            return False

    def search_via_ui(self, keyword, city_code, page_num=1, timeout_ms=30000):
        """导航到搜索 URL 并拦截 joblist.json 响应（最接近真实用户，比 fetch 稳）。"""
        jobs_url = f"{self.JOBS_URL}?city={city_code}&query={quote(keyword)}&page={page_num}"
        captured = {}

        def on_response(response):
            if "search/joblist.json" in response.url and response.status == 200:
                try:
                    captured["data"] = response.json()
                except Exception:
                    pass

        self.page.on("response", on_response)
        try:
            try:
                self.page.goto(jobs_url, wait_until="domcontentloaded", timeout=60000)
            except Exception as e:
                # 页面被拦截/导航中止（net::ERR_ABORTED 等），交给 fallback
                return None
            self.human_delay(self.page, 1500, 1000)
            deadline = time.time() + timeout_ms / 1000
            while time.time() < deadline:
                if captured.get("data"):
                    break
                self.page.wait_for_timeout(500)
            if captured.get("data"):
                return captured["data"]
        finally:
            self.page.remove_listener("response", on_response)
        return None

    def fetch_with_retry(self, api_path, params, max_retries=3):
        last = {}
        for attempt in range(1, max_retries + 1):
            self._ensure_stable_page()
            self.simulate_human_activity()
            self.human_delay(self.page, 400, 800)

            last = self.fetch_api(api_path, params)
            if last.get("code") == -1:
                # fetch 抛异常（多半是页面正在导航），回 jobs 页重试
                self._safe_goto(self.JOBS_URL)
                time.sleep(2)
                continue
            if not is_blocked_response(last):
                return last

            self._recover_from_block(last)

        return last

    # ------------------------------------------------------------------
    def _trigger_security_via_search_probe(self):
        probe = self.fetch_api(
            "/wapi/zpgeek/search/joblist.json",
            {"scene": "1", "query": "Java", "city": "101010100", "page": "1", "pageSize": "1"},
        )
        params = extract_security_params(probe)
        if params:
            self.run_security_check(params)

    def run_security_check(self, params):
        if not self._should_run(params):
            return False
        seed = quote(params["seed"], safe="")
        name = params["name"]
        ts = params["ts"]
        callback = quote("/web/geek/jobs", safe="")
        url = (
            f"{self.SECURITY_CHECK_URL}?seed={seed}&name={name}&ts={ts}"
            f"&callbackUrl={callback}&srcReferer="
        )
        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=45000)
        except Exception:
            self.page.wait_for_timeout(5000)
        self.human_delay(self.page, 1500, 1000)

        ok = self._wait_for_stoken(20)
        self._mark(params)
        if ok:
            # 通过后回到 jobs 页，让后续 fetch 处于正确页面上下文
            try:
                self.page.goto(self.JOBS_URL, wait_until="domcontentloaded", timeout=60000)
                self.human_delay(self.page, 2000, 1000)
            except Exception:
                pass
        return ok

    def _should_run(self, params):
        key = f"{params.get('name')}:{params.get('ts')}"
        if key == self._last_security_key:
            if time.time() - self._last_security_at < self.COOLDOWN_SEC:
                return False
        return True

    def _mark(self, params):
        self._last_security_key = f"{params.get('name')}:{params.get('ts')}"
        self._last_security_at = time.time()

    def _recover_from_block(self, last):
        params = extract_security_params(last)
        if has_stoken(self.context.cookies()):
            # 已有 stoken 仍被拦：刷新 jobs 页即可
            self._safe_goto(self.JOBS_URL)
            self.human_delay(self.page, 1500, 800)
            self.simulate_human_activity()
            return
        if params:
            self.run_security_check(params)
        else:
            self._safe_goto(self.JOBS_URL)
            time.sleep(2)

    def _wait_for_stoken(self, timeout_sec=15):
        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            if has_stoken(self.context.cookies()):
                return True
            self.page.wait_for_timeout(500)
        return has_stoken(self.context.cookies())
