#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从上游仓库找出"版本号最大"的正式/预发布版本 tag。

上游 release 里混着 test-diag59 / test-msrebuild1 / notices 这类非版本 tag,
也有正文说明用的 release, 所以必须按语义化版本过滤 + 排序, 不能直接取"最新发布"。

输出到 stdout: tag 名 (如 v1.0.9-alpha05), 没有可用版本时输出空并 exit 1。
"""

import json
import os
import re
import sys
import urllib.request

UPSTREAM = os.environ.get("UPSTREAM_REPO", "GrahamZen/izuko-tv")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

SEMVER = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:-([A-Za-z]+)\.?(\d+))?$")
STAGE = {"alpha": 0, "beta": 1, "rc": 2}


def sort_key(tag: str):
    m = SEMVER.match(tag)
    if not m:
        return None
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    pre, num = m.group(4), int(m.group(5) or 0)
    # 正式版排在预发布之后: (major, minor, patch, stage, prenum)
    stage = 3 if pre is None else STAGE.get(pre.lower(), 0)
    return (major, minor, patch, stage, num)


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
    best = None
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
            k = sort_key(tag)
            if k is None:
                continue
            if best is None or k > best[0]:
                best = (k, tag, r.get("prerelease", False))
        page += 1

    if best is None:
        print("上游没有符合语义化版本的 release", file=sys.stderr)
        return 1

    _, tag, pre = best
    # 第一行给 shell 用, 第二行给 workflow 判断是否预发布
    print(tag)
    print("prerelease" if pre else "stable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
