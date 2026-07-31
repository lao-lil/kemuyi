#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将原始科目一题库规范化为标准题库。

输入: data/raw_bank.json  (2545题，原始字段)
输出: data/bank.json      (规范化+去重+过滤地方题+章节分类+时效修正)

字段规范（网页直接消费）:
{
  "id":         原始id
  "type":       "judge" | "single"
  "question":   题干
  "image":      图片CDN绝对URL（无图则为null）
  "options":    ["正确","错误"] 或 ["选项A内容",...]
  "answer":     正确答案在 options 中的索引（0-based）
  "explain":    解析（answerSkillExplain 优先，其次 answerSkill）
  "law":        法条原文（remark 字段，可能含HTML）
  "category":   章节分类 law/signal/safety/operation/case
  "updated":    是否已按2025新规修订（bool）
}

运行: python3 scripts/classify.py
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw_bank.json")
OUT = os.path.join(ROOT, "data", "bank.json")


# ---------- 章节分类（基于关键词集合，按优先级匹配）----------
# 每类一组关键词，命中任一即归类；顺序代表优先级（signal 优先于 safety 优先于 operation 优先于 law）
CATEGORY_KEYWORDS = [
    # 交通信号：标志、标线、信号灯、手势
    ("signal", [
        "标志", "标线", "信号灯", "交通信号", "交警手势", "指挥手势",
        "指示标志", "警告标志", "禁令标志", "指路标志", "旅游区标志",
        "黄灯", "红灯", "绿灯", "倒计时", "导向车道", "导向箭头",
        "禁止驶入", "禁止通行", "禁止鸣喇叭", "禁止掉头", "禁止超车",
        "禁止停车", "禁止长时停车", "禁止临时停车",
        "解除限速", "最低限速", "最高限速", "限速",
        "注意行人", "注意儿童", "注意牲畜", "注意横风", "注意落石",
        "注意交叉路口", "注意隧道", "注意窄路", "注意桥梁", "注意陡坡",
        "注意双向交通", "注意施工", "注意事故", "注意冰雪",
        "连续下坡", "路面不平", "注意渡口", "驼峰桥",
        "人行横道预告", "菱形", "反向弯路", "急弯路", "堤坝路",
        "傍山险路", "过水路面",
        "指示标线", "禁止标线", "警告标线", "虚实线", "双黄线",
        "导流线", "网状线", "减速让行", "停车让行", "会车让行",
    ]),
    # 驾驶操作基础：车辆构造、仪表、装置
    ("operation", [
        "仪表", "仪表盘", "转速表", "时速表", "水温表", "燃油表", "油压", "机油",
        "驻车制动", "行车制动", "发动机制动", "ABS", "EBD", "ESP", "TCS",
        "制动踏板", "油门", "加速踏板", "离合器", "方向盘", "换挡", "挡位",
        "手刹", "变速器", "雨刮", "刮水器", "后视镜",
        "远光灯", "近光灯", "雾灯", "示廓灯", "转向灯", "危险报警闪光灯",
        "倒车灯", "位置灯", "灯光开关",
        "座椅", "头枕", "安全带", "儿童安全座椅", "儿童锁", "天窗",
        "车门", "引擎盖", "后备箱", "风挡", "轮胎", "胎压", "备胎",
        "千斤顶", "电瓶", "蓄电池", "发电机",
        "点火开关", "一键启动", "预热", "熄火", "挂挡", "空挡",
        "新能源", "充电", "动力电池", "纯电动", "插电", "混合动力",
        "这个开关", "这个仪表", "这个灯", "这是什么操纵", "点火",
    ]),
    # 安全文明驾驶：驾驶行为、特殊情况、应急、急救
    ("safety", [
        "让行", "礼让", "超车", "会车", "跟车", "倒车", "掉头", "转弯",
        "并线", "变更车道", "夜间行驶", "夜间会车", "危险报警闪光灯",
        "大雨", "暴雨", "阵雨", "台风", "雾天", "冰雪路面", "结冰",
        "泥泞", "涉水", "大风", "紧急制动", "急打方向", "急转向",
        "侧滑", "抱死", "爆胎", "失控", "翻车", "起火", "自燃",
        "发动机温度", "发动机过热", "水温", "转向失灵", "转向失控",
        "制动失灵", "制动失效", "制动延长", "避险", "应急", "急救",
        "伤员", "止血", "骨折", "搬运", "烧伤", "中毒",
        "安全距离", "安全车距", "跟车距离", "盲区", "内轮差",
        "制动距离", "反应距离", "实习期", "疲劳驾驶", "酒后", "醉酒",
        "酒驾", "毒驾", "分心", "玩手机", "安全气囊", "文明驾驶",
        "防御性驾驶", "安全驾驶", "高速公路行驶", "隧道行驶",
    ]),
    # 法律法规规章：记分、罚款、驾驶证、登记、事故处理
    ("law", [
        "记分", "累计记分", "记分周期", "满分", "12分", "9分", "6分",
        "3分", "2分", "1分", "罚款", "暂扣", "吊销", "注销", "撤销",
        "扣留", "收缴", "拘留", "追究刑事责任",
        "申领", "准驾车型", "准驾年龄", "增驾", "初次申领",
        "换证", "补证", "审验", "身体条件", "年审", "有效期",
        "注册登记", "转移登记", "变更登记", "抵押登记", "机动车登记",
        "交通事故", "肇事", "逃逸", "现场", "抢救", "报警",
        "快速理赔", "自行协商",
        "驾驶证", "行驶证", "号牌", "车牌", "检验合格标志",
        "保险标志", "交强险", "交通管理", "车辆管理", "车管所",
        "高速公路", "城市快速路", "应急车道", "行车道", "超车道",
        "匝道", "服务区", "收费站", "最高时速", "最低时速",
        "节假日免费", "公交车", "校车", "出租车", "货运", "载货",
        "载客", "危险品", "化学品", "特种车辆",
        "实习标志", "三力测试", "周岁", "元以下", "元以上",
    ]),
]


def classify(question, explain):
    """返回章节分类。按优先级匹配关键词。"""
    text = (question or "") + " " + (explain or "")
    for cat, keywords in CATEGORY_KEYWORDS:
        for kw in keywords:
            if kw in text:
                return cat
    return "case"  # 兜底：案例与综合


def strip_html(s):
    """去除 remark 字段的 HTML 标签，转纯文本。"""
    if not s:
        return ""
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"&nbsp;", " ", s)
    s = re.sub(r"&[a-z]+;", "", s)
    return s.strip()


def normalize_url(u):
    """规范化图片 URL 为绝对地址。"""
    u = (u or "").strip()
    if not u:
        return None
    if u.startswith("//"):
        return "http:" + u
    if not u.startswith("http"):
        return "http://" + u
    return u


# ---------- 时效性修正（2022.7 → 2026.6）----------
# 受 2025.1 公安部第172号令影响：大中型客货车年龄上限 60→63周岁
# C6轻型牵引挂车：原 20-60，现为 20-70周岁
# 这些是确定性修正，基于公安部官网172号令原文
TIME_FIXES = {
    # (题干子串, 原答案index, 新答案index, 新解析)
    # 题目：申请大型客车驾驶证，应在26周岁以上，50周岁以下。
    # 原答案：错误（原解析：22-60周岁）—— 2026仍为"错误"，但解析需更新为22-63
    "申请大型客车驾驶证的申请人，应该在26周岁以上，50周岁以下": {
        "answer": 1,  # 仍为"错误"
        "explain": "根据公安部第172号令（2025年1月1日施行），申请大型客车（A1）、重型牵引挂车（A2）准驾车型的，年龄条件为22周岁以上、63周岁以下。",
        "updated": True,
    },
    # 题目：申请增驾轻型牵引挂车驾驶证的人年龄条件是多少？ 选项含 20-60 和 20-70
    # 2026正确应为 20-70周岁，需把答案指向含"70"的选项
    "申请增驾轻型牵引挂车驾驶证的人年龄条件是多少": {
        "explain": "根据公安部第172号令（2025年1月1日施行），增驾轻型牵引挂车（C6）准驾车型，年龄条件为20周岁以上、70周岁以下。",
        "updated": True,
        "fix_answer_to_text": "70周岁以下",  # 把答案指向包含此文字的选项
    },
    # 注意：下面这道题问的是"取得资格几年以上"，不是年龄，不修正
}

# 注意：C6相关修正只针对"年龄条件"类题目，避免误伤"几年资格/核发时长/记分要求"等题


def apply_time_fixes(item, q):
    """应用时效修正。返回 (是否修正, item)。"""
    for key, fix in TIME_FIXES.items():
        if key in q:
            if "explain" in fix:
                item["explain"] = fix["explain"]
            if "answer" in fix:
                item["answer"] = fix["answer"]
            # 按选项文字定位正确答案（用于选项本身已含新规答案的情况）
            if "fix_answer_to_text" in fix:
                target = fix["fix_answer_to_text"]
                for i, opt in enumerate(item["options"]):
                    if target in opt:
                        item["answer"] = i
                        break
            item["updated"] = True
            if "note" in fix:
                item["note"] = fix["note"]
            return True, item
    return False, item


def main():
    with open(RAW, encoding="utf-8") as f:
        raw = json.load(f)

    print(f"原始科目一题数: {len(raw)}")

    # 1) 只保留全国通用题（regionCode=0），过滤地方题
    nat = [x for x in raw if str(x.get("regionCode", "0")) == "0"]
    print(f"  过滤地方题后(全国): {len(nat)}")

    # 2) 规范化 + 去重（按题干+图片URL去重，保留第一条）
    seen = set()
    bank = []
    dropped_dup = 0
    for x in nat:
        q = (x.get("question") or "").strip()
        img = normalize_url(x.get("url"))
        # 去重key：题干 + 选项第一个，避免不同图片但题干选项完全一样的
        opts = x.get("itemsDescArray") or []
        key = q + "|" + (opts[0] if opts else "")
        if key in seen:
            dropped_dup += 1
            continue
        seen.add(key)

        titles = x.get("itemsTitleArray") or []
        ans_letter = x.get("answer")
        try:
            ans_idx = titles.index(ans_letter)
        except ValueError:
            continue  # 异常数据丢弃

        item = {
            "id": x.get("id"),
            "type": "judge" if x.get("type") == 3 else "single",
            "question": q,
            "image": img,
            "options": opts,
            "answer": ans_idx,
            "explain": (x.get("answerSkillExplain") or x.get("answerSkill") or "").strip(),
            "law": strip_html(x.get("remark")),
            "category": classify(q, x.get("answerSkillExplain") or x.get("answerSkill")),
            "updated": False,
        }

        # 时效修正
        _, item = apply_time_fixes(item, q)
        bank.append(item)

    print(f"  去重后: {len(bank)} (去除重复 {dropped_dup})")

    # 3) 统计
    from collections import Counter
    by_type = Counter(x["type"] for x in bank)
    by_cat = Counter(x["category"] for x in bank)
    with_img = sum(1 for x in bank if x["image"])
    updated = sum(1 for x in bank if x.get("updated"))
    print(f"\n题型: {dict(by_type)}")
    print(f"章节: {dict(by_cat)}")
    print(f"含图: {with_img}")
    print(f"按2025新规修订: {updated}")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(bank, f, ensure_ascii=False)
    print(f"\n标准题库已保存: {OUT} ({os.path.getsize(OUT)/1024:.1f} KB)")
    print("下一步: 编写 index.html")


if __name__ == "__main__":
    main()
