# -*- coding: utf-8 -*-
"""断点续采：记录已完成的「城市|关键词|页码」，中断后下次跳过已完成部分。"""
import json
import os

import config


class Checkpoint:
    def __init__(self, path=None):
        self.path = path or config.STATE_PATH
        self.completed = set()
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    d = json.load(f)
                self.completed = set(d.get("completed", []))
            except Exception:
                self.completed = set()

    def is_done(self, key):
        return key in self.completed

    def mark_done(self, key):
        self.completed.add(key)
        self._save()

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        data = {"completed": sorted(self.completed)}
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
