#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载科目一完整题库 JSON 到本地（不下载图片，图片走外部 CDN）。

数据源：GitHub 开源项目 doupoa/DrivingTestSubjectOne
       原始题库来自 banban驾道，对应公安部 GA/T 1575 标准
       （《机动车驾驶人考试内容和方法》），最后更新 2022/07/17
分支：main
文件：q.json（含科目一 2545 题 + 科目四 1833 题）

图片策略：题目 url 字段为外部 CDN（app.static.public.chetailian.com），
          网页直接引用该 URL，不在本地缓存图片，保持项目轻量。

运行：
    python3 scripts/fetch_bank.py
产出：
    data/q.json          —— 原始完整题库（如已存在则跳过下载）
    data/raw_bank.json   —— 仅科目一子集（供 classify.py 使用）
"""
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
Q_PATH = os.path.join(DATA_DIR, "q.json")
RAW_PATH = os.path.join(DATA_DIR, "raw_bank.json")

Q_URLS = [
    "https://cdn.jsdelivr.net/gh/doupoa/DrivingTestSubjectOne@main/q.json",
    "https://fastly.jsdelivr.net/gh/doupoa/DrivingTestSubjectOne@main/q.json",
    "https://gcore.jsdelivr.net/gh/doupoa/DrivingTestSubjectOne@main/q.json",
    "https://raw.githubusercontent.com/doupoa/DrivingTestSubjectOne/main/q.json",
]

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def http_get(url, timeout=60, retries=3):
    import time
    last_err = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(1.0 * (i + 1))
    raise RuntimeError(f"GET 失败 {url}: {last_err}")


def ensure_qjson():
    os.makedirs(DATA_DIR, exist_ok=True)
    if os.path.exists(Q_PATH) and os.path.getsize(Q_PATH) > 1_000_000:
        print(f"  ✓ 已存在缓存: {Q_PATH} ({os.path.getsize(Q_PATH)/1024/1024:.1f} MB)")
        return
    last_err = None
    for url in Q_URLS:
        try:
            print(f"  尝试: {url}")
            raw = http_get(url, timeout=180)
            data = json.loads(raw.decode("utf-8"))
            if isinstance(data, list) and data:
                with open(Q_PATH, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
                print(f"  ✓ 成功，共 {len(data)} 条记录 ({os.path.getsize(Q_PATH)/1024/1024:.1f} MB)")
                return
        except Exception as e:  # noqa: BLE001
            print(f"    失败: {e}")
            last_err = e
    raise RuntimeError(f"所有数据源均失败: {last_err}")


def main():
    print("=" * 60)
    print("科目一题库准备工具（图片走外部 CDN，不下载图片）")
    print("数据源: doupoa/DrivingTestSubjectOne (banban驾道原始数据)")
    print("对应标准: 公安部 GA/T 1575《机动车驾驶人考试内容和方法》")
    print("题库更新日期: 2022/07/17")
    print("=" * 60)

    print("\n[1/2] 确保题库 JSON 已就绪 ...")
    ensure_qjson()

    print("\n[2/2] 抽取科目一子集 ...")
    with open(Q_PATH, encoding="utf-8") as f:
        all_data = json.load(f)

    bank = [x for x in all_data if x.get("subject") == 1]
    judge = sum(1 for x in bank if x.get("type") == 3)
    single = sum(1 for x in bank if x.get("type") == 1)
    with_img = sum(1 for x in bank if (x.get("url") or "").strip())

    print(f"  科目一: 共 {len(bank)} 题 (判断题 {judge} / 单选题 {single})")
    print(f"  含图题: {with_img} 道 (网页将通过外部 CDN 加载)")

    # CDN 域名核验
    from urllib.parse import urlparse
    domains = {}
    for x in bank:
        u = (x.get("url") or "").strip()
        if u:
            host = urlparse(u if u.startswith("http") else "http:" + u).netloc
            domains[host] = domains.get(host, 0) + 1
    print(f"  图片 CDN 域名: {domains}")

    with open(RAW_PATH, "w", encoding="utf-8") as f:
        json.dump(bank, f, ensure_ascii=False)
    print(f"\n科目一子集已保存: {RAW_PATH}")
    print("下一步: 运行 classify.py 生成标准题库 + 章节 + 时效标记")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断")
        sys.exit(130)
