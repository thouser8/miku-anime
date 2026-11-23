#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从上游仓库找出"最近发布"的版本 tag (alpha / beta / 正式版都算)。

两个坑:
  1. 上游 release 里混着 test-diag59 / test-msrebuild1 / notices 这类非版本 tag, 必须按语义化版本过滤。
  2. 上游仓库继承了 Animeko 的历史 6.x tag (2026 年 7-9 月), 那是旧产品线,
     所以不能按"版本号最大"取 —— 必须按发布时间取最新的语义化 tag。
"""

import json
import os
import re
import sys
import urllib.request

UPSTREAM = os.environ.get("UPSTREAM_REPO", "GrahamZen/izuko-tv")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

SEMVER = re.compile(r"^v?\d+\.\d+\.\d+(?:-[A-Za-z]+\.?\d*)?$")


def fetch(url: str):
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "miku-anime-autobuild",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    cands = []
    page = 1
    while page <= 3:
        try:
            releases = fetch(
                f"https://api.github.com/repos/{UPSTREAM}/releases?per_page=100&page={page}"
            )
        except Exception as e:  # 网络抖动不该导致误判"没有新版本"
            print(f"查询上游 release 失败: {e}", file=sys.stderr)
            return 1
        if not releases:
            break
        for r in releases:
            if r.get("draft"):
                continue
            tag = r.get("tag_name", "")
            if not SEMVER.match(tag):
                continue
            cands.append((r.get("published_at") or "", tag, r.get("prerelease", False)))
        page += 1

    if not cands:
        print("上游没有符合语义化版本的 release", file=sys.stderr)
        return 1

    # published_at 是 ISO8601, 字典序即时间序
    cands.sort(key=lambda x: x[0], reverse=True)
    _, tag, pre = cands[0]
    print(tag)
    print("prerelease" if pre else "stable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
