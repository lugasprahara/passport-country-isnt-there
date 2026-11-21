#!/usr/bin/env python3
"""Render the passport spread of the Republic of Ilvara (a country that isn't there).

Draws one open passport spread — data page (left) and visas page (right) —
as a 1024x800 PNG using PIL. All names, dates and numbers are invented and
mutually consistent: every stamp falls after the issue date and before the
expiry date, and the machine-readable zone carries correct ICAO check digits.
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1024, 800
PAGE = 512  # each page is 512 wide

PAPER = (247, 242, 228)
PAPER_SHADE = (240, 233, 214)
NAVY = (29, 52, 102)
NAVY_SOFT = (52, 74, 122)
GOLD = (168, 132, 44)
GREY = (96, 96, 92)
DARK = (38, 38, 40)
TEAL_INK = (0, 110, 110)
PURPLE_INK = (88, 40, 138)
RED_INK = (168, 32, 40)
GREEN_INK = (24, 116, 62)

FD = "/usr/share/fonts/truetype/dejavu"


def font(name, size):
    return ImageFont.truetype(os.path.join(FD, name), size)


SERIF_B = lambda s: font("DejaVuSerif-Bold.ttf", s)
SERIF = lambda s: font("DejaVuSerif.ttf", s)
SERIF_I = lambda s: ImageFont.truetype(
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf", s)
SANS = lambda s: font("DejaVuSans.ttf", s)
SANS_B = lambda s: font("DejaVuSans-Bold.ttf", s)
MONO = lambda s: font("DejaVuSansMono.ttf", s)


def tracked(draw, xy, text, fnt, fill, tracking=0, anchor_left=True):
    """Draw text with manual letter tracking; returns total width."""
    x, y = xy
    total = 0
    for ch in text:
        draw.text((x + total, y), ch, font=fnt, fill=fill)
        total += draw.textlength(ch, font=fnt) + tracking
    return total - tracking if text else 0


def tracked_center(draw, cx, y, text, fnt, fill, tracking=0):
    total = sum(draw.textlength(ch, font=fnt) + tracking for ch in text) - tracking
    tracked(draw, (cx - total / 2, y), text, fnt, fill, tracking)
    return total


# ---------------------------------------------------------------- MRZ (ICAO 9303)
def _char_value(ch):
    if ch.isdigit():
        return int(ch)
    if ch == "<":
        return 0
    return ord(ch) - 55  # A=10 .. Z=35


def mrz_check_digit(data):
    weights = (7, 3, 1)
    total = sum(_char_value(c) * weights[i % 3] for i, c in enumerate(data))
    return str(total % 10)


def build_mrz():
    line1 = "P<ILVVELMAR<<ANA<SOREN"
    line1 = line1 + "<" * (44 - len(line1))
    doc = "I4821706<"  # 9 chars incl. filler
    dob, expiry = "910314", "320602"
    personal = "9103142217" + "<" * 4  # 14 chars
    l2 = doc + mrz_check_digit(doc)
    l2 += "ILV"
    l2 += dob + mrz_check_digit(dob)
    l2 += "F"
    l2 += expiry + mrz_check_digit(expiry)
    l2 += personal + mrz_check_digit(personal)
    composite_src = l2[0:10] + l2[13:20] + l2[21:28] + l2[28:43]
    l2 += mrz_check_digit(composite_src)
    assert len(line1) == 44 and len(l2) == 44, (line1, l2)
    return line1, l2


# ---------------------------------------------------------------- coat of arms
def draw_arms(size=92):
    """Shield with a lighthouse over waves, a star above. Navy + gold on paper."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size / 100.0
    # shield outline
    shield = [(18, 8), (82, 8), (82, 52), (50, 94), (18, 52)]
    d.polygon(shield, fill=(233, 238, 246, 255), outline=NAVY + (255,), width=max(2, int(3 * s)))
    d.line([(18, 30), (82, 30)], fill=GOLD + (255,), width=max(1, int(2 * s)))
    # star
    cx, cy, r = 50, 19, 7
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
    d.polygon([(x * s, y * s) for x, y in pts], fill=GOLD + (255,))
    # lighthouse: tapered tower with lamp room, on rocks
    d.polygon([(44 * s, 78 * s), (47 * s, 46 * s), (53 * s, 46 * s), (56 * s, 78 * s)], fill=NAVY + (255,))
    d.rectangle([45 * s, 40 * s, 55 * s, 46 * s], fill=GOLD + (255,))
    d.rectangle([47 * s, 34 * s, 53 * s, 40 * s], fill=NAVY + (255,))
    d.polygon([(50 * s, 29 * s), (45 * s, 34 * s), (55 * s, 34 * s)], fill=NAVY + (255,))
    # light beams
    d.line([(45 * s, 37 * s), (34 * s, 33 * s)], fill=GOLD + (255,), width=max(1, int(2 * s)))
    d.line([(55 * s, 37 * s), (66 * s, 33 * s)], fill=GOLD + (255,), width=max(1, int(2 * s)))
    # waves
    for k, yy in enumerate((82, 88)):
        pts = []
        for x in range(24, 77, 2):
            pts.append((x * s, (yy + 2.2 * math.sin((x - 24) / 6.5 + k * 1.6)) * s))
        d.line(pts, fill=NAVY_SOFT + (255,), width=max(1, int(2 * s)))
    return img


# ---------------------------------------------------------------- portrait
def draw_portrait(w=304, h=480):
    """A neat studio ID portrait, drawn as flat shapes with soft shading."""
    img = Image.new("RGB", (w, h), (176, 190, 205))
    d = ImageDraw.Draw(img)
    # backdrop: gentle vertical gradient
    for y in range(h):
        t = y / h
        c = tuple(int((196 - 40 * t) * 1.0) if i == 2 else int(198 - 34 * t) for i in range(3))
        d.line([(0, y), (w, y)], fill=(int(186 - 30 * t), int(196 - 30 * t), int(210 - 26 * t)))
    cx = w // 2
    skin = (232, 184, 142)
    skin_shade = (214, 160, 118)
    hair = (74, 52, 38)
    # shoulders / jacket (harbour-service teal) with white blouse
    d.polygon([(cx - 118, h), (cx - 96, h - 128), (cx - 40, h - 168), (cx + 40, h - 168),
               (cx + 96, h - 128), (cx + 118, h)], fill=(38, 74, 88))
    d.polygon([(cx - 34, h), (cx, h - 148), (cx + 34, h)], fill=(240, 238, 232))
    d.polygon([(cx - 34, h), (cx, h - 148), (cx - 6, h)], fill=(226, 224, 216))
    # a small gold lighthouse pin on the lapel — she is a keeper of the light
    d.ellipse([cx + 52, h - 96, cx + 62, h - 86], fill=GOLD)
    d.rectangle([cx + 55, h - 104, cx + 59, h - 95], fill=GOLD)
    # neck
    d.rectangle([cx - 22, h - 208, cx + 22, h - 148], fill=skin_shade)
    d.rectangle([cx - 22, h - 190, cx + 22, h - 148], fill=skin)
    # ears
    d.ellipse([cx - 74, h - 268, cx - 56, h - 224], fill=skin)
    d.ellipse([cx + 56, h - 268, cx + 74, h - 224], fill=skin)
    # face
    d.ellipse([cx - 62, h - 348, cx + 62, h - 178], fill=skin)
    d.pieslice([cx - 62, h - 348, cx + 62, h - 178], 20, 160, fill=skin)  # jaw softening
    # hair: swept back, covering the crown and sides
    d.pieslice([cx - 66, h - 362, cx + 66, h - 196], 180, 360, fill=hair)
    d.pieslice([cx - 66, h - 356, cx + 66, h - 210], 175, 250, fill=hair)
    d.pieslice([cx - 66, h - 356, cx + 66, h - 210], 290, 365, fill=hair)
    d.ellipse([cx - 66, h - 300, cx - 48, h - 210], fill=hair)
    d.ellipse([cx + 48, h - 300, cx + 66, h - 210], fill=hair)
    # hairline sheen
    d.arc([cx - 58, h - 350, cx + 58, h - 220], 200, 320, fill=(104, 78, 56), width=3)
    # eyebrows
    d.arc([cx - 44, h - 262, cx - 14, h - 240], 190, 340, fill=(70, 48, 32), width=4)
    d.arc([cx + 14, h - 262, cx + 44, h - 240], 200, 350, fill=(70, 48, 32), width=4)
    # eyes — small, level, with an eyelid line so they read as a photo, not a cartoon
    for ex in (cx - 29, cx + 29):
        d.ellipse([ex - 9, h - 244, ex + 9, h - 234], fill=(250, 250, 248))
        d.ellipse([ex - 4, h - 244, ex + 4, h - 234], fill=(52, 44, 38))
        d.ellipse([ex - 1.5, h - 242, ex + 1.5, h - 237], fill=(16, 14, 12))
        d.arc([ex - 10, h - 248, ex + 10, h - 234], 180, 360, fill=(70, 48, 32), width=2)
    # nose: soft shadow line
    d.line([(cx + 1, h - 232), (cx - 3, h - 208)], fill=skin_shade, width=3)
    d.arc([cx - 9, h - 210, cx + 9, h - 198], 20, 160, fill=skin_shade, width=3)
    # mouth
    d.arc([cx - 17, h - 190, cx + 17, h - 168], 15, 165, fill=(168, 84, 74), width=4)
    d.line([(cx - 14, h - 179), (cx + 14, h - 179)], fill=(178, 96, 84), width=3)
    # gentle cheek shading
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    od.ellipse([cx - 56, h - 226, cx - 20, h - 196], fill=(226, 150, 110, 46))
    od.ellipse([cx + 20, h - 226, cx + 56, h - 196], fill=(226, 150, 110, 46))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    # printed-photo grain
    img = img.filter(ImageFilter.GaussianBlur(0.4))
    return img


# ---------------------------------------------------------------- stamps
def _stamp_canvas(w, h, draw_fn, ink):
    c = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    draw_fn(d, w, h, ink)
    return c


def oval_stamp(lines, ink, w=320, h=118):
    def fn(d, W, H, ink):
        a = ink + (215,)
        d.ellipse([4, 4, W - 4, H - 4], outline=a, width=4)
        d.ellipse([11, 11, W - 11, H - 11], outline=a, width=2)
        y = 20
        for i, (txt, fnt) in enumerate(lines):
            tracked_center(d, W / 2, y, txt, fnt, a, tracking=1)
            y += fnt.size + 5
    return _stamp_canvas(w, h, fn, ink)


def rect_stamp(lines, ink, w=300, h=104):
    def fn(d, W, H, ink):
        a = ink + (215,)
        d.rectangle([4, 4, W - 4, H - 4], outline=a, width=4)
        d.rectangle([10, 10, W - 10, H - 10], outline=a, width=1)
        y = 17
        for txt, fnt in lines:
            tracked_center(d, W / 2, y, txt, fnt, a, tracking=1)
            y += fnt.size + 5
    return _stamp_canvas(w, h, fn, ink)


def round_stamp(lines, ink, r=66):
    size = r * 2 + 12

    def fn(d, W, H, ink):
        a = ink + (215,)
        d.ellipse([6, 6, W - 6, H - 6], outline=a, width=4)
        d.ellipse([13, 13, W - 13, H - 13], outline=a, width=1)
        y = H / 2 - sum(f.size for _, f in lines) / 2 - 4
        for txt, fnt in lines:
            tracked_center(d, W / 2, y, txt, fnt, a, tracking=0)
            y += fnt.size + 3
    return _stamp_canvas(size, size, fn, ink)


def paste_rot(base, stamp, center, angle):
    rot = stamp.rotate(angle, expand=True, resample=Image.BICUBIC)
    x = int(center[0] - rot.width / 2)
    y = int(center[1] - rot.height / 2)
    base.alpha_composite(rot, (x, y))


# ---------------------------------------------------------------- page furniture
def guilloche(page):
    """Pale woven arcs — security-print texture, kept very light."""
    ov = Image.new("RGBA", page.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    ink = (70, 120, 140, 16)
    for cx, cy in ((-140, -120), (660, -80), (240, 920), (700, 900)):
        for r in range(60, 560, 26):
            d.ellipse([cx - r, cy - r * 0.62, cx + r, cy + r * 0.62], outline=ink, width=1)
    ink2 = (150, 120, 50, 12)
    for i in range(0, 900, 9):
        pts = [(x, 640 + i * 0.12 + 8 * math.sin(x / 46 + i)) for x in range(0, 513, 8)]
        d.line(pts, fill=ink2, width=1)
    return Image.alpha_composite(page, ov)


def field(d, x, y, label_en, label_il, value, value_font=None, w=None):
    tracked(d, (x, y), label_en.upper(), SANS(10), GREY, tracking=1)
    if label_il:
        d.text((x + d.textlength(label_en.upper(), font=SANS(10)) + len(label_en) * 1 + 8, y),
               "/ " + label_il, font=SERIF_I(10), fill=GREY)
    d.text((x, y + 15), value, font=value_font or SANS_B(19), fill=DARK)


def main():
    img = Image.new("RGBA", (W, H), PAPER + (255,))
    # per-page shading: right page a touch deeper, centre seam shadow
    d0 = ImageDraw.Draw(img, "RGBA")
    d0.rectangle([PAGE, 0, W, H], fill=PAPER_SHADE + (255,))
    for i in range(26):
        a = int(52 * (1 - i / 26))
        d0.line([(PAGE - 13 + i, 0), (PAGE - 13 + i, H)], fill=(60, 55, 40, a))
        d0.line([(PAGE + 13 - i, 0), (PAGE + 13 - i, H)], fill=(255, 255, 255, int(a * 0.5)))

    left = guilloche(img.crop((0, 0, PAGE, H)))
    right = guilloche(img.crop((PAGE, 0, W, H)))
    img.paste(left, (0, 0))
    img.paste(right, (PAGE, 0))
    d = ImageDraw.Draw(img, "RGBA")

    # ================= LEFT PAGE — data page =================
    arms = draw_arms(92)
    img.alpha_composite(arms, (30, 26))
    d = ImageDraw.Draw(img, "RGBA")
    tracked(d, (136, 36), "REPUBLIC OF ILVARA", SERIF_B(25), NAVY, tracking=0)
    tracked(d, (139, 72), "RESPUBLIKA ILVARA", SANS(14), NAVY_SOFT, tracking=4)
    tracked(d, (139, 97), "PASSPORT · PASPUT", SANS_B(13), GOLD, tracking=3)
    d.line([(30, 126), (482, 126)], fill=GOLD + (255,), width=3)
    d.line([(30, 131), (482, 131)], fill=NAVY + (160,), width=1)

    field(d, 30, 142, "Type", "Tip", "P")
    field(d, 120, 142, "Code", "Koda", "ILV")
    field(d, 232, 142, "Passport No.", "Št. pasputa", "I4821706")

    # portrait
    photo = draw_portrait().resize((152, 240), Image.LANCZOS)
    img.paste(photo, (30, 186))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([30, 186, 182, 426], outline=NAVY_SOFT + (255,), width=2)
    # ghost image (security reprint of the portrait, faded)
    ghost = draw_portrait().resize((64, 100), Image.LANCZOS).convert("RGBA")
    ghost.putalpha(88)
    img.alpha_composite(ghost, (116, 322))
    d = ImageDraw.Draw(img, "RGBA")

    fx = 200
    field(d, fx, 186, "Surname", "Priimek", "VELMAR")
    field(d, fx, 238, "Given names", "Imena", "ANA SOREN")
    field(d, fx, 290, "Nationality", "Državljanstvo", "ILVARAN")
    field(d, fx, 342, "Date of birth", "Datum rojstva", "14 MAR 1991")
    field(d, 392, 342, "Sex", "Spol", "F")
    field(d, fx, 394, "Place of birth", "Kraj rojstva", "SELMARIS")

    field(d, 30, 452, "Date of issue", "Datum izdaje", "02 JUN 2022")
    field(d, 262, 452, "Date of expiry", "Velja do", "02 JUN 2032")
    field(d, 30, 504, "Authority", "Organ izdaje",
          "MINISTRY OF THE INTERIOR — SELMARIS", value_font=SANS_B(15))
    field(d, 30, 556, "Personal No.", "Osebna št.", "910314 2217")
    d.text((262, 556 + 15), "A. Velmar", font=SERIF_I(22), fill=(40, 40, 90))
    tracked(d, (262, 556), "HOLDER'S SIGNATURE / PODPIS", SANS(10), GREY, tracking=1)

    d.text((30, 622), "This passport contains 32 pages. It is the property of the",
           font=SANS(10), fill=GREY)
    d.text((30, 636), "Republic of Ilvara and must be surrendered on demand.",
           font=SANS(10), fill=GREY)

    line1, line2 = build_mrz()
    d.text((30, 700), line1, font=MONO(17), fill=(30, 30, 30))
    d.text((30, 730), line2, font=MONO(17), fill=(30, 30, 30))

    # ================= RIGHT PAGE — visas =================
    rx = PAGE + 30
    tracked(d, (rx, 34), "VISAS", SERIF_B(24), NAVY, tracking=3)
    tracked(d, (rx + 108, 42), "· VIZE · VISA", SANS(13), NAVY_SOFT, tracking=2)
    d.text((W - 58, 34), "8", font=SERIF_B(20), fill=NAVY_SOFT)
    d.line([(rx, 76), (W - 30, 76)], fill=GOLD + (255,), width=3)
    d.line([(rx, 81), (W - 30, 81)], fill=NAVY + (160,), width=1)

    # printed endorsement box — the telling detail of paperwork
    box = (rx, 96, W - 30, 208)
    d.rectangle(box, outline=NAVY + (255,), width=2)
    d.rectangle((box[0] + 5, box[1] + 5, box[2] - 5, box[3] - 5), outline=NAVY + (140,), width=1)
    tracked(d, (rx + 16, 108), "ENDORSEMENT · ZAZNAMEK", SANS_B(12), NAVY, tracking=2)
    body = ("The bearer is licensed keeper of the Selmaris Light and, while "
            "travelling on the Service's business, is exempt from harbour "
            "dues in all ports of the Republic.")
    words, lines, cur = body.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=SERIF(12.5)) > 420:
            lines.append(cur)
            cur = w_
        else:
            cur = t
    lines.append(cur)
    y = 130
    for ln in lines:
        d.text((rx + 16, y), ln, font=SERIF(12.5), fill=DARK)
        y += 17
    d.text((rx + 16, 186), "Ministry of the Interior — Selmaris, 02 JUN 2022",
           font=SERIF_I(11), fill=GREY)

    # stamps — a plausible travel history, all within validity
    s_arr = oval_stamp([("KINGDOM OF DREVANIA", SANS_B(13)),
                        ("★ PORT KESSIG ★", SANS(11)),
                        ("ARRIVAL  18 SEP 2023", SANS_B(13))], PURPLE_INK)
    paste_rot(img, s_arr, (778, 292), -6)
    s_dep = oval_stamp([("KINGDOM OF DREVANIA", SANS_B(13)),
                        ("★ PORT KESSIG ★", SANS(11)),
                        ("DEPARTURE  02 OCT 2023", SANS_B(13))], PURPLE_INK)
    paste_rot(img, s_dep, (694, 398), 4)
    fee = rect_stamp([("HARBOUR FEE PAID", SANS_B(12)),
                      ("25 SOLI · SELMARIS", SANS(11)),
                      ("11 AUG 2023", SANS_B(12))], GREEN_INK, w=252, h=92)
    paste_rot(img, fee, (872, 452), 7)
    s_kh_in = rect_stamp([("UNION OF KHARAT", SANS_B(13)),
                          ("KHARAT CITY AIRPORT", SANS(11)),
                          ("ADMITTED  07 FEB 2024", SANS_B(12))], RED_INK)
    paste_rot(img, s_kh_in, (782, 528), -3)
    s_kh_out = rect_stamp([("UNION OF KHARAT", SANS_B(13)),
                           ("DEPARTED  21 FEB 2024", SANS_B(12))], RED_INK, w=284, h=88)
    paste_rot(img, s_kh_out, (672, 622), 5)
    s_cal = round_stamp([("CALDERA", SANS_B(12)),
                         ("PUERTO CALDER", SANS(9)),
                         ("ARRIVED", SANS(9)),
                         ("30 MAY 2025", SANS_B(10)),
                         ("BY SEA", SANS(9))], TEAL_INK, r=64)
    paste_rot(img, s_cal, (596, 540), -9)
    s_home = round_stamp([("ILVARA", SANS_B(12)),
                          ("SELMARIS", SANS(9)),
                          ("FERRY PORT", SANS(9)),
                          ("RETURNED", SANS(9)),
                          ("14 JUN 2025", SANS_B(10))], NAVY, r=64)
    paste_rot(img, s_home, (902, 616), 8)

    d = ImageDraw.Draw(img, "RGBA")
    d.text((rx, 706), "Condition of travel — the bearer, being a lightkeeper of the",
           font=SERIF_I(12), fill=(70, 70, 66))
    d.text((rx, 723), "Republic, must return to her light within forty days of departure.",
           font=SERIF_I(12), fill=(70, 70, 66))
    d.text((rx, 752), "Pages 8–27 are reserved for visas and endorsements.",
           font=SANS(10), fill=GREY)

    out = os.environ.get("ENTRY_OUT", "entry.png")
    img.convert("RGB").save(out, optimize=True)
    print("wrote", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
