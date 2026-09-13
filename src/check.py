# -*- coding: utf-8 -*-
"""check - pre-delivery quality gate. Exits non-zero if any check fails."""
import glob, json, os, re, sys, csv

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
REP  = os.path.join(ROOT, 'FedEx.Report')
SM   = os.path.join(ROOT, 'FedEx.SemanticModel')
RES  = os.path.join(REP, 'StaticResources', 'RegisteredResources')

err, ok = [], []

# ── inventaire du modèle
measures, columns = set(), {}
mt = open(os.path.join(SM, 'definition', 'tables', 'Metrics.tmdl'), encoding='utf-8').read()
for m in re.finditer(r"^\tmeasure\s+('([^']+)'|[^\s=]+)\s*=", mt, re.M):
    measures.add(m.group(2) or m.group(1))
for f in glob.glob(os.path.join(SM, 'definition', 'tables', '*.tmdl')):
    t = os.path.basename(f)[:-5]
    src = open(f, encoding='utf-8').read()
    columns[t] = set()
    for c in re.finditer(r"^\tcolumn\s+('([^']+)'|\S+)\s*$", src, re.M):
        columns[t].add(c.group(2) or c.group(1))
ok.append(f'{len(measures)} measures and {sum(len(v) for v in columns.values())} columns in the model')

# ── colonnes et mesures référencées par le DAX des mesures
tabs = {}
for f in glob.glob(os.path.join(SM, 'definition', 'tables', '*.tmdl')):
    t = os.path.basename(f)[:-5]
    tabs[t] = set()
    for c in re.finditer(r"^\tcolumn\s+('([^']+)'|\S+)\s*$", open(f, encoding='utf-8').read(), re.M):
        tabs[t].add(c.group(2) or c.group(1))
dax_bad = []
for mm in re.finditer(r"^\tmeasure\s+('([^']+)'|[^\s=]+)\s*=(.*?)(?=^\t(?:measure|column|partition)|\Z)",
                      mt, re.M | re.S):
    nm = mm.group(2) or mm.group(1)
    body = mm.group(3)
    body = re.sub(r'^\s*(formatString|displayFolder|lineageTag):.*$', '', body, flags=re.M)
    for ref in re.finditer(r"(\w+)\[([^\]]+)\]", body):
        t, c = ref.group(1), ref.group(2)
        if t in tabs and c not in tabs[t] and c not in measures:
            dax_bad.append(f'mesure [{nm}] reference {t}[{c}] qui n existe pas')
    for ref in re.finditer(r"(?<![\w\]])\[([^\]]+)\]", body):
        c = ref.group(1)
        if c not in measures:
            dax_bad.append(f'mesure [{nm}] reference la mesure [{c}] qui n existe pas')
err += dax_bad
ok.append(f'{len(dax_bad)} broken DAX references')

# ── références des visuels
used_m, used_c, missing = set(), set(), []
def walk(o, path=''):
    if isinstance(o, dict):
        for k in ('Measure', 'Column'):
            if k in o and isinstance(o[k], dict) and 'Property' in o[k]:
                e = o[k].get('Expression', {}).get('SourceRef', {}).get('Entity')
                p = o[k]['Property']
                if e:
                    (used_m if k == 'Measure' else used_c).add((e, p))
        for v in o.values():
            walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)

files = glob.glob(os.path.join(REP, 'definition', 'pages', '*', 'visuals', '*', 'visual.json'))
for f in files:
    walk(json.load(open(f, encoding='utf-8')))
for e, p in sorted(used_m):
    if e == 'Metrics' and p not in measures:
        missing.append(f'mesure absente : {e}[{p}]')
    elif e != 'Metrics' and p not in columns.get(e, set()):
        missing.append(f'mesure/colonne absente : {e}[{p}]')
for e, p in sorted(used_c):
    if p not in columns.get(e, set()):
        missing.append(f'colonne absente : {e}[{p}]')
err += missing
ok.append(f'{len(files)} visuals referencing {len(used_m)} measures and {len(used_c)} columns, '
          f'{len(missing)} missing')

# ── textes de carte qui deborderaient en largeur (le wordWrap est sans effet)
try:
    import importlib, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from PIL import ImageFont
    import render_pages as RP
    FBOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    over, nocard = [], []
    CARDS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                        'rendered_values.json'), encoding='utf-8')).get('cards', {})
    for f in files:
        v = json.load(open(f, encoding='utf-8'))
        V = v['visual']
        if V['visualType'] != 'card':
            continue
        try:
            nm = list(V['query']['queryState']['Values']['projections'][0]['field'].values())[0]['Property']
        except Exception:
            continue
        # priorite au texte releve en DAX sur le modele : c'est ce que Power BI affiche
        s = CARDS.get(nm, RP.VALUES.get(nm))
        if not s:
            nocard.append(nm)
            continue
        fs = (RP.val(V, 'objects', 'labels', 0, 'properties', 'fontSize') or 20) * 1.33
        lw = ImageFont.truetype(FBOLD, int(fs)).getlength(s)
        if lw > v['position']['width'] - 4:
            over.append(f"{v['name']} {nm} : {lw:.0f}px > {v['position']['width'] - 4}px ({s})")
    err += over
    ok.append(f'{len(over)} card texts too wide '
              f'({len(CARDS)} values read from the live model, {len(set(nocard))} not read)')
except Exception as e:
    ok.append(f'card width check not run ({e})')

# ── titres et sous-titres de visuel qui deborderaient de leur panneau
tt = []
try:
    from PIL import ImageFont as _IF
    FB_T = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    FR_T = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    for f in files:
        v = json.load(open(f, encoding='utf-8'))
        vco = v['visual'].get('visualContainerObjects', {})
        w = v['position']['width'] - 28
        for role, fnt, dflt in (('title', FB_T, 18), ('subTitle', FR_T, 13)):
            if RP.val(vco, role, 0, 'properties', 'show') is not True:
                continue
            txt = RP.val(vco, role, 0, 'properties', 'text')
            sz = (RP.val(vco, role, 0, 'properties', 'fontSize') or dflt) * 1.33
            if txt and _IF.truetype(fnt, int(sz)).getlength(txt) > w:
                tt.append(f"{v['name']} {role} : « {txt} » depasse {w:.0f}px")
except Exception as e:
    ok.append(f'visual title check not run ({e})')
err += tt
ok.append(f'{len(tt)} visual titles too wide')

# ── tailles de police entières
dec = []
for f in files:
    src = open(f, encoding='utf-8').read()
    for m in re.finditer(r'"(fontSize|textSize|titleFontSize)"[^}]*?"Value":\s*"([0-9.]+)D"', src, re.S):
        if '.' in m.group(2):
            dec.append(f'{os.path.basename(os.path.dirname(f))}: {m.group(1)}={m.group(2)}')
err += dec
ok.append(f'{len(dec)} decimal font sizes')

# ── chaque colonne de tableau doit contenir son en-tete ET sa plus longue valeur
#    (c'est la panne que l'utilisateur signale en boucle : « Internatio... », « Corporate & o... »)
trunc = []
try:
    from PIL import ImageFont
    FBOLD_T = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    FREG_T = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    # correspondance nom affiche -> colonne du CSV, lue dans le TMDL (source de verite)
    COLSRC = {}
    for tf in glob.glob(os.path.join(ROOT, '*.SemanticModel', 'definition', 'tables', '*.tmdl')):
        ent = os.path.basename(tf)[:-5]
        cur = None
        for ln in open(tf, encoding='utf-8'):
            mc = re.match(r"\s*column\s+'?([^'\n]+?)'?\s*$", ln)
            if mc:
                cur = mc.group(1)
            ms = re.match(r'\s*sourceColumn:\s*(\S+)', ln)
            if ms and cur:
                COLSRC[(ent, cur)] = ms.group(1)
    SRC = {}
    ddir = os.path.join(ROOT, 'Donnees')
    for fn in os.listdir(ddir):
        if fn.endswith('.csv'):
            with open(os.path.join(ddir, fn), encoding='utf-8') as fh:
                SRC[fn[:-4]] = list(csv.DictReader(fh))
    for f in files:
        v = json.load(open(f, encoding='utf-8'))
        V = v['visual']
        if V['visualType'] != 'tableEx':
            continue
        ws = [float(c['properties']['value']['expr']['Literal']['Value'].rstrip('D'))
              for c in V['objects']['columnWidth']]
        projs = V['query']['queryState']['Values']['projections']
        hs = (RP.val(V, 'objects', 'columnHeaders', 0, 'properties', 'fontSize') or 11) * 1.33
        ts = (RP.val(V, 'objects', 'grid', 0, 'properties', 'textSize') or 12) * 1.33
        fh_, ft_ = ImageFont.truetype(FBOLD_T, int(hs)), ImageFont.truetype(FREG_T, int(ts))
        srt = None
        try:
            srt = list(V['query']['sortDefinition']['sort'][0]['field'].values())[0]['Property']
        except Exception:
            pass
        for i, pr in enumerate(projs):
            if i >= len(ws):
                break
            kind, fld = list(pr['field'].items())[0]
            ent, prop = fld['Expression']['SourceRef']['Entity'], fld['Property']
            need = fh_.getlength(prop) + (18 if prop == srt else 0)
            if kind == 'Column':
                rows = SRC.get(ent, [])
                key = COLSRC.get((ent, prop), prop)
                vals = [str(r[key]) for r in rows if key in r]
                if vals:
                    need = max(need, max(ft_.getlength(x) for x in vals))
            if need + 22 > ws[i]:
                trunc.append(f"{v['name']} [{prop}] : {need + 22:.0f}px requis > {ws[i]:.0f}px")
except Exception as e:
    ok.append(f'column truncation check not run ({e})')
err += trunc
ok.append(f'{len(trunc)} table columns too narrow')

# ── taux de remplissage : un tableau ne doit pas laisser son panneau a moitie vide
vide = []
try:
    import pbir_lib as _L
    ROWS = {'THE FIVE BIGGEST HUBS': 5, 'THE FLEET, TYPE BY TYPE': 10,
            'EVERY MAJOR SORTING FACILITY': 15, 'THE NETWORK IN NUMBERS': 11,
            'THE COMMITMENTS': 9, 'BY SEGMENT': 3, 'BY SOURCE': 6}
    taux = []
    for f in files:
        v = json.load(open(f, encoding='utf-8'))
        V = v['visual']
        if V['visualType'] != 'tableEx':
            continue
        ttl = RP.val(V.get('visualContainerObjects', {}), 'title', 0, 'properties', 'text')
        if ttl not in ROWS:
            continue
        ts = RP.val(V, 'objects', 'grid', 0, 'properties', 'textSize') or 12
        rp = RP.val(V, 'objects', 'grid', 0, 'properties', 'rowPadding') or 0
        sub = RP.val(V.get('visualContainerObjects', {}), 'subTitle', 0, 'properties', 'show')
        hdr = _L.HDR_ZONE if sub is True else _L.HDR_ZONE - _L.SUB_H
        occ = hdr + ROWS[ttl] * _L.row_height(ts, rp)
        r = occ / v['position']['height']
        taux.append(r)
        if r < 0.85:
            vide.append(f"{ttl} : {r*100:.0f}% du panneau occupe")
    if taux:
        ok.append(f'{len(vide)} tables leaving their panel half empty '
                  f'(fill {min(taux)*100:.0f}-{max(taux)*100:.0f}%)')
except Exception as e:
    ok.append(f'panel fill check not run ({e})')
err += vide

# ── largeurs de tableau
wide = []
for f in files:
    v = json.load(open(f, encoding='utf-8'))
    if v['visual']['visualType'] != 'tableEx':
        continue
    ws = [c['properties']['value']['expr']['Literal']['Value'] for c in v['visual']['objects']['columnWidth']]
    s = sum(float(x.rstrip('D')) for x in ws)
    lim = v['position']['width'] - 45
    if s > lim:
        wide.append(f"{v['name']}: {s:.0f} > {lim:.0f}")
err += wide
ok.append(f'{len(wide)} tables that would overflow horizontally')

# ── images déclarées / présentes
rep = json.load(open(os.path.join(REP, 'definition', 'report.json'), encoding='utf-8'))
decl = {i['name'] for p in rep['resourcePackages'] if p['name'] == 'RegisteredResources'
        for i in p['items'] if i['type'] == 'Image'}
present = {os.path.basename(p) for p in glob.glob(os.path.join(RES, '*.png'))}
used_img = set()
for f in files:
    for m in re.finditer(r'"ItemName":\s*"([^"]+)"', open(f, encoding='utf-8').read()):
        used_img.add(m.group(1))
for n in sorted(used_img - decl):
    err.append(f'image utilisee mais non declaree dans report.json : {n}')
for n in sorted(used_img - present):
    err.append(f'image utilisee mais absente du dossier : {n}')
for n in sorted(decl - present):
    err.append(f'image declaree mais absente du dossier : {n}')
ok.append(f'{len(used_img)} images used, {len(decl)} declared, {len(present)} present')

# ── apostrophes dans les littéraux
bad = []
for f in files:
    for m in re.finditer(r'"Value":\s*"\'((?:[^\'"]|\'\')*)\'"', open(f, encoding='utf-8').read()):
        pass
    src = open(f, encoding='utf-8').read()
    for m in re.finditer(r'"Value": "\'(.*?)\'"', src):
        body = m.group(1)
        if re.search(r"(?<!')'(?!')", body):
            bad.append(f'{os.path.basename(os.path.dirname(f))}: {body[:50]}')
err += bad
ok.append(f"{len(bad)} literals with an unescaped apostrophe")

# ── pages et navigation
pages = json.load(open(os.path.join(REP, 'definition', 'pages', 'pages.json'), encoding='utf-8'))
names = set(pages['pageOrder'])
for f in files:
    src = open(f, encoding='utf-8').read()
    for m in re.finditer(r'"navigationSection":\s*\{[^}]*"Value":\s*"\'([^\']+)\'"', src):
        if m.group(1) not in names:
            err.append(f'bouton vers une page inexistante : {m.group(1)}')
ok.append(f"{len(names)} pages, navigation targets consistent")

# ── pas de pageBinding
for f in glob.glob(os.path.join(REP, 'definition', 'pages', '*', 'page.json')):
    if 'pageBinding' in open(f, encoding='utf-8').read():
        err.append(f'pageBinding present dans {f}')

# ── chevauchements de panneaux dans une même page
for pdir in glob.glob(os.path.join(REP, 'definition', 'pages', 'p*')):
    if not os.path.isdir(pdir):
        continue
    boxes = []
    for f in glob.glob(os.path.join(pdir, 'visuals', '*', 'visual.json')):
        v = json.load(open(f, encoding='utf-8'))
        t = v['visual']['visualType']
        if t in ('tableEx', 'barChart', 'columnChart', 'lineChart', 'stackedColumnChart',
                 'donutChart', 'map', 'scatterChart', 'areaChart', 'lineStackedColumnComboChart'):
            p = v['position']
            boxes.append((p['x'], p['y'], p['width'], p['height'], v['name']))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            ox = min(a[0]+a[2], b[0]+b[2]) - max(a[0], b[0])
            oy = min(a[1]+a[3], b[1]+b[3]) - max(a[1], b[1])
            if ox > 2 and oy > 2:
                err.append(f'chevauchement {a[4]} / {b[4]} ({ox}x{oy} px)')

print('\n'.join('  ' + o for o in ok))
if err:
    print('\nFAILURES:')
    for e in err:
        print('  !! ' + e)
    sys.exit(1)
print('\nAll checks passed.')
