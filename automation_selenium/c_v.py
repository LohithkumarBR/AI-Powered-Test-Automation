import json
import base64
import os
import time
import math
from io import BytesIO

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image, ImageDraw, ImageFont


# ---------------------------------------
# Utilities
# ---------------------------------------

def measure_text(draw, text, font):
    if hasattr(draw, "textbbox"):
        l, t, r, b = draw.textbbox((0, 0), text, font=font)
        return r - l, b - t
    return font.getsize(text)


def rects_intersect(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 < bx1 or ax1 > bx2 or ay2 < by1 or ay1 > by2)



def draw_corner_notch(draw, x, y, size, color):

    draw.line([x, y, x + size, y], fill=color, width=3)
    draw.line([x, y, x, y + size], fill=color, width=3)



def annotate_screenshot(screenshot_b64, nodes, output_path):
    img = Image.open(BytesIO(base64.b64decode(screenshot_b64))).convert("RGB")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("tahomabd.ttf", 10)
    except:
        font = ImageFont.load_default()

    COLORS = [
        (255, 0, 0),
        (0, 128, 255),
        (0, 180, 0),
        (255, 140, 0),
        (148, 0, 211),
        (0, 180, 180),
        (180, 0, 0),
        (255, 105, 180),
    ]

    TAG_PADDING = 4   

    used_tag_rects = []

    element_boxes = [
        (
            int(n["bbox"]["x"]),
            int(n["bbox"]["y"]),
            int(n["bbox"]["x"] + n["bbox"]["w"]),
            int(n["bbox"]["y"] + n["bbox"]["h"]),
        )
        for n in nodes
    ]

    def rects_intersect(a, b):
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        return not (ax2 < bx1 or ax1 > bx2 or ay2 < by1 or ay1 > by2)

    def inside_screen(rect):
        x1, y1, x2, y2 = rect
        return x1 >= 0 and y1 >= 0 and x2 <= img.width and y2 <= img.height


    def find_free_tag_position(box, tag_w, tag_h):
        bx1, by1, bx2, by2 = box
        cx = (bx1 + bx2) // 2
        cy = (by1 + by2) // 2

        max_radius = 120
        step = 6

        for radius in range(6, max_radius, step):
            for angle in range(0, 360, 30):
                rad = math.radians(angle)
                lx = int(cx + radius * math.cos(rad) - tag_w // 2)
                ly = int(cy + radius * math.sin(rad) - tag_h // 2)

                rect = (
                    lx - TAG_PADDING,
                    ly - TAG_PADDING,
                    lx + tag_w + TAG_PADDING,
                    ly + tag_h + TAG_PADDING,
                )

                if not inside_screen(rect):
                    continue

                
                if any(rects_intersect(rect, b) for b in element_boxes):
                    continue

            
                if any(rects_intersect(rect, t) for t in used_tag_rects):
                    continue

                used_tag_rects.append(rect)
                return lx, ly

        
        lx = max(0, bx1 - tag_w - 10)
        ly = max(0, by1 - tag_h - 10)
        used_tag_rects.append((lx, ly, lx + tag_w, ly + tag_h))
        return lx, ly

    
    for i, item in enumerate(nodes):
        color = COLORS[i % len(COLORS)]
        label = item["ff"].split("-")[-1]

        x1 = int(item["bbox"]["x"])
        y1 = int(item["bbox"]["y"])
        x2 = int(item["bbox"]["x"] + item["bbox"]["w"])
        y2 = int(item["bbox"]["y"] + item["bbox"]["h"])

        draw.rectangle([x1, y1, x2, y2], outline=color, width=2)

        
        tw, th = measure_text(draw, label, font)
        tag_w = max(18, tw + 6)
        tag_h = max(14, th + 4)

        
        lx, ly = find_free_tag_position((x1, y1, x2, y2), tag_w, tag_h)

      
        draw.rectangle(
            [lx, ly, lx + tag_w, ly + tag_h],
            fill=(255, 255, 255),
            outline=color,
            width=2
        )

        tx = lx + (tag_w - tw) // 2
        ty = ly + (tag_h - th) // 2
        draw.text((tx, ty), label, fill=color, font=font)

        # connector line (edge-safe)
        tag_cx = lx + tag_w // 2
        tag_cy = ly + tag_h // 2

        box_cx = (x1 + x2) // 2
        box_cy = (y1 + y2) // 2

        if tag_cx < x1:
            line_start = (lx + tag_w, tag_cy)
            line_end = (x1, box_cy)
        elif tag_cx > x2:
            line_start = (lx, tag_cy)
            line_end = (x2, box_cy)
        elif tag_cy < y1:
            line_start = (tag_cx, ly + tag_h)
            line_end = (box_cx, y1)
        else:
            line_start = (tag_cx, ly)
            line_end = (box_cx, y2)

        draw.line([line_start, line_end], fill=color, width=2)

    img.save(output_path)
    print(f"[INFO] Saved {output_path}")





JS_VISIBLE_FUNCTION = """
function isReallyVisible(n) {
    const r = n.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return false;

    const cx = r.x + r.width / 2;
    const cy = r.y + r.height / 2;

    let topEl = document.elementFromPoint(cx, cy);
    if (!topEl) return false;

    return n === topEl || n.contains(topEl);
}
"""

JS_PRIMARY = """
return (function() {

    %s

   function isPrimary(n) {
    const tag = n.tagName.toLowerCase();
    const text = (n.innerText || "").trim();
    const style = window.getComputedStyle(n);

    if (["input", "button", "select", "textarea"].includes(tag))
        return true;

    if (tag === "label" && text.length > 0)
        return true;

    if (tag === "a" && text.length > 0)
        return true;

    if (tag === "li") {
        if (text.length > 0 && style.cursor === "pointer")
            return true;
    }

    return false;
}
    function getBBox(n) {
        const r = n.getBoundingClientRect();
        return {x:r.x, y:r.y, w:r.width, h:r.height};
    }

    function collectShadowAware(root, out) {
        if (!root) return;

        if (root.nodeType === Node.ELEMENT_NODE && root.hasAttribute("ff-inspect"))
            out.push(root);

        for (const child of root.children) {
            collectShadowAware(child, out);
            if (child.shadowRoot) collectShadowAware(child.shadowRoot, out);
        }
    }

    const all = [];
    collectShadowAware(document.documentElement, all);

    const out = [];

    for (let n of all) {
        if (isReallyVisible(n) && isPrimary(n)) {
            out.push({
                ff: n.getAttribute("ff-inspect"),
                xpath: n.getAttribute("ff-xpath"),
                bbox: getBBox(n),
                tag: n.tagName.toLowerCase(),
                text: (n.innerText || "").trim()
            });
        }
    }

    return out;
})();
""" % JS_VISIBLE_FUNCTION



JS_SECONDARY = """
return (function() {

    %s

    function isSecondary(n) {
        const r = n.getBoundingClientRect();
        const tag = n.tagName.toLowerCase();
        const text = (n.innerText || "").trim();
        const style = window.getComputedStyle(n);

        if (r.y < 120 && text.length > 0 && text.length <= 12)
            return true;

        if (["div", "span"].includes(tag)) {
            if (text.length > 0 && text.length <= 20 && r.height > 10)
                return true;
            if (style.cursor === "pointer")
                return true;
        }

        if (tag === "li") {
            if (text.length > 0 || style.cursor === "pointer")
                return true;
        }

        return false;
    }

    function getBBox(n) {
        const r = n.getBoundingClientRect();
        return {x:r.x, y:r.y, w:r.width, h:r.height};
    }

    function collectShadowAware(root, out) {
        if (!root) return;

        if (root.nodeType === Node.ELEMENT_NODE && root.hasAttribute("ff-inspect"))
            out.push(root);

        for (const child of root.children) {
            collectShadowAware(child, out);
            if (child.shadowRoot) collectShadowAware(child.shadowRoot, out);
        }
    }

    const all = [];
    collectShadowAware(document.documentElement, all);

    const out = [];

    for (let n of all) {
        if (isReallyVisible(n) && isSecondary(n)) {
            out.push({
                ff: n.getAttribute("ff-inspect"),
                xpath: n.getAttribute("ff-xpath"),
                bbox: getBBox(n),
                tag: n.tagName.toLowerCase(),
                text: (n.innerText || "").trim()
            });
        }
    }

    return out;
})();
""" % JS_VISIBLE_FUNCTION




def generate_annotated_screenshots(driver, output_dir="screenshots"):
    os.makedirs(output_dir, exist_ok=True)

    # print("[INFO] Injecting ff attributes...")
    # driver.execute_script(INJECT_FF)
    # time.sleep(1)

    screenshot_b64 = driver.get_screenshot_as_base64()

    print("[INFO] Extracting primary elements...")
    primary = driver.execute_script(JS_PRIMARY)
    print(f"[INFO] Primary count: {len(primary)}")

    primary_ids = set(item["ff"] for item in primary)

    primary_path = os.path.join(output_dir, "annotated_primary.png")
    annotate_screenshot(screenshot_b64, primary, primary_path)

    print("[INFO] Extracting secondary elements...")
    secondary = driver.execute_script(JS_SECONDARY)
    secondary = [item for item in secondary if item["ff"] not in primary_ids]

    print(f"[INFO] Secondary count (filtered): {len(secondary)}")

    secondary_path = os.path.join(output_dir, "annotated_secondary.png")
    annotate_screenshot(screenshot_b64, secondary, secondary_path)

    print("[INFO] Completed annotated screenshots.")

