# -*- coding: utf-8 -*-
"""CSV 导出 + 基础去重。

对应需求文档第十三、十四节：
- 字段缺失留空，不删除整条记录。
- 去重优先级：job_id -> job_url -> job_name+company_name+city。
"""
import csv
import os
import datetime

import config
from crawler import logger


def _dedup_key(job):
    """按优先级返回去重键。"""
    job_id = (job.get("job_id") or "").strip()
    if job_id:
        return f"id:{job_id}"
    job_url = (job.get("job_url") or "").strip()
    if job_url:
        return f"url:{job_url}"
    return "name:{}|{}|{}".format(
        job.get("job_name") or "",
        job.get("company_name") or "",
        job.get("city") or "",
    )


class CsvExporter:
    def __init__(self, path=None):
        self.path = path or config.CSV_PATH
        self._keys = set()
        self._total = 0
        self._load_existing()

    def _load_existing(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    key = _dedup_key(row)
                    if key:
                        self._keys.add(key)
                    self._total += 1
            logger.info(f"已载入现有 CSV，共 {self._total} 条")
        except Exception as e:
            logger.warn(f"读取现有 CSV 失败: {e}")

    def add_many(self, jobs):
        """写入一批岗位，返回 (新增数, 重复数)。"""
        added = 0
        dup = 0
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        exists = os.path.exists(self.path) and os.path.getsize(self.path) > 0

        with open(self.path, "a", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=config.CSV_FIELDS)
            if not exists:
                writer.writeheader()
            for job in jobs:
                key = _dedup_key(job)
                if key in self._keys:
                    dup += 1
                    continue
                self._keys.add(key)
                row = {k: (job.get(k) or "") for k in config.CSV_FIELDS}
                row["crawl_time"] = row["crawl_time"] or datetime.datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                writer.writerow(row)
                added += 1
                self._total += 1

        return added, dup

    @property
    def total(self):
        return self._total
