#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建脚本：把 src/ 下的源码与 data/bank.json 题库打包成单文件 PWA。

输入（全部纳入版本管理）：
    src/index.template.html   页面骨架（含 __CSS__ / __APP_JS__ / __BANK_JSON__ / __BUILD_VER__ 占位符）
    src/style.css             样式
    src/app.js                应用逻辑
    src/sw.template.js        Service Worker（含 __BUILD_VER__ 占位符）
    data/bank.json            标准题库

输出（.gitignore 忽略，CI 自动重建）：
    index.html  manifest.json  sw.js  icon-192.png  icon-512.png  favicon.png

设计：
- 题库以 JS 变量内联（window.__BANK__），避免 file:// 协议下 fetch 被 CORS 拦截
- CSS / JS 内联进 index.html，单文件零依赖
- 图片走外部 CDN 绝对 URL，由 Service Worker 懒缓存

运行: python3 scripts/build_html.py
依赖: Python 3.6+，图标生成需 Pillow（pip install Pillow，缺失时跳过图标）
"""
import json
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
BANK = os.path.join(ROOT, "data", "bank.json")
OUT_HTML = os.path.join(ROOT, "index.html")
OUT_MANIFEST = os.path.join(ROOT, "manifest.json")
OUT_SW = os.path.join(ROOT, "sw.js")
OUT_ICON_192 = os.path.join(ROOT, "icon-192.png")
OUT_ICON_512 = os.path.join(ROOT, "icon-512.png")
OUT_FAVICON = os.path.join(ROOT, "favicon.png")

# 构建版本号（用于 Service Worker 缓存失效）
BUILD_VER = time.strftime("%Y%m%d%H%M%S")

# 模板占位符
PLACEHOLDERS = ("__CSS__", "__APP_JS__", "__BANK_JSON__", "__BUILD_VER__")


def read_src(name):
    with open(os.path.join(SRC, name), encoding="utf-8") as f:
        return f.read()


def main():
    with open(BANK, encoding="utf-8") as f:
        bank = json.load(f)
    # 紧凑 JSON，减少体积
    bank_json = json.dumps(bank, ensure_ascii=False, separators=(",", ":"))

    template = read_src("index.template.html")
    css = read_src("style.css")
    app_js = read_src("app.js")
    sw_template = read_src("sw.template.js")

    # 安全检查：源码中不得含占位符文本，否则替换会互相污染
    for name, content in [("style.css", css), ("app.js", app_js)]:
        for ph in PLACEHOLDERS:
            if ph in content:
                raise SystemExit(f"构建中止：src/{name} 中不允许出现占位符 {ph}")
    # 内联 JS 中不得出现 "</script"，否则会提前闭合 script 标签
    if "</script" in app_js.lower():
        raise SystemExit("构建中止：src/app.js 中含有 '</script'，会破坏内联 script 标签")

    # 先替换结构性占位符，最后内联题库（题库内容不再参与任何替换）
    html = (template
            .replace("__BUILD_VER__", BUILD_VER)
            .replace("__CSS__", css)
            .replace("__APP_JS__", app_js)
            .replace("__BANK_JSON__", bank_json))

    for ph in ("__CSS__", "__APP_JS__", "__BANK_JSON__", "__BUILD_VER__"):
        if ph in html:
            raise SystemExit(f"构建中止：占位符 {ph} 未被完全替换")

    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    # manifest.json
    manifest = {
        "name": "C1 驾照 · 科目一模拟考试",
        "short_name": "科目一",
        "description": "智能刷题 + 模拟考试，SM-2 间隔重复算法精选，离线可用",
        "start_url": ".",
        "scope": ".",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#f7f8fa",
        "theme_color": "#1e80ff",
        "lang": "zh-CN",
        "icons": [
            {"src": "icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
            {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"}
        ]
    }
    with open(OUT_MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # sw.js
    sw_js = sw_template.replace("__BUILD_VER__", BUILD_VER)
    if "__BUILD_VER__" in sw_js:
        raise SystemExit("构建中止：sw.template.js 中 __BUILD_VER__ 未被完全替换")
    with open(OUT_SW, "w", encoding="utf-8") as f:
        f.write(sw_js)

    # PWA 图标（用 Pillow 生成；无 Pillow 时跳过，保留已存在的图标）
    try:
        generate_icons()
    except ImportError:
        print("提示: 未安装 Pillow，跳过图标生成（保留现有图标文件）")

    size_kb = os.path.getsize(OUT_HTML) / 1024
    print(f"已生成: {OUT_HTML}")
    print(f"  题库: {len(bank)} 题")
    print(f"  体积: {size_kb:.1f} KB ({size_kb/1024:.2f} MB)")
    print(f"已生成: {OUT_MANIFEST}")
    print(f"已生成: {OUT_SW}  (缓存版本: {BUILD_VER})")
    print(f"构建版本: {BUILD_VER}")


def generate_icons():
    """用 Pillow 生成 PWA 图标：蓝紫渐变背景 + 白色简化汽车。"""
    from PIL import Image, ImageDraw

    BLUE = (30, 128, 255)
    BLUE_DARK = (22, 96, 216)
    WHITE = (255, 255, 255)

    def lerp(a, b, t):
        return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

    def make_icon(size, path):
        S = size * 4  # 超采样抗锯齿
        img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        # 背景填满纯色（maskable 安全区）
        img.paste(BLUE, (0, 0, S, S))
        # 渐变叠加
        grad = Image.new("RGBA", (S, S))
        gp = grad.load()
        for y in range(S):
            for x in range(S):
                t = (x + y) / (2 * S)
                gp[x, y] = lerp(BLUE, BLUE_DARK, t) + (255,)
        img = Image.alpha_composite(img, grad)
        draw = ImageDraw.Draw(img)

        cx, cy = S / 2, S / 2
        w = S * 0.56
        h = S * 0.38
        left = cx - w / 2
        right = cx + w / 2
        top = cy - h / 2
        bottom = cy + h / 2
        body_top = top + h * 0.28

        # 车身
        draw.rounded_rectangle([left, body_top, right, bottom], radius=h * 0.18, fill=WHITE)
        # 驾驶舱
        cabin_l, cabin_r = left + w * 0.20, right - w * 0.20
        draw.polygon([
            (cabin_l + w * 0.06, body_top), (cabin_r - w * 0.06, body_top),
            (cabin_r - w * 0.16, top + h * 0.02), (cabin_l + w * 0.16, top + h * 0.02)
        ], fill=WHITE)
        # 车窗
        draw.polygon([
            (cabin_l + w * 0.15, body_top - S * 0.005), (cabin_r - w * 0.15, body_top - S * 0.005),
            (cabin_r - w * 0.19, top + h * 0.05), (cabin_l + w * 0.19, top + h * 0.05)
        ], fill=BLUE_DARK)
        # 车轮
        wheel_r = w * 0.10
        wheel_y = bottom - S * 0.005
        for wx in (left + w * 0.24, right - w * 0.24):
            draw.ellipse([wx - wheel_r, wheel_y - wheel_r * 0.7, wx + wheel_r, wheel_y + wheel_r * 0.7], fill=BLUE_DARK)
            hub_r = wheel_r * 0.4
            draw.ellipse([wx - hub_r, wheel_y - hub_r * 0.7, wx + hub_r, wheel_y + hub_r * 0.7], fill=WHITE)

        img.resize((size, size), Image.LANCZOS).save(path, "PNG")

    make_icon(192, OUT_ICON_192)
    make_icon(512, OUT_ICON_512)
    make_icon(32, OUT_FAVICON)
    print("已生成: icon-192.png / icon-512.png / favicon.png")


if __name__ == "__main__":
    main()
