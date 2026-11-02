# BossJobCrawler — BOSS 直聘招聘数据采集器

> 珠三角互联网 / 计算机岗位技术栈需求研究 · 个人研究用的公开数据采集工具

本项目用于从 [BOSS 直聘](https://www.zhipin.com) 采集公开招聘信息（岗位、公司、薪资、技能要求等），
保存为 `data/jobs.csv`，以便研究珠三角地区 AI / 大模型 / Python / Java 等方向的技术栈需求。
**所有数据均为程序真实运行采集，不使用任何 Mock 或假数据。**

---

## ⚠️ 合规与使用声明（必读）

本项目**仅供个人学习与研究公开数据使用**，请在使用前知悉并遵守以下原则：

- 使用**本人账号**登录，遵守 BOSS 直聘的《用户协议》与 `robots.txt`；若网站明确禁止采集，请立即停止。
- 内置频率控制（请求间随机等待 5~8 秒、单浏览器单页面、不并发），**请勿用于高频、批量、商业倒卖或攻击性行为**。
- 采集过程尊重网站的安全校验机制，仅以正常浏览器会话访问公开页面，不做任何破坏性绕过。
- 输出字段以公开可见信息为限；页面未提供的字段**留空而非伪造**。
- 采集到的数据**不含个人隐私信息**，但请勿将其用于任何侵犯他人权益的用途。

如因违反上述约定产生的任何后果，由使用者自行承担。

---

## ✨ 特性

- **配置化**：城市、关键词、延迟、翻页数等全部集中在 `config.py`，不写死在逻辑里。
- **真实浏览器采集**：基于 Playwright + 本机 Edge，以登录态 + 安全校验会话访问官方公开接口。
- **登录态持久化**：首次扫码登录后，`storage_state` 持久化到 `state/login_state.json`，后续免登录。
- **岗位列表 + 详情**：列表（薪资 / 地点 / 经验学历 / 标签）+ 详情（JD 描述 / 公司信息 / 招聘者）。
- **多层去重**：按 `job_id` → `job_url` → `job_name + company_name + city` 三级去重。
- **断点续采**：`state/state.json` 记录已完成的「城市 + 关键词 + 页码」，中断后可续跑。
- **反爬友好**：随机等待、单实例单页面、不并发，尽量贴近正常访问。

---

## 🛠 环境要求

| 项 | 说明 |
| --- | --- |
| 操作系统 | Windows（路径与浏览器通道按本机配置；其他平台需微调） |
| Python | 3.10+ |
| 浏览器 | 本机已安装 **Microsoft Edge**（默认 `CHANNEL = "msedge"`） |
| 依赖 | `playwright` |

---

## 📦 安装

```bash
# 1. 克隆（若尚未克隆）或进入项目目录
cd BossJobCrawler

# 2. （推荐）创建并激活虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装 Playwright 浏览器驱动（使用本机 Edge 时可跳过，但首次需确保 Edge 已装）
playwright install
```

> 本项目通过 `channel="msedge"` 复用本机已安装的 Edge，比 Playwright 自带 Chromium 更接近真实浏览器。
> 若改用 Chromium，请在 `config.py` 中调整 `CHANNEL`。

---

## 🚀 快速开始

```bash
# 全量采集（珠三角 9 城 × 11 关键词 × 3 页，抓详情）
python main.py

# 只抓列表，不抓详情（更快，适合先铺数据量）
python main.py --no-detail

# 每关键词仅 1 页
python main.py --pages 1 --no-detail

# 指定城市与关键词
python main.py --cities 广州,深圳 --keywords Python,Java

# 忽略断点，重新采集
python main.py --no-resume

# 登录态过期时，重新扫码刷新会话并验证
python relogin.py
```

首次运行会弹出 Edge 窗口并等待你**扫码登录**（登录态保存到 `state/login_state.json`），之后运行免登录。
终端会实时打印采集进度：`发现岗位 → 解析 → 新增 → CSV 累计`。

---

## 💻 命令行参数

| 参数 | 说明 |
| --- | --- |
| `--cities` | 逗号分隔的城市，默认用 `config.CITIES` |
| `--keywords` | 逗号分隔的关键词，默认用 `config.KEYWORDS` |
| `--pages` | 每个「城市 + 关键词」最大翻页数，默认 `config.MAX_PAGES` |
| `--no-detail` | 不抓岗位详情（仅列表，速度更快） |
| `--no-resume` | 忽略断点，从头重新采集 |

---

## ⚙️ 配置（`config.py` 核心项）

| 配置 | 默认 | 说明 |
| --- | --- | --- |
| `CITIES` | 珠三角 9 城 | 目标城市列表，可扩展到全国 |
| `KEYWORDS` | 11 个技术关键词 | 搜索关键词列表 |
| `CITY_CODES` | 城市 → BOSS 编码 | 新增城市需先在页面核对编码 |
| `MIN_DELAY` / `MAX_DELAY` | 5 / 8 | 请求间随机等待秒数 |
| `CONCURRENCY` | 1 | 固定单实例，不并发 |
| `MAX_PAGES` | 3 | 每条件最多翻页数 |
| `FETCH_DETAIL` | `True` | 是否抓取岗位详情 |
| `HEADLESS` | `False` | 需有头浏览器（扫码 + 降低被识别概率） |
| `CHANNEL` | `"msedge"` | 使用的浏览器通道 |

---

## 📁 输出字段（`data/jobs.csv`）

共 **23 个字段**，以 UTF-8（带 BOM）保存，Excel 可直接打开：

`job_id` · `job_name` · `job_url` · `salary` · `city` · `district` · `experience` · `education` ·
`job_tags` · `job_description` · `company_id` · `company_name` · `company_url` · `company_industry` ·
`company_scale` · `company_financing` · `company_address` · `company_description` ·
`recruiter_name` · `recruiter_title` · `source_keyword` · `source_city` · `crawl_time`

字段缺失时留空，不删除整条记录、不伪造。

---

## 📂 项目结构

```
BossJobCrawler/
├── main.py              # 入口：登录 → 安全校验 → 列表/详情采集 → 写 CSV → 断点续采
├── relogin.py           # 重新扫码刷新登录态并验证薪资字段
├── config.py            # 城市 / 关键词 / 延迟 / 路径 / URL 全部配置化
├── requirements.txt     # 依赖
├── crawler/
│   ├── browser.py       # Playwright 启动（stealth + storage_state，单页面）
│   ├── login.py         # 登录态检测 + 等待扫码
│   ├── anti_bot.py      # 指纹隐藏 + security-check 会话握手 + 浏览器内 fetch
│   ├── search.py        # 岗位列表接口采集
│   ├── detail.py        # 岗位详情接口采集
│   ├── mapper.py        # 接口字段 → CSV 字段映射
│   ├── exporter.py      # CSV 写入 + 去重
│   ├── state.py         # 断点续采检查点
│   └── logger.py        # 终端 + 文件日志
├── data/
│   └── jobs.csv         # 采集输出（真实数据）
├── debug/               # 调试证据（截图 / HTML / 日志，已 gitignore）
└── state/               # 登录态与断点（登录态已 gitignore，切勿提交）
```

---

## 🔄 断点续采

`state/state.json` 记录每个「城市｜关键词｜页码」是否已完成。
中断后再次运行会**跳过已完成项**，从中断处继续，不会从头重跑（除非加 `--no-resume`）。

---

## ⏳ 风控限制与等待机制

BOSS 直聘对访问频率与浏览器环境有较严格的风控，本项目**刻意保持低频**，请务必了解以下几点：

- **必须等待（不是 bug）**：每次请求前程序会随机等待 `MIN_DELAY`~`MAX_DELAY` 秒（默认 **5~8 秒**）。这是为了避免触发 `code=37 环境异常`，**请耐心等，不要手动加速或并发**。一轮全量采集（9 城 × 11 关键词 × 3 页 + 详情）耗时较长，属正常现象。
- **连续失败自动暂停**：若某页连续采集失败达到 **3 次**，程序会暂停本轮并提示「连续多次失败，暂停采集（可稍后断点续采）」。此时应停止，等一段时间后再用默认方式续跑，**不要反复重试**。
- **遇到验证码 / 登录拦截 / 安全验证页**：程序会保存截图与 HTML 到 `debug/`，记录日志并暂停。**请勿尝试强行绕过滑块或验证码**，等待恢复即可。
- **`code=37 环境异常` 的常见原因**：未登录、登录态过期、未通过安全校验、或访问过快。先执行 `python relogin.py` 刷新登录态，并保持低频。
- **不要短时间大量重跑**：同一账号短时间内高频访问极易触发限制，建议分批、隔段时间采集。
- **想更快铺数据量**：可用 `--no-detail` 跳过详情请求，整体请求数更少，触发风控概率更低。

---

## 🚧 采集策略说明

BOSS 直聘对「未登录 / 未通过安全校验」的自动化访问会返回 `code=37 环境异常`。
本项目实测跑通的链路是：

1. **登录**：用户手动扫码一次，`wt2` 等登录态经 Playwright `storage_state` 持久化。
2. **安全校验会话**：在真实浏览器中完成站点标准的安全校验握手，获取访问公开接口所需的会话凭证。
3. **采集**：携带登录态与凭证，通过浏览器内 `fetch` 调用官方公开接口（`joblist.json` / `detail.json`）。
4. **映射与去重**：`mapper.py` 映射字段，`exporter.py` 按多级键去重写入 CSV。

> 纯 HTTP 请求会被 `code=37` 直接拦截，因此本项目采用「真实浏览器内 fetch」而非裸 `requests`。
> 整个过程保持低频、单实例，尊重网站访问频率。

---

## 🗺 路线图

- **第二阶段**：珠三角 9 城 × 多关键词 × 分页 × 断点续采，目标 5000~10000 条。
- **第三阶段**：公司与岗位数据关联，引入 MySQL 存储。
- **第四阶段**：对岗位描述做技术栈抽取（Java / Python / LLM / RAG 等），分析城市 / 薪资 / 学历与技术栈的关系。

---

## 📄 License

本项目以 [MIT License](./LICENSE) 开源。请遵守上方的合规与使用声明。

---

## ❓ 常见问题

**Q：为什么必须登录？**
A：BOSS 直聘的搜索页与接口需要先通过登录与安全校验才能访问，未登录会被 `code=37` 拦截。
本项目使用你本人的账号手动扫码登录，仅访问公开数据。

**Q：数据从哪里来？**
A：全部来自 BOSS 直聘公开可访问的搜索结果与岗位详情，由程序实跑采集，绝无假数据。

**Q：会触发风控吗？**
A：已内置随机等待、单实例单页面、不并发等友好策略；若仍遇到验证码 / 登录拦截，
程序会保存证据并暂停，请稍后断点续采，切勿尝试强行绕过。
