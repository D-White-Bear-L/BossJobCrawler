# -*- coding: utf-8 -*-
"""把 joblist.json / detail.json 的原始字段映射到 CSV 字段。

字段名基于 BossWork 已验证的接口返回结构；公司 id / 公司 URL / 地址等
字段若接口未提供，保持为空（需求文档：缺失留空，不伪造）。
"""
import config


def _join(items):
    if not items:
        return ""
    if isinstance(items, list):
        return "|".join(str(x) for x in items if x)
    return str(items)


def job_to_row(job, detail, keyword, city, crawl_time=""):
    """job: 列表接口单条；detail: 详情 dict 或 None。"""
    info = {}
    boss_info = {}
    if detail and detail.get("code") == 0:
        zp = detail.get("zpData") or {}
        info = zp.get("jobInfo") or {}
        boss_info = zp.get("bossInfo") or {}

    merged = {**job, **info}

    job_id = job.get("encryptJobId") or info.get("encryptId") or ""
    brand_id = job.get("encryptBrandId") or job.get("brandId") or info.get("encryptBrandId") or ""

    job_url = f"https://www.zhipin.com/job_detail/{job_id}.html" if job_id else ""
    company_url = f"https://www.zhipin.com/gongsir/{brand_id}.html" if brand_id else ""

    # job_tags = 技术栈（skills）；jobLabels 是经验/学历标签，已由 experience/education 覆盖
    skills = merged.get("skills") or merged.get("showSkills") or []
    job_tags = _join(skills)

    return {
        "job_id": job_id,
        "job_name": merged.get("jobName") or "",
        "job_url": job_url,
        "salary": merged.get("salaryDesc") or merged.get("salary") or "",
        "city": merged.get("cityName") or "",
        "district": merged.get("areaDistrict") or "",
        "experience": merged.get("jobExperience") or merged.get("experienceName") or "",
        "education": merged.get("jobDegree") or merged.get("degreeName") or "",
        "job_tags": job_tags,
        "job_description": (merged.get("postDescription") or "").strip(),
        "company_id": brand_id,
        "company_name": merged.get("brandName") or "",
        "company_url": company_url,
        "company_industry": merged.get("brandIndustry") or merged.get("industryName") or "",
        "company_scale": merged.get("brandScaleName") or merged.get("scaleName") or "",
        "company_financing": merged.get("brandStageName") or merged.get("stageName") or "",
        "company_address": merged.get("locationName") or merged.get("address") or "",
        "company_description": merged.get("brandDescription") or "",
        "recruiter_name": merged.get("bossName") or boss_info.get("name") or "",
        "recruiter_title": merged.get("bossTitle") or boss_info.get("title") or "",
        "source_keyword": keyword,
        "source_city": city,
        "crawl_time": crawl_time,
    }
