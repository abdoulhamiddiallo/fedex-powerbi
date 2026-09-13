# -*- coding: utf-8 -*-
"""gen_report : construction des pages PBIR du rapport MERIDIAN."""
import os, shutil, csv, math, re, json
import brand
from pbir_lib import *
from pbir_lib import _accent_png
import pbir_lib as L

# bornes de la projection du planisphere : partagees par le PNG et la couche cliquable
MAP_BOUNDS = (-170, 158, -46, 76)
MAP_A = 928          # largeur du panneau carte
MAP_TOP = 82                    # bandeau reserve au titre, au-dessus de l'image
MAP_W, MAP_H = MAP_A - 4, 536 - MAP_TOP - 2   # le PNG fait la taille exacte de son cadre

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
REP  = os.path.join(ROOT, 'FedEx.Report')
RES  = os.path.join(REP, 'StaticResources', 'RegisteredResources')

TITLE = 'MERIDIAN'
SUB   = 'FedEx Global Network Intelligence'
THEME = 'ThemeMeridian'
LOGO_SRC = '/root/.claude/uploads/cd084ff7-7210-5a13-a830-25bf044b73be/7018556a-image.jpg'

NAV = [
    ('p1', 'Network Pulse', 'pulse',  'NETWORK'),
    ('p2', 'Air Fleet',     'plane',  'FLEET'),
    ('p3', 'Hubs',          'hub',    'HUBS'),
    ('p4', 'Ground',        'truck',  'GROUND'),
    ('p5', 'Climate',       'leaf',   'CLIMATE'),
    ('p6', 'Financials',    'chart',  'FINANCE'),
    ('p7', 'Energy',        'bolt',   'ENERGY'),
]

EYEBROW = 'FEDEX CORPORATION  ·  FY2026'
FOOT = ('Source: FedEx Form 10-K FY2026 and FY2025 (SEC), Statistical Book Q4 FY2026, Corporate Responsibility '
        'Reports. Fiscal year ends 31 May. Independent analysis of public filings.')

# ─────────────────────────── ossature de page ───────────────────────────
_FREG = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def slicer_width(ref, flag=None, size=13):
    """Largeur d'un segment en tuiles.

    Power BI donne la meme largeur a toutes les tuiles : c'est donc la valeur la plus
    longue qui commande. On la mesure et on ajoute la marge interne, pour qu'aucun
    libelle ne soit jamais coupe en 'Internatio...'."""
    from PIL import ImageFont
    ent, col, _ = L.parse(ref)
    tbl = {'D_FiscalYear': 'D_FiscalYear', 'D_Hub': 'D_Hub', 'F_Network': 'F_Network'}[ent]
    src = {'FiscalYearShort': 'FiscalYearShort', 'Tier': 'HubClass',
           'Continent': 'Continent', 'Pillar': 'Pillar'}[col]
    rows = list(csv.DictReader(open(os.path.join(ROOT, 'Donnees', tbl + '.csv'), encoding='utf-8')))
    if flag:
        fent, fcol, _ = L.parse(flag[0])
        rows = [r for r in rows if str(r.get(fcol)) == str(flag[1])]
    vals = sorted({r[src] for r in rows})
    f = ImageFont.truetype(_FREG, int(round(size * 1.33)))
    widest = max(f.getlength(v) for v in vals)
    return int(math.ceil(len(vals) * (widest + 20) + 24))

_FBOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def _tw(txt, size):
    """Largeur en pixels d'un titre, mesuree avec la meme metrique que le controle."""
    from PIL import ImageFont
    return ImageFont.truetype(_FBOLD, int(size)).getlength(txt)

_COLSRC = None
_RENDERED = None

def _rendered():
    """Valeurs affichees par Power BI, relevees en DAX sur le modele ouvert.

    C'est le seul moyen de connaitre la largeur reelle d'une colonne de mesure :
    « 56 owned · 3 leased » ou « 19,319,200 » ne sont dans aucun CSV."""
    global _RENDERED
    if _RENDERED is None:
        f = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rendered_values.json')
        _RENDERED = {k: v for k, v in json.load(open(f, encoding='utf-8')).items()
                     if not k.startswith('_')}
    return _RENDERED


def _colsrc():
    """Nom affiche -> colonne du CSV, lu dans le TMDL deja genere."""
    global _COLSRC
    if _COLSRC is None:
        _COLSRC = {}
        import glob as _g
        for tf in _g.glob(os.path.join(ROOT, '*.SemanticModel', 'definition', 'tables', '*.tmdl')):
            ent, cur = os.path.basename(tf)[:-5], None
            for ln in open(tf, encoding='utf-8'):
                mc = re.match(r"\s*column\s+'?([^'\n]+?)'?\s*$", ln)
                if mc:
                    cur = mc.group(1)
                ms = re.match(r'\s*sourceColumn:\s*(\S+)', ln)
                if ms and cur:
                    _COLSRC[(ent, cur)] = ms.group(1)
    return _COLSRC

def fitw(cols, widths, w, size=13, hdrsize=13, sort=None):
    """Elargit toute colonne trop etroite pour son en-tete ou sa plus longue valeur.

    Les largeurs passees restent des minimums : on ne retrecit jamais une colonne qui
    marche deja (les valeurs de mesure ne sont pas mesurables ici), on ne fait que
    donner sa place a ce qui serait coupe. C'est le controle que l'utilisateur a du
    faire a ma place trois fois de suite."""
    from PIL import ImageFont
    fh = ImageFont.truetype(_FBOLD, int(round(hdrsize * 1.33)))
    ft = ImageFont.truetype(_FREG, int(round(size * 1.33)))
    src = _colsrc()
    rend = _rendered()
    out = []
    for ref, cur in zip(cols, widths):
        ent, prop, meas = L.parse(ref)
        need = fh.getlength(prop) + (18 if sort and sort.endswith('.' + prop) else 0)
        vals = []
        # 1) valeurs telles que Power BI les affiche, relevees en DAX (mesures comprises)
        vals += rend.get(f'{ent}.{prop}', [])
        # 2) a defaut, le texte brut du CSV
        if not vals and not meas:
            key = src.get((ent, prop), prop)
            path = os.path.join(ROOT, 'Donnees', ent + '.csv')
            if os.path.exists(path):
                rows = list(csv.DictReader(open(path, encoding='utf-8')))
                vals = [str(r[key]) for r in rows if key in r]
        if vals:
            need = max(need, max(ft.getlength(v) for v in vals))
        elif meas:
            warn(f'colonne de mesure non relevee : {ref} (largeur non garantie)')
        out.append(int(math.ceil(max(cur, need + 22))))
    lim = w - 45
    if sum(out) > lim:
        warn(f'tableau {cols[0]} : {sum(out)} px necessaires pour {lim} px disponibles')
    return out

L.FITW = fitw

def frame(pg, active, title, subtitle, filt=None, flabel=None, fwidth=660, single=False,
          fvfilter=None):
    image(pg, 0, 0, W, H, 'bg.png', 'Fill')
    image(pg, 0, 0, RAIL_W, H, 'px_rail.png', 'Fill')
    image(pg, 12, 18, 96, 96, 'mark.png', 'Fit')
    y = 132
    for name, disp, icon, lab in NAV:
        on = (name == active)
        if on:
            image(pg, 6, y - 8, RAIL_W - 12, 82, 'px_railon.png', 'Fill')
            image(pg, 6, y - 8, 5, 82, _accent_png(ORANGE), 'Fill')
        image(pg, (RAIL_W - 46) // 2, y, 46, 46, f'ic_{icon}_{"on" if on else "off"}.png', 'Fit')
        text(pg, 0, y + 48, RAIL_W, 26, [(lab, 12, ORANGE if on else DIM, FTB)], 'center')
        navbutton(pg, 6, y - 8, RAIL_W - 12, 82, name, disp)
        y += 90
    text(pg, 0, H - 46, RAIL_W, 28, [(TITLE, 13, MUTED, FD)], 'center')

    fx = (X1 - 190 - fwidth) if filt else None
    # largeur reellement disponible pour le titre : on s'arrete avant le filtre
    tw = (fx - 20 - X0) if filt else 900
    tsize = 31
    while tsize > 26 and _tw(title.upper(), tsize * 1.33) > tw:
        tsize -= 1
    text(pg, X0, 6, 1000, 24, [(EYEBROW, 12, ORANGE, FTB)], 'left')
    text(pg, X0, 28, max(tw, 220), 46, [(title.upper(), tsize, INK, FD)], 'left')
    text(pg, X0, 78, 1400, 28, [(subtitle, 15, MUTED, FT)], 'left')
    image(pg, X1 - 178, 14, 178, 52, 'fedex_logo.png', 'Fit')
    if filt:
        text(pg, fx, 0, fwidth, 24, [(flabel or 'FILTER', 11, DIM, FTB)], 'left')
        slicer(pg, fx, 24, fwidth, 44, filt, size=13, padding=6, single=single,
               bg='#3B1D6B', fg=INK, vfilter=fvfilter)
    text(pg, X0, 860, CW, 30, [(FOOT, 12, '#BFAFE2', FT)], 'left')

def row(n, gap=16, x0=X0, w=CW):
    ww = (w - gap * (n - 1)) / n
    return [(x0 + i * (ww + gap), ww) for i in range(n)]

KPIY, KPIH = 112, 202
CY, CH = 328, 536            # zone de contenu
HALF = (CH - 16) // 2        # 260
TOPH = HALF                  # bloc haut quand il porte un tableau
BOTH = CH - 16 - TOPH        # 236

def kpirow(pg, items, y=KPIY, h=KPIH, vs=None):
    cols = row(len(items))
    # les tuiles a six colonnes sont plus etroites, mais le texte reste lisible :
    # c'est le controle des cartes qui dira si une ligne de contexte ne rentre plus
    ls = 12 if len(items) >= 6 else 13
    cs = 12 if len(items) >= 6 else 13
    vs = vs or (34 if len(items) >= 6 else 38)
    for i, ((x, w), it) in enumerate(zip(cols, items)):
        kpi(pg, x, y, w, h, it['label'], it['ref'], it.get('ctx'),
            it.get('accent', ORANGE if i % 2 == 0 else VIOLET),
            vsize=it.get('vsize', vs), lsize=ls, csize=cs,
            units=it.get('units', 1), prec=it.get('prec'),
            icon='ki_%s.png' % it['icon'] if it.get('icon') else None)

# ═══════════════════════════ P1 : NETWORK PULSE ═══════════════════════════
def page1():
    pg = Page('p1', 'Network Pulse')
    frame(pg, 'p1', 'Network Pulse',
          'One network, 700 aircraft and 180,000 vehicles, reaching more than 220 countries and territories',
          filt='#D_Hub.Continent', flabel='CONTINENT',
          fwidth=slicer_width('#D_Hub.Continent'))
    kpirow(pg, [
        dict(label='Aircraft', ref='Metrics.Aircraft', ctx='Metrics.Fleet context', icon='plane'),
        dict(label='Daily volume, m', ref='Metrics.Daily packages m', ctx='Metrics.Volume context',
             icon='parcel'),
        dict(label='Revenue, $bn', ref='Metrics.Revenue bn', ctx='Metrics.Revenue context', icon='dollar'),
        dict(label='Countries', ref='Metrics.Countries served', ctx='Metrics.Network context', icon='globe'),
        dict(label='Team members', ref='Metrics.Employees', ctx='Metrics.Employee context', icon='people'),
    ])
    a = MAP_A
    b = CW - a - 16
    panel(pg, X0, CY, a, CH)
    # Le titre a desormais son propre bandeau : l'image commence en dessous, si bien
    # qu'aucune etiquette de hub ne peut plus se retrouver sous le sous-titre.
    my = CY + MAP_TOP
    image(pg, X0 + 2, my, a - 4, MAP_H, 'network_map.png', 'Fill')
    # couche vivante : memes bornes que la projection du PNG, donc les hubs tombent juste
    mapscatter(pg, X0 + 2, my, a - 4, MAP_H,
               '#D_Hub.Hub', '#D_Hub.Longitude', '#D_Hub.Latitude',
               size='Metrics.Sort capacity', bounds=MAP_BOUNDS, bubble=-52, labels=False,
               tips=['Metrics.Sort capacity', 'Metrics.Share', 'Metrics.Sq ft'])
    text(pg, X0 + 20, CY + 14, a - 40, 32,
         [('THE GLOBAL SORTING NETWORK', 19, INK, FD)], 'left')
    text(pg, X0 + 20, CY + 46, a - 40, 28,
         [('Click any hub to filter the page : bubble size is pieces per hour', 15, MUTED, FT)],
         'left')
    table(pg, X0 + a + 16, CY, b, TOPH,
          ['#D_Hub.Hub', 'Metrics.Sort capacity', 'Metrics.Share'],
          [174, 166, 84],
          # pas de sous-titre ici : les 26 px qu'il coutait sont ceux qui manquaient au
          # graphique du dessous pour afficher sa sixieme ligne de service
          title='THE FIVE BIGGEST HUBS',
          sort='Metrics.Sort capacity', rows=5,
          vfilter=('#D_Hub.CapacityRank', 4, 5),
          tips=['Metrics.Sq ft', 'Metrics.Hub acres'])
    bar(pg, X0 + a + 16, CY + TOPH + 16, b, BOTH, '#F_Service.Service', ['Metrics.Daily packages'],
        title='WHERE THE VOLUME IS',
        sub='Average daily volume by service, thousands',
        sort='Metrics.Daily packages', fill=ORANGE, dlabels=True, catsize=14, valsize=14,
        tips=['Metrics.Service revenue', 'Metrics.Reported yield', '#F_Service.ServiceGroup'])
    return pg

# ═══════════════════════════ P2 : AIR FLEET ═══════════════════════════
AC_ART = [('B777F · 767F · A300-600', 'wide2', 'ac_wide2.png'),
          ('MD-11 trijet', 'wide3', 'ac_wide3.png'),
          ('757-200', 'narrow', 'ac_narrow.png'),
          ('ATR 42 · ATR 72', 'turbo', 'ac_turbo.png'),
          ('Cessna 208B · 408', 'single', 'ac_single.png')]

def page2():
    pg = Page('p2', 'Air Fleet')
    frame(pg, 'p2', 'Air Fleet',
          'Every aircraft, its maximum payload and how it is held : at 31 May 2026',
          filt='#D_FiscalYear.FiscalYearShort', flabel='FISCAL YEAR',
          fvfilter=('#D_FiscalYear.IsFleet', 1, 0),
          fwidth=slicer_width('#D_FiscalYear.FiscalYearShort', ('#D_FiscalYear.IsFleet', 1)))
    kpirow(pg, [
        dict(label='Aircraft', ref='Metrics.Aircraft', ctx='Metrics.Fleet context', icon='plane'),
        dict(label='Payload, M lb', ref='Metrics.Fleet payload Mlbs', ctx='Metrics.Payload context',
             icon='weight'),
        dict(label='Avg payload', ref='Metrics.Average payload', ctx='Metrics.Average payload context',
             icon='scale'),
        dict(label='Boeing built', ref='Metrics.Boeing share', ctx='Metrics.Boeing context', icon='factory'),
        dict(label='Owned', ref='Metrics.Owned share', ctx='Metrics.Owned context', icon='key'),
        dict(label='On order', ref='Metrics.Aircraft on order', ctx='Metrics.Order context', icon='order'),
    ])
    a = 1000
    b = CW - a - 16
    table(pg, X0, CY, a, CH,
          ['#D_Aircraft.Type', '#D_Aircraft.Payload', 'Metrics.Aircraft',
           'Metrics.Fleet %', 'Metrics.Total lift', 'Metrics.Lift %',
           'Metrics.vs FY23', 'Metrics.Ownership'],
          [140, 110, 88, 82, 116, 76, 96, 132],
          title='THE FLEET, TYPE BY TYPE',
          sub='Maximum payload per aircraft, the lift each type contributes, and how the count has moved since FY2023',
          sort='Metrics.Total lift', rowpad=5, rows=10,
          tips=['#D_Aircraft.Manufacturer', '#D_Aircraft.Family', '#D_Aircraft.Class',
                '#D_Aircraft.InServiceSince', 'Metrics.Aircraft on order'])
    x = X0 + a + 16
    panel(pg, x, CY, b, TOPH, 'FIVE FAMILIES', 'Drawn to relative scale')
    yy = CY + 72
    for lab, kind, png in AC_ART:
        image(pg, x + 20, yy, 34, 34, png, 'Fit')
        text(pg, x + 66, yy + 5, b - 86, 26, [(lab, 13, MUTED, FTS)], 'left')
        yy += 38
    col(pg, x, CY + TOPH + 16, b, BOTH, '#F_FleetPlan.FiscalYear',
        ['Metrics.Deliveries', 'Metrics.Retirements'],
        title='ORDER BOOK',
        sub='Deliveries and planned retirements',
        legend=True, dlabels=False, valax=True, catcategorical=True, palette=[ORANGE, ROSE])
    return pg

# ═══════════════════════════ P3 : HUBS ═══════════════════════════
def page3():
    pg = Page('p3', 'Hubs')
    frame(pg, 'p3', 'Hubs and Facilities',
          'Fifteen major sorting facilities, 17.2 million square feet, 1.2 million pieces an hour',
          filt='#D_Hub.Tier', flabel='HUB TIER',
          fwidth=slicer_width('#D_Hub.Tier'))
    kpirow(pg, [
        dict(label='Major hubs', ref='Metrics.Hubs', ctx='Metrics.Hubs context', icon='warehouse'),
        dict(label='Sort capacity, k/h', ref='Metrics.Sort capacity k', ctx='Metrics.Capacity k context',
             icon='sort'),
        dict(label='Footprint, M sq ft', ref='Metrics.Footprint Msqft', ctx='Metrics.Footprint context',
             icon='area'),
        dict(label='Land, acres', ref='Metrics.Hub acres', ctx='Metrics.Acres context', icon='land'),
        dict(label='Airports served', ref='Metrics.Airports served', ctx='Metrics.Airports context',
             icon='tower'),
    ])
    # « Tier » sortait deux fois de la page : c'est deja le segment en haut et le
    # decoupage de l'anneau. En le retirant, les lignes passent en 13pt et l'anneau
    # recupere la largeur dont ses cinq etiquettes avaient besoin.
    a = 860
    b = CW - a - 16
    table(pg, X0, CY, a, CH,
          ['#D_Hub.Hub', '#D_Hub.Country', 'Metrics.Sort capacity',
           'Metrics.Sq ft', '#D_Hub.Acres', '#D_Hub.Lease to'],
          [176, 126, 148, 126, 80, 100],
          title='EVERY MAJOR SORTING FACILITY',
          sub='Hourly capacity, floor area, land, and the year each lease runs to',
          sort='Metrics.Sort capacity', size=13, hdrsize=13, rows=15,
          tips=['#D_Hub.City', '#D_Hub.Continent', '#D_Hub.Lessor', '#D_Hub.PiecesPerSqFt'])
    # le tableau de gauche classe deja les quinze hubs par capacite : un « top six »
    # ferait doublon. On donne la place a l'anneau, qui manquait d'air pour ses
    # etiquettes, et a une lecture geographique que la page n'avait pas.
    dh, bh2 = 292, CH - 292 - 16
    donut(pg, X0 + a + 16, CY, b, dh, '#D_Hub.Tier', 'Metrics.Sort capacity',
          title='CAPACITY BY TIER',
          sub='Share of hourly sorting capacity', dlsize=12)
    bar(pg, X0 + a + 16, CY + dh + 16, b, bh2, '#D_Hub.Continent',
        ['Metrics.Footprint Msqft'],
        title='FOOTPRINT BY CONTINENT',
        sub='Sorting floor area, millions of square feet',
        sort='Metrics.Footprint Msqft', fill=VIOLET, dlabels=True, prec=1)
    return pg

# ═══════════════════════════ P4 : GROUND ═══════════════════════════
def page4():
    pg = Page('p4', 'Ground')
    frame(pg, 'p4', 'Ground Network',
          'The last mile: 180,000 vehicles, 1,085 US facilities, 530,000 team members',
          filt='#F_Network.Pillar', flabel='PILLAR',
          fwidth=slicer_width('#F_Network.Pillar'))
    kpirow(pg, [
        dict(label='Vehicles', ref='Metrics.Vehicles', ctx='Metrics.Vehicle context', icon='truck'),
        dict(label='Team members', ref='Metrics.Employees', ctx='Metrics.Employee context', icon='people'),
        dict(label='Electric vehicles', ref='Metrics.Electric vehicles', ctx='Metrics.EV context',
             icon='plug'),
        dict(label='US facilities', ref='Metrics.US facilities', ctx='Metrics.Facilities context',
             icon='building'),
        dict(label='LTL / day', ref='Metrics.LTL shipments', ctx='Metrics.LTL context',
             icon='pallet'),
    ])
    a = 892
    b = CW - a - 16
    table(pg, X0, CY, a, CH,
          ['#F_Network.Indicator', '#F_Network.Pillar', 'Metrics.Reported figure', '#F_Network.Unit'],
          [300, 130, 170, 146],
          title='THE NETWORK IN NUMBERS',
          sub='Every figure as published in the FY2026 annual report',
          sort='Metrics.Reported figure', rowpad=4, rows=11,
          vfilter=('#F_Network.IsKey', 1, 0))
    col(pg, X0 + a + 16, CY, b, HALF, '#F_Electric.FiscalYear',
        ['Metrics.Electric vehicles series'],
        title='ELECTRIFICATION',
        sub='Electric vehicles in operation, FY2022 to FY2025',
        fill=ORANGE, catcategorical=True)
    col(pg, X0 + a + 16, CY + HALF + 16, b, HALF, '#F_Freight.FiscalYear',
        ['Metrics.LTL shipments series'],
        title='LESS-THAN-TRUCKLOAD VOLUME',
        sub='FedEx Freight shipments per day',
        fill=VIOLET, catcategorical=True)
    return pg

# ═══════════════════════════ P5 : CLIMATE ═══════════════════════════
def page5():
    pg = Page('p5', 'Climate')
    frame(pg, 'p5', 'Climate and Fuel',
          'Carbon-neutral operations by 2040 : where the emissions stand and how fast intensity is falling',
          filt='#D_FiscalYear.FiscalYearShort', flabel='FISCAL YEAR',
          fvfilter=('#D_FiscalYear.IsClimate', 1, 0),
          fwidth=slicer_width('#D_FiscalYear.FiscalYearShort', ('#D_FiscalYear.IsClimate', 1)))
    kpirow(pg, [
        dict(label='Scope 1 & 2, Mt', ref='Metrics.Scope 1 and 2 Mt', ctx='Metrics.Emissions context',
             icon='cloud'),
        dict(label='Carbon intensity', ref='Metrics.Carbon intensity latest', ctx='Metrics.Intensity context',
             icon='gauge'),
        dict(label='Scope 3, Mt', ref='Metrics.Scope 3 Mt', ctx='Metrics.Scope 3 context', icon='chain'),
        dict(label='Electric vehicles', ref='Metrics.Electric vehicles', ctx='Metrics.EV context',
             icon='plug'),
        dict(label='SAF, M gallons', ref='Metrics.SAF deployed', ctx='Metrics.SAF context', icon='fuel'),
    ])
    a = 736
    b = CW - a - 16
    line(pg, X0, CY, a, HALF, '#F_Intensity.FiscalYear', ['Metrics.Carbon intensity'],
         title='SIXTEEN YEARS OF DECOUPLING',
         sub='Scope 1 and 2 emissions per million dollars of revenue, FY2009 to FY2025',
         fill=ORANGE, catcategorical=True, valax=True, catsize=14)
    bar(pg, X0, CY + HALF + 16, a, HALF, '#F_Scope3.Category', ['Metrics.Scope 3 kt'],
        title='WHERE SCOPE 3 SITS',
        sub='FY2025 categories, thousands of metric tons CO2e',
        sort='Metrics.Scope 3 kt', fill=VIOLET, dlabels=True)
    table(pg, X0 + a + 16, CY, b, CH,
          ['#D_Target.Target', '#D_Target.Due', '#D_Target.Commitment'],
          [140, 66, 248],
          title='THE COMMITMENTS',
          sub='Published targets, what each one covers, and the year it falls due',
          sort='#D_Target.Due', sortdir='Ascending', size=13, hdrsize=13, rows=9,
          tips=['#D_Target.Pillar', 'Metrics.Years to target'])
    return pg

# ═══════════════════════════ P6 : FINANCIALS ═══════════════════════════
def page6():
    pg = Page('p6', 'Financials')
    frame(pg, 'p6', 'Financials',
          'FY2026 closed at $94.7 billion, the last year consolidating FedEx Freight before the spin-off',
          filt='#D_FiscalYear.FiscalYearShort', flabel='FISCAL YEAR',
          fvfilter=('#D_FiscalYear.IsFinancial', 1, 0),
          fwidth=slicer_width('#D_FiscalYear.FiscalYearShort', ('#D_FiscalYear.IsFinancial', 1)))
    kpirow(pg, [
        dict(label='Revenue, $bn', ref='Metrics.Revenue bn', ctx='Metrics.Revenue growth context',
             icon='dollar'),
        dict(label='Op. income', ref='Metrics.Operating income', ctx='Metrics.Operating income context',
             icon='chart'),
        dict(label='Op. margin', ref='Metrics.Operating margin', ctx='Metrics.Margin context',
             icon='percent'),
        dict(label='Net income', ref='Metrics.Net income', ctx='Metrics.Net income context', icon='coin'),
        dict(label='Diluted EPS', ref='Metrics.EPS', ctx='Metrics.EPS context', icon='share'),
        dict(label='Capex', ref='Metrics.Capex', ctx='Metrics.Capex context', icon='invest'),
    ])
    a = 832
    b = CW - a - 16
    col(pg, X0, CY, a, HALF, '#D_FiscalYear.FiscalYearShort', ['Metrics.Revenue'],
        title='TWELVE YEARS OF REVENUE',
        sub='Consolidated revenue, USD millions, FY2015 to FY2026',
        fill=ORANGE, catcategorical=True, dlabels=False, valax=True)
    bar(pg, X0, CY + HALF + 16, a, HALF, '#F_Service.Service', ['Metrics.Service revenue'],
        title='REVENUE BY SERVICE LINE',
        sub='Federal Express segment, FY2026, USD millions',
        sort='Metrics.Service revenue', fill=VIOLET,
        tips=['Metrics.Daily packages', 'Metrics.Reported yield', 'Metrics.Volume growth'])
    table(pg, X0 + a + 16, CY, b, TOPH,
          ['#F_Segment.Segment', 'Metrics.Revenue, $m', 'Metrics.Op income, $m'],
          [178, 155, 170],
          title='BY SEGMENT',
          sub='FY2026 revenue and operating income, USD millions',
          sort='Metrics.Revenue, $m', size=14, hdrsize=13, rows=3,
          tips=['Metrics.Margin'])
    line(pg, X0 + a + 16, CY + TOPH + 16, b, BOTH, '#D_FiscalYear.FiscalYearShort',
         ['Metrics.Operating margin'],
         title='MARGIN THROUGH THE CYCLE',
         sub='Operating margin, FY2019 to FY2026',
         fill=ORANGE, catcategorical=True,
         vfilter=('Metrics.Operating margin', 1, 0))
    return pg

# ═══════════════════════════ P7 : ENERGY ═══════════════════════════
def page7():
    pg = Page('p7', 'Energy')
    frame(pg, 'p7', 'Energy and Consumption',
          'Every terajoule FedEx burns : jet fuel, vehicle fuel and electricity, FY2022 to FY2025',
          filt='#D_FiscalYear.FiscalYearShort', flabel='FISCAL YEAR',
          fvfilter=('#D_FiscalYear.IsEnergy', 1, 0),
          fwidth=slicer_width('#D_FiscalYear.FiscalYearShort', ('#D_FiscalYear.IsEnergy', 1)))
    kpirow(pg, [
        dict(label='Jet fuel, TJ', ref='Metrics.Jet fuel', ctx='Metrics.Jet fuel context', icon='fuel'),
        dict(label='Vehicle fuel, TJ', ref='Metrics.Vehicle fuel', ctx='Metrics.Vehicle fuel context',
             icon='truck'),
        dict(label='Electricity, TJ', ref='Metrics.Electricity used', ctx='Metrics.Electricity context',
             icon='plug'),
        dict(label='Total energy, PJ', ref='Metrics.Total energy PJ', ctx='Metrics.Total energy context',
             icon='bolt'),
        dict(label='Intensity', ref='Metrics.Energy intensity',
             ctx='Metrics.Energy intensity context', icon='gauge'),
        dict(label='Aircraft CO2', ref='Metrics.Aircraft intensity cut',
             ctx='Metrics.Aircraft cut context', icon='plane'),
    ], vs=32)
    a = 892
    b = CW - a - 16
    eh = 300                      # la colonne empilee porte une legende : il lui faut de l'air
    stackcol(pg, X0, CY, a, eh, '#D_FiscalYear.FiscalYearShort', ['Metrics.Energy by year'],
             series='#F_EnergySource.Source',
             title='WHERE THE ENERGY GOES',
             sub='Terajoules by source, FY2022 to FY2025',
             legend=True, dlabels=False, catcategorical=True, valax=True)
    col(pg, X0, CY + eh + 16, a, CH - eh - 16, '#D_FiscalYear.FiscalYearShort',
        ['Metrics.Jet fuel series'],
        title='JET FUEL, FOUR YEARS OF DECLINE',
        sub='Aviation fuel burned, terajoules',
        fill=ORANGE, catcategorical=True)
    table(pg, X0 + a + 16, CY, b, CH,
          ['#F_EnergySource.Source', '#F_EnergySource.Pillar', 'Metrics.Terajoules',
           'Metrics.Of total'],
          [126, 106, 122, 96],
          title='BY SOURCE',
          sub='Latest year, terajoules and share',
          sort='Metrics.Terajoules', size=14, rowpad=18, rows=6,
          tips=['Metrics.Total energy'])
    return pg

# ═══════════════════════════ thème ═══════════════════════════
def theme():
    return {
        "name": THEME,
        "dataColors": SERIES,
        "background": BG, "foreground": INK, "tableAccent": ORANGE,
        "good": GREEN, "neutral": AMBER, "bad": ROSE,
        "maximum": ORANGE, "center": VIOLET, "minimum": TEAL,
        "textClasses": {
            "title":    {"fontFace": FD,  "fontSize": 16, "color": INK},
            "header":   {"fontFace": FTS, "fontSize": 13, "color": INK},
            "label":    {"fontFace": FT,  "fontSize": 12, "color": MUTED},
            "callout":  {"fontFace": FD,  "fontSize": 40, "color": INK},
        },
        "visualStyles": {"*": {"*": {
            "background": [{"show": True, "color": {"solid": {"color": PANEL}}, "transparency": PANEL_A}],
            "border": [{"show": True, "color": {"solid": {"color": LINE}}, "radius": 14}],
            "outspacePane": [{"backgroundColor": {"solid": {"color": '#0A0912'}},
                              "foregroundColor": {"solid": {"color": INK}},
                              "borderColor": {"solid": {"color": LINE}}}],
            "filterCard": [{"$id": "Applied", "backgroundColor": {"solid": {"color": '#151327'}},
                            "foregroundColor": {"solid": {"color": INK}}},
                           {"$id": "Available", "backgroundColor": {"solid": {"color": '#151327'}},
                            "foregroundColor": {"solid": {"color": MUTED}}}],
        }}},
    }

# ═══════════════════════════ ressources ═══════════════════════════
def resources():
    import csv
    brand.OUT = RES
    os.makedirs(RES, exist_ok=True)
    names = brand.build(RES)
    for c in (ORANGE, VIOLET, TEAL, AMBER, GREEN, ROSE, PURPLE, '#60A5FA'):
        names.append(brand.accent(c, _accent_png(c)))
    from PIL import Image
    Image.new('RGBA', (24, 24), (16, 7, 32, 236)).save(os.path.join(RES, 'px_rail.png'))
    names.append('px_rail.png')
    Image.new('RGBA', (24, 24), (52, 25, 95, 255)).save(os.path.join(RES, 'px_railon.png'))
    names.append('px_railon.png')
    for lab, kind, png in AC_ART:
        brand.save(brand.aircraft(kind, 132, 132), png)
        names.append(png)
    # carte du réseau
    rows = list(csv.DictReader(open(os.path.join(ROOT, 'Donnees', 'D_Hub.csv'), encoding='utf-8')))
    hubs = [(r['Hub'], float(r['Latitude']), float(r['Longitude']),
             float(r['SortCapacityHr']), r['HubClass']) for r in rows]
    brand.save(brand.network_map(hubs, MAP_W, MAP_H, *MAP_BOUNDS, bubbles=False), 'network_map.png')
    names.append('network_map.png')
    # pictogrammes de KPI
    for k in ('plane', 'parcel', 'dollar', 'globe', 'people', 'weight', 'scale', 'factory', 'key',
              'order', 'warehouse', 'sort', 'area', 'land', 'tower', 'truck', 'plug', 'building',
              'pallet', 'cloud', 'gauge', 'chain', 'fuel', 'chart', 'percent', 'coin', 'share', 'bolt',
              'invest'):
        brand.save(brand.kpi_icon(k, 96, (255, 255, 255)), f'ki_{k}.png')
        names.append(f'ki_{k}.png')
    # logo fourni par l'utilisateur
    if os.path.exists(LOGO_SRC):
        brand.save(brand.fedex_logo(LOGO_SRC, 392, 112), 'fedex_logo.png')
        names.append('fedex_logo.png')
    return sorted(set(names))


def build():
    if os.path.isdir(REP):
        shutil.rmtree(REP)
    os.makedirs(RES, exist_ok=True)
    names = resources()
    pages = [page1(), page2(), page3(), page4(), page5(), page6(), page7()]
    import json
    with open(os.path.join(RES, THEME), 'w', encoding='utf-8') as f:
        json.dump(theme(), f, indent=2)
    names.append(THEME)
    write_report(REP, pages, [p.name for p in pages], THEME,
                 [n for n in names if n.endswith('.png')])
    with open(os.path.join(REP, 'definition.pbir'), 'w', encoding='utf-8') as f:
        json.dump({"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/"
                              "definitionProperties/2.0.0/schema.json",
                   "version": "4.0",
                   "datasetReference": {"byPath": {"path": "../FedEx.SemanticModel"}}}, f, indent=2)
    with open(os.path.join(ROOT, 'FedEx.pbip'), 'w', encoding='utf-8') as f:
        json.dump({"$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
                   "version": "1.0",
                   "artifacts": [{"report": {"path": "FedEx.Report"}}],
                   "settings": {"enableAutoRecovery": True}}, f, indent=2)
    nv = sum(len(p.visuals) for p in pages)
    print(f'{len(pages)} pages, {nv} visuels, {len(names)} ressources')
    for wmsg in warnings():
        print('  !! ' + wmsg)
    return pages


if __name__ == '__main__':
    build()
