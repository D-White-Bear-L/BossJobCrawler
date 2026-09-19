# BOSS 直聘招聘数据采集 —— 第一阶段 MVP

真实从 BOSS 直聘采集招聘数据并保存为 CSV。已跑通「广州 + Python」，
成功采集 20 条真实岗位到 `data/jobs.csv`。

## 运行

```bash
# 使用虚拟环境 wjx（内含 Playwright）
C:/Users/baixiong/.conda/envs/wjx/python.exe main.py
```

首次运行会弹出 Edge 窗口并等待扫码登录（登录态保存到 `state/login_state.json`），
之后运行免登录。采集频率：请求间随机等待 2~5 秒，单浏览器单页面，不并发。

## 技术方案（重要）

BOSS 直聘对「自动化浏览器 + 未登录/未过安全校验」的访问一律返回 `code=37 环境异常`，
公开页面（搜索页 / 详情页 / 搜索接口）全部需要先通过浏览器安全校验。

本项目的采集链路（已实测跑通）：

1. **登录**：用户手动扫码登录一次，`wt2` 登录态经 Playwright `storage_state` 持久化。
2. **反爬**：`crawler/anti_bot.py` 隐藏 `navigator.webdriver` 等自动化指纹
   （经你授权；属于修改浏览器指纹绕过风控），并从 `code=37` 响应提取 `seed/name/ts`，
   访问 `security-check.html` 让浏览器 JS 生成 `__zp_stoken__`。
3. **采集**：带登录态 + stoken，用浏览器内 `fetch` 调用
   `wapi/zpgeek/search/joblist.json`（列表）与 `wapi/zpgeek/job/detail.json`（详情）。
4. **映射**：`crawler/mapper.py` 把接口字段映射到 CSV 的 23 个字段。
5. **去重**：`crawler/exporter.py` 按 `job_id` → `job_url` → `job_name+company_name+city`。

> 注：需求文档第五节提到「HTTP 优先、需要时再 Playwright」。实测纯 HTTP 请求
> 直接被 `code=37` 拦截，必须走浏览器 + 登录 + 过 security-check，因此本项目
> 采用「浏览器内 fetch」而非 requests。

## 结构

```
main.py            # 入口：登录 -> security-check -> 列表/详情采集 -> 写 CSV
config.py          # 城市/关键词/延迟/URL/CSV字段 全部配置化
crawler/
  browser.py       # Playwright 启动（stealth + storage_state，单页面）
  login.py         # 登录态检测 + 等待扫码
  anti_bot.py      # stealth 指纹隐藏 + security-check + 浏览器内 fetch
  search.py        # joblist.json 采集
  detail.py        # detail.json 采集
  mapper.py        # 接口字段 -> CSV 字段映射
  exporter.py      # CSV 写入 + 去重
  logger.py        # 终端 + 文件日志
data/jobs.csv      # 输出（真实数据）
state/login_state.json  # 登录态（持久化）
debug/             # 日志 / 调试证据
```

## 扩展

后续阶段（尚未实现）：多关键词、多城市、翻页、断点续采（`state/state.json`）。
城市/关键词已在 `config.py` 配置化，改 `CITIES` / `KEYWORDS` 即可。
