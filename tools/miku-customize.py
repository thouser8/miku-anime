#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Miku 动画定制脚本 —— 在 Animeko / Izuko TV 源码树上重放全部个人定制。

设计原则:
  1. 幂等: 同一份源码反复跑, 结果一致。
  2. 上游无关: 不假设上游某文件的内容, 只做定向替换; 上游改了结构时尽力匹配, 匹配不上就报错退出,
     绝不让"看起来构建成功但定制丢了"的包发出去。
  3. 分层: 静态资源(图标/横幅/字体实现/镜像清单)放 miku-assets/overlay 直接覆盖;
     需要改上游既有代码的(改名/砍工单/版本配置)在本脚本里做字符串处理。

用法:
    python3 tools/miku-customize.py <源码根目录> --version 1.0.9-alpha05
"""

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

APP_NAME_SIMPLE = "Miku动画"
APP_NAME_TRAD = "Miku動畫"
APP_NAME_EN = "Miku Anime"

# 需要先删除的上游文件(与 overlay 里的同名资源冲突, 或功能已砍掉)
DELETE_FILES = [
    "app/shared/src/androidMain/res/drawable/ic_launcher_foreground.xml",
    "app/shared/src/androidMain/res/drawable/ic_launcher_monochrome.xml",
    "app/installer/src/main/res/drawable/ic_launcher_foreground.xml",
    "app/installer/src/main/res/drawable/ic_launcher_monochrome.xml",
    # tv_banner: XML 换成 PNG, 同名不同后缀会资源冲突
    "app/android/src/izukoTv/res/drawable/tv_banner.xml",
    "app/installer/src/main/res/drawable/tv_banner.xml",
]
DELETE_DIRS = [
    "tools/ticket-worker",
]

OK, WARN, FAIL = [], [], []


def ok(msg):
    OK.append(msg)
    print(f"  [OK]   {msg}")


def warn(msg):
    WARN.append(msg)
    print(f"  [WARN] {msg}")


def fail(msg):
    FAIL.append(msg)
    print(f"  [FAIL] {msg}")


def read(p):
    return Path(p).read_text(encoding="utf-8")


def write(p, text):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(text, encoding="utf-8", newline="\n")


def step_delete(src):
    """删除与 overlay 冲突的上游资源 + 已砍掉的功能目录"""
    print("[1/6] 删除冲突资源")
    for rel in DELETE_FILES:
        p = src / rel
        if p.exists():
            p.unlink()
            ok(f"删除 {rel}")
        else:
            warn(f"不存在, 跳过 {rel}")
    for rel in DELETE_DIRS:
        p = src / rel
        if p.is_dir():
            shutil.rmtree(p)
            ok(f"删除目录 {rel}")
        else:
            warn(f"目录不存在, 跳过 {rel}")


def step_overlay(src, overlay):
    """把 miku-assets/overlay 整棵树覆盖到源码树"""
    print("[2/6] 覆盖定制资源")
    if not overlay.is_dir():
        fail(f"overlay 目录不存在: {overlay}")
        return
    n = 0
    for base, _, files in os.walk(overlay):
        for f in files:
            s = Path(base) / f
            rel = s.relative_to(overlay)
            d = src / rel
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(s, d)
            n += 1
    ok(f"覆盖 {n} 个文件")


def step_rename(src):
    """全部 strings.xml 里的应用名改掉。简述: values-zh-rHK / values-zh-rTW 用繁体名。"""
    print("[3/6] 改应用名")
    changed = 0
    for p in sorted(src.rglob("res/values*/strings.xml")):
        try:
            t = read(p)
        except (UnicodeDecodeError, OSError):
            continue
        if "Izuko" not in t:
            continue
        trad = "zh-rHK" in str(p) or "zh-rTW" in str(p)
        zh = trad or "values-zh" in str(p) or "zh-rCN" in str(p)
        if trad:
            name = APP_NAME_TRAD
        elif zh:
            name = APP_NAME_SIMPLE
        else:
            name = APP_NAME_EN
        # 先长后短, 避免 "Izuko TV" 被拆成 "Miku动画 TV"
        t2 = t.replace("Izuko TV", name).replace("Izuko", name)
        if t2 != t:
            write(p, t2)
            changed += 1
    if changed:
        ok(f"改名 {changed} 个 strings.xml")
    else:
        fail("没有任何 strings.xml 被改名, 上游可能改了应用名的写法")


def step_gradle_props(src, version, repo):
    print("[4/6] 改版本与更新指向")
    p = src / "gradle.properties"
    if not p.exists():
        fail("gradle.properties 不存在")
        return
    t = read(p)
    t = re.sub(r"(?m)^ani\.repository=.*$", f"ani.repository={repo}", t)
    t = re.sub(r"(?m)^ani\.update\.asset\.prefix=.*$", "ani.update.asset.prefix=miku", t)
    t = re.sub(r"(?m)^version\.name=.*$", f"version.name={version}", t)
    write(p, t)
    ok(f"ani.repository={repo}, prefix=miku, version.name={version}")


def step_channel(src):
    """默认更新渠道改成 ALPHA, 否则正式版渠道看不到 alpha 包"""
    print("[5/6] 默认更新渠道 -> ALPHA")
    cands = list(src.rglob("preference/UpdateSettings.kt"))
    if not cands:
        warn("找不到 UpdateSettings.kt, 应用内需手动把渠道切到 alpha")
        return
    p = cands[0]
    t = read(p)
    t2, n = re.subn(
        r"(val releaseClass: ReleaseClass = ReleaseClass\.)STABLE",
        r"\1ALPHA",
        t,
    )
    if n:
        write(p, t2)
        ok(f"releaseClass 默认改为 ALPHA ({p.relative_to(src)})")
    else:
        warn("UpdateSettings 里没匹配到 STABLE 默认值, 应用内需手动切渠道")


def step_kill_tickets(src):
    """砍工单: 只删引用, 保留定义(未使用的 internal 常量不影响编译, 也不怕上游重构)"""
    print("[6/6] 砍工单系统")

    # --- 6.1 手机控制台页面里的反馈样式/脚本引用 ---
    page = src / "app/shared/ui-tv/src/commonMain/kotlin/ui/remote/RemoteControlPage.kt"
    if page.exists():
        t = read(page)
        orig = t
        for const in ("FEEDBACK_STYLE", "FEEDBACK_SET_ROW", "FEEDBACK_SET_GROUP", "FEEDBACK_SCRIPT"):
            t = t.replace(f' + "\\n" + {const}', "")
        t = re.sub(r"(?m)^[ \t]*if \(g === 'feedback' && window\.loadFeedback\)[^\n]*\n", "", t)
        if t != orig:
            write(page, t)
            left = len(re.findall(r"FEEDBACK_", t))
            ok(f"RemoteControlPage 去掉反馈页引用 (残留定义引用 {left} 处, 属正常)")
        else:
            warn("RemoteControlPage 没匹配到反馈引用, 上游可能已重构")
    else:
        fail("RemoteControlPage.kt 不存在")

    # --- 6.2 控制台的 /api/feedback 路由 ---
    ctl = src / "app/shared/ui-tv/src/commonMain/kotlin/ui/remote/TvRemoteControl.kt"
    if ctl.exists():
        t = read(ctl)
        orig = t
        # 请求体上限里的 RemoteFeedback 分支
        t = t.replace(" ?: RemoteFeedback.maxBodyBytes(path)", "")
        # when 分支: 从 path == "api/feedback" 起, 到该分支的 status(405...) 行结束
        lines = t.splitlines(True)
        i = 0
        removed = 0
        while i < len(lines):
            if 'path == "api/feedback"' in lines[i]:
                start = i
                if start > 0 and lines[start - 1].lstrip().startswith("//"):
                    start -= 1
                end = i
                while end < len(lines) and "status(405" not in lines[end]:
                    end += 1
                del lines[start:end + 1]
                removed += 1
                i = start
                continue
            i += 1
        t = "".join(lines)
        if t != orig:
            write(ctl, t)
            ok(f"TvRemoteControl 去掉 /api/feedback 路由 ({removed} 个分支)")
        else:
            warn("TvRemoteControl 没匹配到反馈路由")

    # --- 6.3 网页控制台的 i18n 文案 ---
    i18n = src / "app/shared/ui-tv/src/commonMain/kotlin/ui/remote/RemoteI18nTable.kt"
    if i18n.exists():
        t = read(i18n)
        t2 = t.replace(" + feedbackTexts()", "")
        if t2 != t:
            write(i18n, t2)
            ok("RemoteI18nTable 去掉 feedbackTexts()")
        else:
            warn("RemoteI18nTable 没匹配到 feedbackTexts()")

    # --- 6.4 TV 设置的「我的反馈」入口 ---
    entry = src / "app/shared/ui-settings-catalog/src/commonMain/kotlin/ui/settings/tv/TvSettingsEntriesApp.kt"
    if entry.exists():
        t = read(entry)
        lines = t.splitlines(True)
        kept, dropped = [], 0
        for ln in lines:
            if re.match(r"^\s*feedbackItems\(\)\s*$", ln):
                dropped += 1
                continue
            kept.append(ln)
        t2 = "".join(kept)
        # 文档注释里的指向也顺手清掉
        t2 = re.sub(r"\s*\(见 feedbackItems\)", "", t2)
        if dropped:
            write(entry, t2)
            ok(f"TV 设置去掉「我的反馈」入口 ({dropped} 行)")
        else:
            warn("TV 设置没匹配到 feedbackItems() 调用")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="源码根目录")
    ap.add_argument("--version", required=True, help="版本名, 如 1.0.9-alpha05")
    ap.add_argument("--repo", default="thouser8/miku-anime", help="应用内更新指向的仓库 owner/name")
    ap.add_argument("--assets", default=None, help="miku-assets 目录, 默认脚本同级 ../miku-assets")
    args = ap.parse_args()

    src = Path(args.src).resolve()
    if not (src / "gradle.properties").exists():
        print(f"不是有效的源码目录: {src}", file=sys.stderr)
        return 2

    assets = Path(args.assets) if args.assets else (Path(__file__).resolve().parent.parent / "miku-assets")
    overlay = assets / "overlay"

    print(f"== Miku 定制: {src}  版本={args.version} ==")
    step_delete(src)
    step_overlay(src, overlay)
    step_rename(src)
    step_gradle_props(src, args.version, args.repo)
    step_channel(src)
    step_kill_tickets(src)

    print(f"\n== 结果: OK={len(OK)} WARN={len(WARN)} FAIL={len(FAIL)} ==")
    if FAIL:
        print("\n失败项:", file=sys.stderr)
        for m in FAIL:
            print("  - " + m, file=sys.stderr)
        return 1
    if WARN:
        print("\n警告项(不阻塞构建, 但请确认是否符合预期):")
        for m in WARN:
            print("  - " + m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
