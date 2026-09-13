# -*- coding: utf-8 -*-
"""brand : ressources graphiques originales du rapport MERIDIAN.

Tout est dessiné ici : fond, marque, icônes de rail, silhouettes d'appareils.
Aucun logo ni marque figurative d'entreprise n'est reproduit.
"""
import math, os, random
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = None
ORANGE = (255, 102, 0)
VIOLET = (181, 124, 246)
TEAL   = (45, 212, 191)
INK    = (246, 244, 255)
DIM    = (139, 133, 168)
PANEL  = (35, 16, 63)

def _f(sz, bold=True):
    p = '/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf' % ('-Bold' if bold else '')
    try:
        return ImageFont.truetype(p, sz)
    except Exception:
        return ImageFont.load_default()

def save(im, name):
    im.save(os.path.join(OUT, name), 'PNG', optimize=True)
    return name

# ─────────────────────────── fond de page ───────────────────────────
def background(w=1600, h=900):
    """Nuit violette, meridiens et routes aeriennes. Dessin original."""
    base = (23, 10, 43)
    im = Image.new('RGB', (w, h), base)
    glow = Image.new('RGB', (w, h), base)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-420, -460, 820, 540], fill=(64, 28, 112))          # halo violet
    gd.ellipse([w - 700, h - 520, w + 380, h + 360], fill=(74, 32, 12))  # halo orange
    gd.ellipse([w * 0.38, -340, w * 0.96, 300], fill=(44, 20, 84))
    glow = glow.filter(ImageFilter.GaussianBlur(200))
    im = Image.blend(im, glow, 0.88)
    d = ImageDraw.Draw(im, 'RGBA')

    # globe en projection, en bas a droite
    cx, cy, R = w * 0.82, h * 1.04, 580
    for k in range(-6, 7):
        a = k / 6.0
        rx = R * abs(a) if a else 6
        pts = []
        for t in range(-90, 91, 3):
            y = cy - R * math.sin(math.radians(t))
            x = cx + rx * math.cos(math.radians(t)) * (1 if a >= 0 else -1)
            pts.append((x, y))
        d.line(pts, fill=(178, 130, 255, 30), width=1)
    for lat in range(-80, 81, 20):
        y = cy - R * math.sin(math.radians(lat))
        rr = R * math.cos(math.radians(lat))
        d.arc([cx - rr, y - rr * 0.16, cx + rr, y + rr * 0.16], 0, 360,
              fill=(178, 130, 255, 26), width=1)

    # routes aeriennes
    random.seed(7)
    for i in range(30):
        x1 = random.uniform(60, w - 60); y1 = random.uniform(70, h - 110)
        x2 = x1 + random.uniform(200, 660) * random.choice([-1, 1])
        y2 = y1 + random.uniform(-200, 200)
        x2 = max(40, min(w - 40, x2)); y2 = max(50, min(h - 50, y2))
        lift = random.uniform(56, 168)
        pts = []
        for t in [j / 44 for j in range(45)]:
            x = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * ((x1 + x2) / 2) + t ** 2 * x2
            y = (1 - t) ** 2 * y1 + 2 * (1 - t) * t * ((y1 + y2) / 2 - lift) + t ** 2 * y2
            pts.append((x, y))
        hot = (i % 3 == 0)
        d.line(pts, fill=((ORANGE + (46,)) if hot else (VIOLET + (26,))),
               width=2 if hot else 1)
        if hot:
            px, py = pts[int(len(pts) * 0.66)]
            d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=ORANGE + (170,))
    im = im.filter(ImageFilter.SMOOTH)
    v = Image.new('L', (w, h), 0)
    vd = ImageDraw.Draw(v)
    vd.ellipse([-w * 0.26, -h * 0.32, w * 1.26, h * 1.32], fill=196)
    v = v.filter(ImageFilter.GaussianBlur(160))
    dark = Image.new('RGB', (w, h), (14, 6, 27))
    return Image.composite(im, dark, v)

# ─────────────────────────── marque MERIDIAN ───────────────────────────
def mark(size=384):
    """Globe meridien traverse par une trajectoire ascendante. Dessin original."""
    S = size * 3
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    c = S / 2
    R = S * 0.385

    # disque : degrade violet profond vers violet clair
    disc = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    dd = ImageDraw.Draw(disc)
    for i in range(int(R), 0, -1):
        t = i / R
        col = (int(46 + 92 * (1 - t)), int(18 + 44 * (1 - t)), int(88 + 96 * (1 - t)), 255)
        dd.ellipse([c - i, c - i, c + i, c + i], fill=col)
    mask = Image.new('L', (S, S), 0)
    ImageDraw.Draw(mask).ellipse([c - R, c - R, c + R, c + R], fill=255)
    im.paste(disc, (0, 0), mask)

    d = ImageDraw.Draw(im)
    # meridiens
    for k in (0.32, 0.66):
        rr = R * k
        d.ellipse([c - rr, c - R, c + rr, c + R], outline=(226, 214, 255, 130),
                  width=max(2, S // 200))
    d.line([c - R, c, c + R, c], fill=(226, 214, 255, 130), width=max(2, S // 200))
    for k in (0.55,):
        yy = R * k
        d.arc([c - R, c - yy, c + R, c + yy], 0, 360, fill=(226, 214, 255, 100),
              width=max(2, S // 220))
    d.ellipse([c - R, c - R, c + R, c + R], outline=(255, 255, 255, 235), width=max(3, S // 110))

    # trajectoire orange
    pts = []
    for t in [j / 70 for j in range(71)]:
        x = c - R * 1.20 + t * (R * 2.46)
        y = c + R * 0.66 - math.sin(t * math.pi * 0.84) * R * 1.36
        pts.append((x, y))
    d.line(pts, fill=(12, 5, 24, 210), width=max(9, S // 30), joint='curve')
    d.line(pts, fill=ORANGE + (255,), width=max(6, S // 44), joint='curve')
    x2, y2 = pts[-1]; x1, y1 = pts[-7]
    a = math.atan2(y2 - y1, x2 - x1)
    L = S * 0.085
    d.polygon([(x2 + L * math.cos(a), y2 + L * math.sin(a)),
               (x2 + L * 0.52 * math.cos(a + 2.5), y2 + L * 0.52 * math.sin(a + 2.5)),
               (x2 + L * 0.52 * math.cos(a - 2.5), y2 + L * 0.52 * math.sin(a - 2.5))],
              fill=ORANGE + (255,))
    return im.resize((size, size), Image.LANCZOS)

def wordmark(w=640, h=150):
    im = Image.new('RGBA', (w * 2, h * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((0, 6), 'MERIDIAN', font=_f(int(h * 1.30)), fill=INK + (255,))
    d.text((6, int(h * 1.44)), 'FEDEX NETWORK INTELLIGENCE',
           font=_f(int(h * 0.40), False), fill=ORANGE + (255,))
    return im.resize((w, h), Image.LANCZOS)

# ─────────────────────────── pixels et bandes ───────────────────────────
def transparent(name, w=8, h=8):
    return save(Image.new('RGBA', (w, h), (0, 0, 0, 0)), name)

def accent(hexcol, name, w=64, h=8):
    c = tuple(int(hexcol.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4))
    return save(Image.new('RGBA', (w, h), c + (255,)), name)

# ─────────────────────────── icônes de rail ───────────────────────────
def _icon(kind, size=128, on=True):
    S = size * 3
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = ORANGE + (255,) if on else (150, 144, 180, 255)
    lw = max(4, S // 30)
    m = S * 0.17
    if kind == 'pulse':          # réseau / vue d'ensemble : nœuds reliés
        pts = [(0.5, 0.20), (0.20, 0.46), (0.80, 0.46), (0.32, 0.80), (0.68, 0.80)]
        for a, b in [(0, 1), (0, 2), (1, 3), (2, 4), (1, 2), (3, 4)]:
            d.line([pts[a][0] * S, pts[a][1] * S, pts[b][0] * S, pts[b][1] * S], fill=c, width=lw)
        for i, (px, py) in enumerate(pts):
            r = S * (0.075 if i == 0 else 0.048)
            d.ellipse([px * S - r, py * S - r, px * S + r, py * S + r], fill=c)
    elif kind == 'plane':        # avion vu de dessus
        d.polygon([(0.50, 0.10), (0.565, 0.30), (0.565, 0.44), (0.95, 0.63), (0.95, 0.72),
                   (0.565, 0.63), (0.565, 0.80), (0.68, 0.90), (0.68, 0.95), (0.50, 0.90),
                   (0.32, 0.95), (0.32, 0.90), (0.435, 0.80), (0.435, 0.63), (0.05, 0.72),
                   (0.05, 0.63), (0.435, 0.44), (0.435, 0.30)],
                  fill=c)
    elif kind == 'hub':          # cible / hub avec anneaux
        for r in (0.42, 0.28):
            d.ellipse([S * (0.5 - r), S * (0.5 - r), S * (0.5 + r), S * (0.5 + r)], outline=c, width=lw)
        d.ellipse([S * 0.40, S * 0.40, S * 0.60, S * 0.60], fill=c)
        for a in range(0, 360, 90):
            x = 0.5 + 0.50 * math.cos(math.radians(a)); y = 0.5 + 0.50 * math.sin(math.radians(a))
            d.line([S * 0.5, S * 0.5, S * x, S * y], fill=c, width=max(2, lw // 2))
    elif kind == 'truck':        # camion de livraison
        d.rounded_rectangle([S * 0.06, S * 0.32, S * 0.58, S * 0.68], radius=S * 0.04, fill=c)
        d.polygon([(S * 0.58, S * 0.40), (S * 0.78, S * 0.40), (S * 0.92, S * 0.54),
                   (S * 0.92, S * 0.68), (S * 0.58, S * 0.68)], fill=c)
        for cx in (0.26, 0.76):
            d.ellipse([S * (cx - 0.10), S * 0.62, S * (cx + 0.10), S * 0.82], fill=c)
            d.ellipse([S * (cx - 0.045), S * 0.675, S * (cx + 0.045), S * 0.765], fill=(10, 9, 18, 255))
    elif kind == 'leaf':         # feuille / climat
        d.polygon([(0.50 * S, 0.08 * S), (0.86 * S, 0.42 * S), (0.62 * S, 0.90 * S),
                   (0.38 * S, 0.90 * S), (0.14 * S, 0.42 * S)], fill=c)
        d.line([0.5 * S, 0.14 * S, 0.5 * S, 0.90 * S], fill=(10, 9, 18, 255), width=lw)
        for t in (0.34, 0.52, 0.70):
            d.line([0.5 * S, t * S, (0.5 + 0.24 * (1 - t)) * S + 0.10 * S, (t - 0.13) * S],
                   fill=(10, 9, 18, 255), width=max(2, lw - 2))
            d.line([0.5 * S, t * S, (0.5 - 0.24 * (1 - t)) * S - 0.10 * S, (t - 0.13) * S],
                   fill=(10, 9, 18, 255), width=max(2, lw - 2))
    elif kind == 'bolt':         # energie : eclair dans un hexagone
        d.polygon([(0.50 * S, 0.04 * S), (0.90 * S, 0.27 * S), (0.90 * S, 0.73 * S),
                   (0.50 * S, 0.96 * S), (0.10 * S, 0.73 * S), (0.10 * S, 0.27 * S)],
                  outline=c, width=lw)
        d.polygon([(0.56 * S, 0.18 * S), (0.30 * S, 0.54 * S), (0.47 * S, 0.54 * S),
                   (0.42 * S, 0.84 * S), (0.70 * S, 0.46 * S), (0.53 * S, 0.46 * S)], fill=c)
    elif kind == 'chart':        # finance : colonnes + flèche
        for i, (hh, ww) in enumerate([(0.30, 0.16), (0.50, 0.16), (0.72, 0.16)]):
            x = 0.12 + i * 0.24
            d.rounded_rectangle([S * x, S * (0.90 - hh), S * (x + ww), S * 0.90],
                                radius=S * 0.02, fill=c)
        d.line([S * 0.14, S * 0.34, S * 0.44, S * 0.20, S * 0.86, S * 0.10], fill=c, width=lw)
        d.polygon([(S * 0.92, S * 0.08), (S * 0.74, S * 0.08), (S * 0.86, S * 0.22)], fill=c)
    return im.resize((size, size), Image.LANCZOS)

# ─────────────────────────── silhouettes d'appareils ───────────────────────────
def aircraft(kind, w=200, h=200, colr=None):
    """Silhouette d'avion cargo vue de dessus, nez en haut. Dessin paramétrique original.

    Chaque famille a ses proportions : elancement du fuselage, envergure, fleche,
    nombre de nacelles, helices. Aucune image ni marque n'est reproduite.
    """
    S = 4
    W, Hh = w * S, h * S
    im = Image.new('RGBA', (W, Hh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    base = colr or (214, 208, 242)
    c = base + (255,)
    c2 = tuple(int(v * 0.70) for v in base) + (255,)
    dark = (10, 9, 18, 255)

    P = {
      # span, length, fuselage width, wing y, chord, sweep, engines(offsets), prop, tail span
      'wide2' : dict(sp=0.94, ln=0.94, fw=0.105, wy=0.42, ch=0.20, sw=0.30, eng=(0.36, 0.62),
                     prop=False, ts=0.36, tri=False),
      'wide3' : dict(sp=0.90, ln=0.96, fw=0.100, wy=0.43, ch=0.19, sw=0.29, eng=(0.40,),
                     prop=False, ts=0.34, tri=True),
      'narrow': dict(sp=0.72, ln=0.94, fw=0.078, wy=0.45, ch=0.16, sw=0.28, eng=(0.34,),
                     prop=False, ts=0.28, tri=False),
      'turbo' : dict(sp=0.92, ln=0.78, fw=0.090, wy=0.33, ch=0.15, sw=0.06, eng=(0.40,),
                     prop=True, ts=0.34, tri=False),
      'single': dict(sp=0.96, ln=0.66, fw=0.076, wy=0.30, ch=0.14, sw=0.04, eng=(),
                     prop='nose', ts=0.30, tri=False),
    }[kind]

    cx = W / 2
    y0 = Hh * 0.04
    L = Hh * 0.92 * P['ln']
    y1 = y0 + L
    fw = W * P['fw'] / 2
    Y = lambda t: y0 + L * t

    # ── voilure : trapeze en fleche
    wy = Y(P['wy'])
    span = W * P['sp'] / 2
    ch = L * P['ch']
    sw = L * P['sw']
    for sgn in (-1, 1):
        d.polygon([(cx + sgn * fw * 0.9, wy),
                   (cx + sgn * span, wy + sw),
                   (cx + sgn * span, wy + sw + ch * 0.34),
                   (cx + sgn * fw * 0.9, wy + ch)], fill=c2)

    # ── empennage horizontal
    ty = Y(0.885)
    tspan = W * P['ts'] / 2
    tch = L * 0.085
    for sgn in (-1, 1):
        d.polygon([(cx + sgn * fw * 0.8, ty),
                   (cx + sgn * tspan, ty + tch * 0.95),
                   (cx + sgn * tspan, ty + tch * 1.45),
                   (cx + sgn * fw * 0.8, ty + tch * 1.30)], fill=c2)

    # ── fuselage : capsule effilee au nez, affinee a la queue
    pts_l, pts_r = [], []
    N = 40
    for i in range(N + 1):
        t = i / N
        if t < 0.13:
            r = fw * (0.20 + 0.80 * (t / 0.13) ** 0.55)
        elif t > 0.80:
            r = fw * (1 - 0.62 * ((t - 0.80) / 0.20) ** 1.3)
        else:
            r = fw
        pts_l.append((cx - r, Y(t)))
        pts_r.append((cx + r, Y(t)))
    d.polygon(pts_l + pts_r[::-1], fill=c)

    # ── derive vue de dessus : losange fin sur l'axe, a l'arriere
    d.polygon([(cx, Y(0.80)), (cx + fw * 0.52, Y(0.925)),
               (cx, Y(0.995)), (cx - fw * 0.52, Y(0.925))], fill=c2)

    # ── moteur central (trijet) : bulbe a la base de la derive
    if P['tri']:
        d.ellipse([cx - fw * 0.46, Y(0.945), cx + fw * 0.46, Y(1.02)], fill=c2)

    # ── nacelles ou turbopropulseurs
    for off in P['eng']:
        for sgn in (-1, 1):
            ex = cx + sgn * span * off
            ey = wy + sw * off * 0.92
            if P['prop'] is True:
                d.rounded_rectangle([ex - fw * 0.34, ey - L * 0.055, ex + fw * 0.34, ey + L * 0.075],
                                    radius=fw * 0.30, fill=c2)
                d.line([ex - span * 0.155, ey - L * 0.052, ex + span * 0.155, ey - L * 0.052],
                       fill=c2, width=max(3, int(Hh * 0.010)))
            else:
                d.rounded_rectangle([ex - fw * 0.40, ey - L * 0.045, ex + fw * 0.40, ey + L * 0.085],
                                    radius=fw * 0.36, fill=c2)
                d.ellipse([ex - fw * 0.30, ey - L * 0.040, ex + fw * 0.30, ey + L * 0.005], fill=dark)

    # ── helice de nez
    if P['prop'] == 'nose':
        d.line([cx - span * 0.34, Y(0.030), cx + span * 0.34, Y(0.030)],
               fill=c2, width=max(3, int(Hh * 0.010)))

    # ── verriere
    d.polygon([(cx - fw * 0.55, Y(0.115)), (cx, Y(0.055)), (cx + fw * 0.55, Y(0.115)),
               (cx + fw * 0.40, Y(0.165)), (cx - fw * 0.40, Y(0.165))], fill=dark)
    # ── porte cargo laterale
    d.rounded_rectangle([cx + fw * 0.30, Y(0.30), cx + fw * 0.92, Y(0.45)],
                        radius=fw * 0.10, outline=dark, width=max(2, int(Hh * 0.006)))
    return im.resize((w, h), Image.LANCZOS)


# ─────────────────────────── barre de progression ───────────────────────────
def gauge(pct, w=360, h=26, col=None, bg=(38, 34, 66)):
    S = 3
    im = Image.new('RGBA', (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = h * S / 2
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], radius=r, fill=bg + (255,))
    ww = max(h * S, (w * S) * min(max(pct, 0), 100) / 100)
    d.rounded_rectangle([0, 0, ww, h * S - 1], radius=r, fill=(col or ORANGE) + (255,))
    return im.resize((w, h), Image.LANCZOS)


def build(outdir):
    global OUT
    OUT = outdir
    os.makedirs(OUT, exist_ok=True)
    names = []
    names.append(save(background(), 'bg.png'))
    names.append(save(mark(384), 'mark.png'))
    names.append(save(wordmark(), 'wordmark.png'))
    names.append(transparent('px_panel.png'))
    names.append(transparent('px_tile.png'))
    for k in ('pulse', 'plane', 'hub', 'truck', 'leaf', 'chart', 'bolt'):
        names.append(save(_icon(k, 128, True), f'ic_{k}_on.png'))
        names.append(save(_icon(k, 128, False), f'ic_{k}_off.png'))
    return names


# ─────────────────────────── carte du réseau ───────────────────────────
def network_map(hubs, w=944, h=540, lon0=-170, lon1=158, lat0=-46, lat1=76,
                bubbles=True, labels=True):
    """Planisphère en points + routes aériennes réelles. Dessin original, aucune tuile importée."""
    from global_land_mask import globe
    S = 2
    W, H = w * S, h * S
    im = Image.new('RGB', (W, H), (23, 10, 43))

    def px(lat, lon):
        return ((lon - lon0) / (lon1 - lon0) * W, (lat1 - lat) / (lat1 - lat0) * H)

    glow = Image.new('RGB', (W, H), (23, 10, 43))
    gd = ImageDraw.Draw(glow)
    for la, lo, r in ((36, -92, W * 0.17), (49, 6, W * 0.10), (28, 120, W * 0.11)):
        x, y = px(la, lo)
        gd.ellipse([x - r, y - r, x + r, y + r], fill=(56, 25, 98))
    glow = glow.filter(ImageFilter.GaussianBlur(int(W * 0.055)))
    im = Image.blend(im, glow, 0.5)
    d = ImageDraw.Draw(im, 'RGBA')

    for lo in range(-180, 181, 30):
        if lon0 <= lo <= lon1:
            x, _ = px(0, lo)
            d.line([x, 0, x, H], fill=(150, 110, 220, 22), width=1)
    for la in range(-30, 76, 30):
        if lat0 <= la <= lat1:
            _, y = px(la, 0)
            d.line([0, y, W, y], fill=(150, 110, 220, 22), width=1)

    step = 1.0
    r = max(1.0, W / 1250)
    la = lat0
    while la <= lat1:
        lo = lon0
        while lo <= lon1:
            if globe.is_land(la, lo):
                x, y = px(la, lo)
                t = max(0.0, min(1.0, (la - lat0) / (lat1 - lat0)))
                d.ellipse([x - r, y - r, x + r, y + r],
                          fill=(int(120 + 44 * t), int(92 + 30 * t), int(184 + 34 * t), 205))
            lo += step
        la += step

    HB = {n: (la, lo, cap) for n, la, lo, cap, _ in hubs}

    def arc(a, b, col, width, alpha, lift=0.18):
        (la1, lo1, _), (la2, lo2, _) = HB[a], HB[b]
        x1, y1 = px(la1, lo1); x2, y2 = px(la2, lo2)
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1
        mx, my = (x1 + x2) / 2 - dy / L * L * lift, (y1 + y2) / 2 + dx / L * L * lift
        pts = [((1 - t) ** 2 * x1 + 2 * (1 - t) * t * mx + t ** 2 * x2,
                (1 - t) ** 2 * y1 + 2 * (1 - t) * t * my + t ** 2 * y2)
               for t in [i / 60 for i in range(61)]]
        d.line(pts, fill=col + (alpha,), width=width, joint='curve')
        for k in (0.34, 0.62, 0.86):
            x, y = pts[int(k * 60)]
            rr = max(1.4, W / 760)
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col + (min(255, alpha + 80),))

    US = ['Indianapolis Hub', 'Miami Gateway', 'Fort Worth Alliance', 'Newark', 'Oakland',
          'Chicago', 'Los Angeles', 'Atlanta']
    for n in US:
        arc('Memphis SuperHub', n, ORANGE, max(2, S), 105, 0.15)
    arc('Memphis SuperHub', 'Anchorage', ORANGE, max(2, S), 130, 0.20)
    for n in ('Paris CDG', 'Liege', 'Cologne'):
        arc('Memphis SuperHub', n, ORANGE, max(2, S + 1), 160, 0.17)
    for n in ('Guangzhou', 'Osaka'):
        arc('Paris CDG', n, VIOLET, max(2, S + 1), 150, 0.15)

    mx = max(c for _, _, _, c, _ in hubs)
    for name, la, lo, cap, tier in (hubs if bubbles else []):
        x, y = px(la, lo)
        rr = (W / 320) + (W / 96) * (cap / mx) ** 0.55
        for k, a in ((3.0, 16), (2.0, 34), (1.4, 70)):
            d.ellipse([x - rr * k, y - rr * k, x + rr * k, y + rr * k], fill=ORANGE + (a,))
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=ORANGE + (255,))
        d.ellipse([x - rr * 0.40, y - rr * 0.40, x + rr * 0.40, y + rr * 0.40],
                  fill=(255, 244, 232, 255))

    # Etiquettes placees par essais successifs : chaque nom prend la premiere position
    # libre autour de son hub. Aucune ne peut donc en recouvrir une autre, ni tomber sur
    # un autre hub : c'est la grappe americaine (huit hubs serres) qui l'imposait.
    LAB = {'Memphis SuperHub': 'MEMPHIS', 'Indianapolis Hub': 'INDIANAPOLIS',
           'Newark': 'NEWARK', 'Miami Gateway': 'MIAMI',
           'Fort Worth Alliance': 'FORT WORTH', 'Oakland': 'OAKLAND',
           'Anchorage': 'ANCHORAGE', 'Paris CDG': 'PARIS', 'Cologne': 'COLOGNE',
           'Liege': 'LIEGE', 'Guangzhou': 'GUANGZHOU', 'Osaka': 'OSAKA',
           'Chicago': 'CHICAGO', 'Los Angeles': 'LOS ANGELES', 'Atlanta': 'ATLANTA'}
    f = _f(int(W / 66))
    fh = W / 52                       # hauteur de ligne
    pad = W / 260                     # marge autour du hub
    taken = []                        # boites deja posees
    marks = [px(la, lo) for _, la, lo, _, _ in hubs]

    def free(bx):
        x0, y0, x1, y1 = bx
        if x0 < 4 or y0 < 4 or x1 > W - 4 or y1 > H * 0.965:
            return False
        for t in taken:
            if x0 < t[2] + pad and t[0] < x1 + pad and y0 < t[3] + pad and t[1] < y1 + pad:
                return False
        for mxp, myp in marks:          # ne jamais poser une etiquette sur un hub
            if x0 - pad < mxp < x1 + pad and y0 - pad < myp < y1 + pad:
                return False
        return True

    # du plus gros hub au plus petit : les grands noms se placent en premier
    for name, la, lo, cap, tier in (sorted(hubs, key=lambda r: -r[3]) if labels else []):
        if name not in LAB:
            continue
        txt = LAB[name]
        x, y = px(la, lo)
        tw = d.textlength(txt, font=f)
        r0 = W / 150
        best = None
        for ring in (1.0, 1.7, 2.6, 3.8):
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                           (1, 1), (-1, 1), (1, -1), (-1, -1)):
                cx = x + dx * (r0 * ring + (tw / 2 if dx else 0)) - tw / 2
                cy = y + dy * (r0 * ring + (fh / 2 if dy else 0)) - fh / 2
                box = (cx, cy, cx + tw, cy + fh)
                if free(box):
                    best = box
                    break
            if best:
                break
        if not best:
            continue
        taken.append(best)
        tx, ty = best[0], best[1]
        for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            d.text((tx + ox, ty + oy), txt, font=f, fill=(19, 8, 36, 235))
        d.text((tx, ty), txt, font=f, fill=(255, 255, 255, 250))

    band = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(band)
    for i in range(int(H * 0.23)):
        a = int(244 * (1 - i / (H * 0.23)) ** 1.35)
        bd.line([0, i, W, i], fill=(23, 10, 43, a))
    for i in range(int(H * 0.11)):
        a = int(200 * (1 - i / (H * 0.11)) ** 1.4)
        bd.line([0, H - 1 - i, W, H - 1 - i], fill=(23, 10, 43, a))
    im = Image.alpha_composite(im.convert('RGBA'), band).convert('RGB')
    d = ImageDraw.Draw(im, 'RGBA')

    lf = _f(int(W / 62), False)
    items = [('dot', ORANGE, 'Sorting hub, bubble size is pieces per hour'),
             ('line', ORANGE, 'Routes from Memphis'),
             ('line', VIOLET, 'Europe to Asia')] if bubbles else [
             ('dot', ORANGE, 'Click a hub to filter the page, size is pieces per hour'),
             ('line', ORANGE, 'Routes from Memphis'),
             ('line', VIOLET, 'Europe to Asia')]
    pad = W * 0.014
    lh = W / 46
    tw = max(d.textlength(t, font=lf) for _, _, t in items)
    bw = tw + W / 24 + pad * 2
    bh = lh * len(items) + pad * 1.6
    bx, by = W * 0.014, H - bh - W * 0.012
    plate = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle([bx, by, bx + bw, by + bh],
                                            radius=W * 0.008, fill=(18, 7, 34, 232),
                                            outline=(96, 62, 148, 255), width=max(1, int(W / 900)))
    im = Image.alpha_composite(im.convert('RGBA'), plate).convert('RGB')
    d = ImageDraw.Draw(im, 'RGBA')
    ty = by + pad * 0.8
    for kind, col, txt in items:
        cx = bx + pad + W / 90
        cy = ty + lh * 0.42
        if kind == 'dot':
            rr = W / 190
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], fill=col + (255,))
        else:
            d.line([cx - W / 100, cy, cx + W / 100, cy], fill=col + (255,), width=max(2, int(W / 340)))
        d.text((bx + pad + W / 42, ty), txt, font=lf, fill=(255, 255, 255, 246))
        ty += lh
    return im.resize((w, h), Image.LANCZOS)


# ─────────────────────────── icônes de KPI ───────────────────────────
def kpi_icon(kind, size=96, col=None):
    """Pictogramme original par indicateur, tracé au trait épais."""
    S = size * 4
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = (col or ORANGE) + (255,)
    lw = max(3, int(S * 0.055))
    P = lambda *v: [x * S for x in v]

    if kind == 'plane':                      # avion vu de dessus
        d.polygon(P(0.50,0.06, 0.575,0.30, 0.575,0.44, 0.96,0.63, 0.96,0.73, 0.575,0.62,
                    0.575,0.82, 0.70,0.92, 0.70,0.97, 0.50,0.90, 0.30,0.97, 0.30,0.92,
                    0.425,0.82, 0.425,0.62, 0.04,0.73, 0.04,0.63, 0.425,0.44, 0.425,0.30), fill=c)
    elif kind == 'parcel':                   # colis
        d.polygon(P(0.50,0.08, 0.92,0.30, 0.50,0.52, 0.08,0.30), fill=c)
        d.polygon(P(0.08,0.34, 0.48,0.56, 0.48,0.94, 0.08,0.72), fill=c)
        d.polygon(P(0.92,0.34, 0.92,0.72, 0.52,0.94, 0.52,0.56), fill=c[:3] + (170,))
    elif kind == 'dollar':
        d.ellipse(P(0.04,0.04,0.96,0.96), outline=c, width=lw)
        gf = _f(int(S * 0.72))
        tw = d.textlength('$', font=gf)
        d.text((S * 0.5 - tw / 2, S * 0.09), '$', font=gf, fill=c)
    elif kind == 'globe':
        d.ellipse(P(0.06,0.06,0.94,0.94), outline=c, width=lw)
        d.ellipse(P(0.32,0.06,0.68,0.94), outline=c, width=max(2, lw - 2))
        d.line(P(0.06,0.50,0.94,0.50), fill=c, width=max(2, lw - 2))
        d.arc(P(0.06,0.16,0.94,0.62), 0, 180, fill=c, width=max(2, lw - 2))
        d.arc(P(0.06,0.38,0.94,0.84), 180, 360, fill=c, width=max(2, lw - 2))
    elif kind == 'people':
        d.ellipse(P(0.36,0.08,0.64,0.36), fill=c)
        d.pieslice(P(0.20,0.42,0.80,1.02), 180, 360, fill=c)
        d.ellipse(P(0.06,0.20,0.26,0.40), fill=c[:3] + (180,))
        d.ellipse(P(0.74,0.20,0.94,0.40), fill=c[:3] + (180,))
        d.pieslice(P(0.00,0.46,0.30,0.92), 180, 360, fill=c[:3] + (180,))
        d.pieslice(P(0.70,0.46,1.00,0.92), 180, 360, fill=c[:3] + (180,))
    elif kind == 'weight':                   # charge utile : haltere
        d.rounded_rectangle(P(0.22,0.44,0.78,0.56), radius=S*0.03, fill=c)
        for x in (0.06, 0.78):
            d.rounded_rectangle(P(x,0.26,x+0.16,0.74), radius=S*0.05, fill=c)
        for x in (0.00, 0.94):
            d.rounded_rectangle(P(x,0.36,x+0.06,0.64), radius=S*0.03, fill=c[:3]+(190,))
    elif kind == 'scale':                    # moyenne / balance
        d.line(P(0.50,0.10,0.50,0.86), fill=c, width=lw)
        d.line(P(0.16,0.28,0.84,0.28), fill=c, width=lw)
        d.line(P(0.28,0.86,0.72,0.86), fill=c, width=lw)
        d.arc(P(0.02,0.16,0.34,0.48), 0, 180, fill=c, width=lw)
        d.arc(P(0.66,0.16,0.98,0.48), 0, 180, fill=c, width=lw)
    elif kind == 'factory':                  # constructeur
        d.polygon(P(0.06,0.92, 0.06,0.46, 0.34,0.62, 0.34,0.46, 0.62,0.62, 0.62,0.20,
                    0.94,0.20, 0.94,0.92), fill=c)
        d.rectangle(P(0.16,0.66,0.26,0.80), fill=(20,8,38,255))
        d.rectangle(P(0.44,0.66,0.54,0.80), fill=(20,8,38,255))
        d.rectangle(P(0.72,0.44,0.84,0.62), fill=(20,8,38,255))
    elif kind == 'key':                      # propriété
        d.ellipse(P(0.06,0.30,0.46,0.70), outline=c, width=lw)
        d.line(P(0.42,0.50,0.94,0.50), fill=c, width=lw)
        d.line(P(0.74,0.50,0.74,0.74), fill=c, width=lw)
        d.line(P(0.90,0.50,0.90,0.70), fill=c, width=lw)
    elif kind == 'order':                    # carnet de commandes
        d.rounded_rectangle(P(0.10,0.16,0.90,0.92), radius=S*0.06, outline=c, width=lw)
        d.line(P(0.10,0.36,0.90,0.36), fill=c, width=lw)
        d.line(P(0.30,0.06,0.30,0.26), fill=c, width=lw)
        d.line(P(0.70,0.06,0.70,0.26), fill=c, width=lw)
        d.line(P(0.26,0.62,0.44,0.78), fill=c, width=lw)
        d.line(P(0.44,0.78,0.76,0.48), fill=c, width=lw)
    elif kind == 'warehouse':                # hub
        d.polygon(P(0.50,0.10, 0.96,0.38, 0.96,0.92, 0.04,0.92, 0.04,0.38), fill=c)
        d.rectangle(P(0.34,0.56,0.66,0.92), fill=(20,8,38,255))
        d.rectangle(P(0.14,0.52,0.26,0.68), fill=(20,8,38,255))
        d.rectangle(P(0.74,0.52,0.86,0.68), fill=(20,8,38,255))
    elif kind == 'sort':                     # convoyeur de tri
        d.rounded_rectangle(P(0.04,0.58,0.96,0.74), radius=S*0.05, fill=c)
        for cx in (0.16, 0.38, 0.60, 0.82):
            d.ellipse(P(cx-0.07,0.74,cx+0.07,0.88), outline=c, width=max(2, lw-2))
        d.rectangle(P(0.14,0.34,0.36,0.56), fill=c)
        d.rectangle(P(0.46,0.20,0.66,0.56), fill=c[:3]+(180,))
        d.rectangle(P(0.74,0.40,0.92,0.56), fill=c[:3]+(180,))
    elif kind == 'area':                     # surface au sol
        d.rectangle(P(0.08,0.08,0.92,0.92), outline=c, width=lw)
        d.line(P(0.08,0.08,0.92,0.92), fill=c[:3]+(150,), width=max(2, lw-2))
        d.line(P(0.08,0.42,0.42,0.08), fill=c[:3]+(120,), width=max(2, lw-3))
        d.line(P(0.58,0.92,0.92,0.58), fill=c[:3]+(120,), width=max(2, lw-3))
    elif kind == 'land':                     # terrain
        d.polygon(P(0.04,0.72, 0.36,0.46, 0.62,0.66, 0.96,0.34, 0.96,0.92, 0.04,0.92), fill=c)
        d.ellipse(P(0.68,0.10,0.90,0.32), fill=c[:3]+(170,))
    elif kind == 'tower':                    # tour de contrôle
        d.polygon(P(0.36,0.92, 0.42,0.42, 0.58,0.42, 0.64,0.92), fill=c)
        d.polygon(P(0.28,0.42, 0.36,0.22, 0.64,0.22, 0.72,0.42), fill=c)
        d.line(P(0.50,0.22,0.50,0.04), fill=c, width=lw)
        d.arc(P(0.18,0.02,0.82,0.34), 200, 340, fill=c[:3]+(150,), width=max(2, lw-2))
    elif kind == 'truck':
        d.rounded_rectangle(P(0.04,0.34,0.58,0.70), radius=S*0.04, fill=c)
        d.polygon(P(0.58,0.42, 0.78,0.42, 0.92,0.56, 0.92,0.70, 0.58,0.70), fill=c)
        for cx in (0.24, 0.76):
            d.ellipse(P(cx-0.11,0.64,cx+0.11,0.86), fill=c)
            d.ellipse(P(cx-0.05,0.70,cx+0.05,0.80), fill=(20,8,38,255))
    elif kind == 'plug':                     # véhicule électrique
        d.rounded_rectangle(P(0.28,0.30,0.72,0.72), radius=S*0.06, fill=c)
        d.line(P(0.40,0.30,0.40,0.08), fill=c, width=lw)
        d.line(P(0.60,0.30,0.60,0.08), fill=c, width=lw)
        d.line(P(0.50,0.72,0.50,0.94), fill=c, width=lw)
        d.polygon(P(0.52,0.36, 0.36,0.56, 0.48,0.56, 0.44,0.68, 0.62,0.48, 0.50,0.48),
                  fill=(20,8,38,255))
    elif kind == 'building':
        d.rectangle(P(0.08,0.26,0.46,0.92), fill=c)
        d.rectangle(P(0.52,0.44,0.92,0.92), fill=c[:3]+(190,))
        for yy in (0.34, 0.50, 0.66, 0.80):
            for xx in (0.14, 0.28):
                d.rectangle(P(xx,yy,xx+0.08,yy+0.08), fill=(20,8,38,255))
        for yy in (0.54, 0.70, 0.84):
            for xx in (0.60, 0.76):
                d.rectangle(P(xx,yy,xx+0.08,yy+0.06), fill=(20,8,38,255))
    elif kind == 'pallet':                   # fret palettisé
        d.rectangle(P(0.10,0.72,0.90,0.82), fill=c)
        d.rectangle(P(0.14,0.82,0.24,0.92), fill=c)
        d.rectangle(P(0.45,0.82,0.55,0.92), fill=c)
        d.rectangle(P(0.76,0.82,0.86,0.92), fill=c)
        d.rectangle(P(0.20,0.36,0.52,0.70), fill=c[:3]+(210,))
        d.rectangle(P(0.56,0.20,0.84,0.70), fill=c[:3]+(160,))
    elif kind == 'cloud':                    # émissions
        d.ellipse(P(0.06,0.34,0.44,0.72), fill=c)
        d.ellipse(P(0.28,0.20,0.72,0.64), fill=c)
        d.ellipse(P(0.56,0.36,0.94,0.72), fill=c)
        d.rectangle(P(0.16,0.54,0.84,0.72), fill=c)
        for xx in (0.26, 0.48, 0.70):
            d.line(P(xx,0.80,xx-0.06,0.94), fill=c[:3]+(190,), width=lw)
    elif kind == 'gauge':                    # intensité
        d.arc(P(0.04,0.16,0.96,1.08), 180, 360, fill=c, width=lw)
        d.line(P(0.50,0.62,0.24,0.34), fill=c, width=lw)
        d.ellipse(P(0.42,0.54,0.58,0.70), fill=c)
        for a in (200, 240, 280, 320):
            x1 = 0.50 + 0.40 * math.cos(math.radians(a)); y1 = 0.62 + 0.40 * math.sin(math.radians(a))
            x2 = 0.50 + 0.32 * math.cos(math.radians(a)); y2 = 0.62 + 0.32 * math.sin(math.radians(a))
            d.line(P(x1,y1,x2,y2), fill=c[:3]+(170,), width=max(2, lw-2))
    elif kind == 'chain':                    # chaîne d'approvisionnement
        for cx in (0.22, 0.50, 0.78):
            d.ellipse(P(cx-0.16,0.34,cx+0.16,0.66), outline=c, width=lw)
        d.line(P(0.36,0.50,0.36,0.50), fill=c, width=lw)
    elif kind == 'fuel':                     # carburant durable
        d.polygon(P(0.50,0.06, 0.86,0.50, 0.86,0.72, 0.50,0.94, 0.14,0.72, 0.14,0.50), fill=c)
        d.polygon(P(0.50,0.28, 0.34,0.54, 0.46,0.54, 0.40,0.76, 0.66,0.46, 0.54,0.46),
                  fill=(20,8,38,255))
    elif kind == 'bolt':                     # energie
        d.polygon(P(0.50,0.04, 0.90,0.27, 0.90,0.73, 0.50,0.96, 0.10,0.73, 0.10,0.27),
                  outline=c, width=lw)
        d.polygon(P(0.56,0.18, 0.30,0.54, 0.47,0.54, 0.42,0.84, 0.70,0.46, 0.53,0.46), fill=c)
    elif kind == 'chart':
        for i, hh in enumerate((0.34, 0.54, 0.76)):
            x = 0.10 + i * 0.28
            d.rounded_rectangle(P(x,0.92-hh,x+0.18,0.92), radius=S*0.02, fill=c)
        d.line(P(0.12,0.36,0.42,0.20,0.88,0.08), fill=c, width=lw)
    elif kind == 'percent':
        gf = _f(int(S * 0.86))
        tw = d.textlength('%', font=gf)
        d.text((S * 0.5 - tw / 2, S * 0.02), '%', font=gf, fill=c)
    elif kind == 'coin':
        d.ellipse(P(0.10,0.22,0.90,0.60), outline=c, width=lw)
        d.arc(P(0.10,0.40,0.90,0.78), 0, 180, fill=c, width=lw)
        d.line(P(0.10,0.41,0.10,0.59), fill=c, width=lw)
        d.line(P(0.90,0.41,0.90,0.59), fill=c, width=lw)
        d.arc(P(0.10,0.54,0.90,0.92), 0, 180, fill=c, width=lw)
        d.line(P(0.10,0.55,0.10,0.73), fill=c, width=lw)
        d.line(P(0.90,0.55,0.90,0.73), fill=c, width=lw)
    elif kind == 'share':                    # bénéfice par action
        d.rounded_rectangle(P(0.10,0.10,0.90,0.90), radius=S*0.08, outline=c, width=lw)
        d.line(P(0.24,0.68,0.42,0.46,0.58,0.58,0.78,0.28), fill=c, width=lw)
        d.ellipse(P(0.72,0.22,0.84,0.34), fill=c)
    elif kind == 'invest':                   # investissement
        d.polygon(P(0.50,0.06, 0.62,0.34, 0.92,0.34, 0.68,0.54, 0.78,0.86, 0.50,0.66,
                    0.22,0.86, 0.32,0.54, 0.08,0.34, 0.38,0.34), fill=c)
    return im.resize((size, size), Image.LANCZOS)


def fedex_logo(src, w=300, h=84, pad=0.10):
    """Prépare le logo fourni par l'utilisateur : rognage des marges, pastille blanche."""
    im = Image.open(src).convert('RGB')
    g = im.convert('L')
    bbox = g.point(lambda v: 255 if v < 245 else 0).getbbox()
    im = im.crop(bbox)
    sc = min((w * (1 - 2 * pad)) / im.width, (h * (1 - 2 * pad)) / im.height)
    im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
    card = Image.new('RGBA', (w * 4, h * 4), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle([0, 0, w * 4 - 1, h * 4 - 1], radius=h * 4 * 0.22,
                                           fill=(255, 255, 255, 255))
    card = card.resize((w, h), Image.LANCZOS)
    card.paste(im, ((w - im.width) // 2, (h - im.height) // 2))
    return card
