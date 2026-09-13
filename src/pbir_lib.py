# -*- coding: utf-8 -*-
"""pbir_lib : écriture directe de la couche rapport PBIR (schéma visualContainer 2.12.0).

Reconstruction pour le projet MERIDIAN (FedEx), reprenant les règles éprouvées :
  · piles CSS de polices complètes (un nom seul n'est pas résolu)
  · fontSize entières (une décimale est ignorée et retombe à 9 pt)
  · toute zone de texte >= 24 px, toute carte de mesure >= 56 px
  · title / subTitle dans visualContainerObjects
  · apostrophes doublées dans les littéraux
  · largeur de tableau : somme des colonnes <= largeur - 45
  · pas de pageBinding (casse le chargement du projet)
"""
import json, os, uuid, re, hashlib

# ─────────────────────────── identité MERIDIAN ───────────────────────────
BG      = '#170A2B'   # violet nuit FedEx
PANEL   = '#2A1250'   # panneaux
PANEL_A = 8          # transparence des panneaux
TILE    = '#34195F'   # tuiles KPI (opaques)
LINE    = '#57368E'   # bordures
ORANGE  = '#FF6600'   # orange FedEx
VIOLET  = '#B57CF6'   # violet clair, lisible sur fond sombre
PURPLE  = '#8A3FE0'   # violet soutenu
TEAL    = '#FF9248'   # orange clair (remplace le sarcelle)
AMBER   = '#FFB800'
ROSE    = '#FF4D6A'
GREEN   = '#4ADE80'
INK     = '#FFFFFF'   # texte fort
MUTED   = '#DCD2F0'   # texte courant
DIM     = '#C3B5E0'   # texte secondaire, eclairci pour la lisibilite
GRID    = '#3E2865'

SERIES = [ORANGE, VIOLET, '#FF9248', PURPLE, '#FFC48A', '#D8B4FE', AMBER, '#7C3AED', ROSE, GREEN]

FT  = "'Segoe UI', wf_segoe-ui_normal, helvetica, arial, sans-serif"
FTS = "'Segoe UI Semibold', wf_segoe-ui_semibold, helvetica, arial, sans-serif"
FTB = "'Segoe UI Bold', wf_segoe-ui_bold, helvetica, arial, sans-serif"
FD  = "'DIN', wf_standard-font, helvetica, arial, sans-serif"

W, H = 1600, 900
RAIL_W = 120
X0, X1 = 144, 1576          # zone de contenu
CW = X1 - X0                # 1432

SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.12.0/schema.json"

_warn = []
FITW = None

def warn(msg):
    _warn.append(msg)
def warnings():
    return list(_warn)

# ─────────────────────────── helpers d'expression ───────────────────────────
def esc(s):
    """Littéral texte PBIR : entouré d'apostrophes, apostrophes internes doublées."""
    return "'" + str(s).replace("'", "''") + "'"

def lit(v):
    return {"expr": {"Literal": {"Value": v}}}

def slit(s):
    return lit(esc(s))

def num(v):
    return lit(f"{v}D")

def boo(v):
    return lit("true" if v else "false")

def color(c):
    return {"solid": {"color": {"expr": {"Literal": {"Value": esc(c)}}}}}

def colmeas(entity, prop):
    return {"solid": {"color": {"expr": {"Measure": {
        "Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}}}}}

def fz(v):
    """Taille de police : toujours un entier (Power BI ignore les décimales sur les axes)."""
    return num(int(round(v)))

def fld(entity, prop, measure=True, active=None):
    kind = "Measure" if measure else "Column"
    f = {"field": {kind: {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
         "queryRef": f"{entity}.{prop}", "nativeQueryRef": prop}
    if active is not None:
        f["active"] = active
    return f

def parse(ref):
    """'Metrics.Total aircraft' -> (entity, prop, is_measure). Un préfixe '#' force une colonne."""
    m = ref.startswith('#')
    if m:
        ref = ref[1:]
    e, p = ref.split('.', 1)
    return e, p, (not m)

def agg(ref, func=1):
    """Projection agregee. func : 0 = Somme, 1 = Moyenne, 2 = Min, 3 = Max, 4 = Nombre."""
    e, p, meas = parse(ref)
    name = {0: 'Sum', 1: 'Average', 2: 'Min', 3: 'Max', 4: 'Count'}[func]
    return {"field": {"Aggregation": {
                "Expression": {("Measure" if meas else "Column"): {
                    "Expression": {"SourceRef": {"Entity": e}}, "Property": p}},
                "Function": func}},
            "queryRef": f"{name}({e}.{p})", "nativeQueryRef": f"{name} of {p}"}

def proj(ref, active=None):
    e, p, meas = parse(ref)
    return fld(e, p, meas, active)

# ─────────────────────────── enveloppes standard ───────────────────────────
def _off(*keys):
    return {k: [{"properties": {"show": boo(False)}}] for k in keys}

def vco(title=None, sub=None, panel=False, tooltip=True, radius=14, tsize=19, ssize=14,
        tcol=None, scol=None, bg=None, alpha=None):
    o = {}
    if panel:
        o["background"] = [{"properties": {"show": boo(True),
                                           "color": color(bg or PANEL),
                                           "transparency": num(PANEL_A if alpha is None else alpha)}}]
        o["border"] = [{"properties": {"show": boo(True), "color": color(LINE), "radius": num(radius)}}]
    else:
        o["background"] = [{"properties": {"show": boo(False)}}]
        o["border"] = [{"properties": {"show": boo(False)}}]
    o["dropShadow"] = [{"properties": {"show": boo(False)}}]
    o["visualHeader"] = [{"properties": {"show": boo(False)}}]
    if title:
        o["title"] = [{"properties": {"show": boo(True), "text": slit(title),
                                      "fontColor": color(tcol or INK), "fontSize": fz(tsize),
                                      "fontFamily": slit(FD), "alignment": slit("left"),
                                      "titleWrap": boo(False)}}]
    else:
        o["title"] = [{"properties": {"show": boo(False)}}]
    if sub:
        o["subTitle"] = [{"properties": {"show": boo(True), "text": slit(sub),
                                         "fontColor": color(scol or DIM), "fontSize": fz(ssize),
                                         "fontFamily": slit(FT), "alignment": slit("left")}}]
    else:
        o["subTitle"] = [{"properties": {"show": boo(False)}}]
    o["visualTooltip"] = [{"properties": {"show": boo(bool(tooltip))}}]
    return o

def measure_filter(ref, kind, value):
    """Visual-level filter on a measure. kind: 1 = >, 2 = >=, 3 = <, 4 = <=.

    The filter name is derived from the filter itself, never random: two runs of the
    build must produce byte-identical files, otherwise the repository shows phantom
    diffs on every rebuild."""
    e, p, meas = parse(ref)
    return {"filters": [{
        "name": "f" + hashlib.sha1(f'{ref}|{kind}|{value}'.encode()).hexdigest()[:8],
        "field": {("Measure" if meas else "Column"): {
            "Expression": {"SourceRef": {"Entity": e}}, "Property": p}},
        "type": "Advanced",
        "filter": {"Version": 2,
                   "From": [{"Name": "m", "Entity": e, "Type": 0}],
                   "Where": [{"Condition": {"Comparison": {
                       "ComparisonKind": kind,
                       "Left": {(("Measure") if meas else "Column"): {
                           "Expression": {"SourceRef": {"Source": "m"}}, "Property": p}},
                       "Right": {"Literal": {"Value": f"{value}D"}}}}}]}}]}

# ─────────────────────────── page ───────────────────────────
class Page:
    def __init__(self, name, display, bg_image=None):
        self.name = name
        self.display = display
        self.visuals = []
        self.n = 0
        self.bg_image = bg_image

    def add(self, v):
        v["name"] = f"{self.name}_{self.n:03d}_{v.pop('_k', 'v')}"
        v["position"]["z"] = (self.n + 1) * 1000
        v["position"]["tabOrder"] = self.n * 1000
        self.visuals.append(v)
        self.n += 1
        return v

    def json(self):
        return {
            "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json",
            "name": self.name, "displayName": self.display,
            "displayOption": "FitToPage", "height": H, "width": W,
            "objects": {
                "background": [{"properties": {"color": color(BG), "transparency": num(0)}}],
                "outspace": [{"properties": {"color": color('#07060D'), "transparency": num(0)}}],
                "displayArea": [{"properties": {"verticalAlignment": slit("Top")}}],
            },
        }

def _pos(x, y, w, h):
    return {"x": round(x), "y": round(y), "width": round(w), "height": round(h)}

# ─────────────────────────── primitives visuelles ───────────────────────────
def image(page, x, y, w, h, name, scaling="Fit"):
    return page.add({"_k": "im", "position": _pos(x, y, w, h), "visual": {
        "visualType": "image",
        "objects": {
            "general": [{"properties": {"imageUrl": {"expr": {"ResourcePackageItem": {
                "PackageName": "RegisteredResources", "PackageType": 1, "ItemName": name}}}}}],
            "imageScaling": [{"properties": {"imageScalingType": slit(scaling)}}],
        },
        "visualContainerObjects": vco(tooltip=False)}})

def text(page, x, y, w, h, runs, align="left", valign=None):
    """runs : [(texte, taille pt, couleur, police)] : hauteur minimale 24 px."""
    if h < 24:
        warn(f"{page.name}: zone de texte de {h}px (<24) -> barre de defilement")
    tr = [{"value": t, "textStyle": {"fontFamily": f, "fontSize": f"{int(round(s))}pt", "color": c}}
          for t, s, c, f in runs]
    para = {"textRuns": tr, "horizontalTextAlignment": align}
    return page.add({"_k": "tx", "position": _pos(x, y, w, h), "visual": {
        "visualType": "textbox",
        "objects": {"general": [{"properties": {"paragraphs": [para]}}]},
        "visualContainerObjects": vco(tooltip=False)}})

def label(page, x, y, w, txt, size=11, col=None, font=None, align="left", h=None):
    return text(page, x, y, w, h or max(24, int(size * 2.2)),
                [(txt, size, col or MUTED, font or FT)], align)

def panel(page, x, y, w, h, title=None, sub=None, radius=14):
    """Panneau vide (fond + bordure) posé sous un groupe de visuels."""
    return page.add({"_k": "pn", "position": _pos(x, y, w, h), "visual": {
        "visualType": "image",
        "objects": {"general": [{"properties": {"imageUrl": {"expr": {"ResourcePackageItem": {
            "PackageName": "RegisteredResources", "PackageType": 1, "ItemName": "px_panel.png"}}}}}],
            "imageScaling": [{"properties": {"imageScalingType": slit("Fill")}}]},
        "visualContainerObjects": vco(title=title, sub=sub, panel=True, tooltip=False, radius=radius)}})

def card(page, x, y, w, h, ref, size=32, col=None, font=None, align="left", wrap=False,
         fmt=None, units=None):
    """Carte de mesure. Le visuel card centre toujours sa valeur ; h >= 2.6 x taille en pt."""
    need = max(56, int(round(size * 2.6)))
    if h < need:
        warn(f"{page.name}: carte {ref} h={h} < {need} pour {size}pt -> valeur invisible")
    o = {
        "labels": [{"properties": {"color": color(col or INK), "fontSize": fz(size),
                                   "fontFamily": slit(font or FD), "alignment": slit(align)}}],
        "categoryLabels": [{"properties": {"show": boo(False)}}],
        "wordWrap": [{"properties": {"show": boo(wrap)}}],
    }
    if units is not None:
        o["labels"][0]["properties"]["labelDisplayUnits"] = num(units)
    if fmt is not None:
        o["labels"][0]["properties"]["labelPrecision"] = num(fmt)
    return page.add({"_k": "cd", "position": _pos(x, y, w, h), "visual": {
        "visualType": "card",
        "query": {"queryState": {"Values": {"projections": [proj(ref)]}}},
        "objects": o,
        "visualContainerObjects": vco(tooltip=False),
        "drillFilterOtherVisuals": True}})

# ─────────────────────────── tuile KPI ───────────────────────────
KY, KH = 110, 188

def kpi(page, x, y, w, h, lab, ref, ctx=None, accent=None, vsize=40, lsize=13, csize=13,
        units=1, prec=None, icon=None):
    """Tuile KPI : bande d'accent, pictogramme, libelle, valeur, ligne de contexte."""
    a = accent or ORANGE
    page.add({"_k": "kb", "position": _pos(x, y, w, h), "visual": {
        "visualType": "image",
        "objects": {"general": [{"properties": {"imageUrl": {"expr": {"ResourcePackageItem": {
            "PackageName": "RegisteredResources", "PackageType": 1, "ItemName": "px_tile.png"}}}}}],
            "imageScaling": [{"properties": {"imageScalingType": slit("Fill")}}]},
        "visualContainerObjects": {**_off("dropShadow", "visualHeader", "title", "subTitle"),
                                   "background": [{"properties": {"show": boo(True),
                                                                  "color": color(TILE),
                                                                  "transparency": num(0)}}],
                                   "border": [{"properties": {"show": boo(True),
                                                              "color": color(LINE), "radius": num(12)}}],
                                   "visualTooltip": [{"properties": {"show": boo(False)}}]}}})
    image(page, x, y, w, 5, _accent_png(a), scaling="Fill")
    iw = 46 if icon else 0
    text(page, x + 16, y + 15, w - 32 - iw, 26, [(lab.upper(), lsize, a, FTB)], "left")
    if icon:
        image(page, x + w - 50, y + 13, 36, 36, icon, scaling="Fit")
    ch = 56 if ctx else 12
    vh = h - 45 - ch
    card(page, x + 10, y + 45, w - 20, vh, ref, size=vsize, col=INK,
         font=FD, align="left", units=units, fmt=prec)
    if ctx:
        card(page, x + 12, y + h - ch, w - 24, ch, ctx, size=csize, col=MUTED, font=FT,
             align="left", wrap=False)

_ACC = {}
def _accent_png(c):
    return _ACC.setdefault(c, 'px_acc_%s.png' % c.lstrip('#').lower())

def accents_used():
    return dict(_ACC)

# ─────────────────────────── graphiques ───────────────────────────
def _axis(show=True, size=14, title=None, grid=False, units=1, col=None):
    p = {"show": boo(show), "labelColor": color(col or MUTED), "fontSize": fz(size),
         "fontFamily": slit(FT), "showAxisTitle": boo(bool(title)),
         "gridlineShow": boo(grid)}
    if grid:
        p["gridlineColor"] = color(GRID)
        p["gridlineThickness"] = num(1)
    if title:
        p["titleText"] = slit(title)
        p["axisTitle"] = slit(title)
        p["titleFontSize"] = fz(size)
        p["titleColor"] = color(DIM)
    p["labelDisplayUnits"] = num(units)
    return [{"properties": p}]

def _legend(show=True, size=14, pos="TopCenter"):
    return [{"properties": {"show": boo(show), "position": slit(pos),
                            "labelColor": color(MUTED), "fontSize": fz(size),
                            "fontFamily": slit(FT), "showTitle": boo(False)}}]

def _labels(show=True, size=14, col=None, units=1, prec=0, font=None):
    return [{"properties": {"show": boo(show), "color": color(col or INK), "fontSize": fz(size),
                            "fontFamily": slit(font or FTS), "labelDisplayUnits": num(units),
                            "labelPrecision": num(prec)}}]

def _dp(fill=None, measure=None):
    if measure:
        e, p, _ = parse(measure)
        c = colmeas(e, p)
    else:
        c = color(fill or ORANGE)
    return [{"properties": {"fill": c},
             "selector": {"data": [{"dataViewWildcard": {"matchingOption": 0}}]}}]

def _chart(page, vtype, x, y, w, h, cat, vals, y2=None, title=None, sub=None, legend=False,
           dlabels=True, fill=None, colmeasure=None, sort=None, sortdir="Descending",
           catsize=16, valsize=16, lsize=16, units=1, prec=0, catgrid=False, valgrid=True,
           catax=True, valax=False, cataxtitle=None, valaxtitle=None, series=None,
           vfilter=None, tooltip=True, catcategorical=False, palette=None, tips=None):
    q = {"queryState": {}}
    if cat:
        q["queryState"]["Category"] = {"projections": [proj(cat, active=True)]}
    if series:
        q["queryState"]["Series"] = {"projections": [proj(series)]}
    q["queryState"]["Y"] = {"projections": [proj(v) for v in vals]}
    if y2:
        q["queryState"]["Y2"] = {"projections": [proj(v) for v in y2]}
    if tips:
        q["queryState"]["Tooltips"] = {"projections": [proj(t) for t in tips]}
    if sort:
        e, p, meas = parse(sort)
        q["sortDefinition"] = {"sort": [{"field": {("Measure" if meas else "Column"): {
            "Expression": {"SourceRef": {"Entity": e}}, "Property": p}},
            "direction": sortdir}], "isDefaultSort": True}
    o = {
        "legend": _legend(legend, lsize),
        "categoryAxis": _axis(catax, catsize, cataxtitle, catgrid),
        "valueAxis": _axis(valax, valsize, valaxtitle, valgrid, units),
        "labels": _labels(dlabels, valsize, INK, units, prec),
    }
    if catcategorical:
        o["categoryAxis"][0]["properties"]["axisType"] = slit("Categorical")
    if y2:
        o["valueAxis"][0]["properties"].update({
            "secShow": boo(True), "secLabelColor": color(MUTED), "secFontSize": fz(valsize),
            "secShowAxisTitle": boo(False), "secLabelDisplayUnits": num(0)})
        o["y2Labels"] = _labels(False, valsize)
        o["lineStyles"] = [{"properties": {"strokeWidth": num(3), "showMarker": boo(True),
                                           "markerSize": num(5)}}]
    if colmeasure or fill or not series:
        o["dataPoint"] = _dp(fill, colmeasure)
    if palette:
        o["dataPoint"] = o.get("dataPoint", []) + [
            {"properties": {"fill": color(c)},
             "selector": {"metadata": _qref(vals[i])}} for i, c in enumerate(palette) if i < len(vals)]
    v = {"_k": "ch", "position": _pos(x, y, w, h), "visual": {
        "visualType": vtype, "query": q, "objects": o,
        "visualContainerObjects": vco(title, sub, panel=True, tooltip=tooltip),
        "drillFilterOtherVisuals": True}}
    if vfilter:
        v["filterConfig"] = measure_filter(*vfilter)
    return page.add(v)

def _qref(ref):
    e, p, _ = parse(ref)
    return f"{e}.{p}"

def bar(page, *a, **k):    return _chart(page, "barChart", *a, **k)
def col(page, *a, **k):    return _chart(page, "clusteredColumnChart", *a, **k)
def line(page, *a, **k):
    k.setdefault("valax", True); k.setdefault("dlabels", False)
    return _chart(page, "lineChart", *a, **k)
def area(page, *a, **k):
    k.setdefault("valax", True); k.setdefault("dlabels", False)
    return _chart(page, "areaChart", *a, **k)
def stackcol(page, *a, **k): return _chart(page, "columnChart", *a, **k)
def combo(page, *a, **k):    return _chart(page, "lineStackedColumnComboChart", *a, **k)
def donut(page, x, y, w, h, cat, val, title=None, sub=None, legend=False, lsize=14, dlsize=14,
          palette=None, tooltip=True):
    o = {"legend": _legend(legend, lsize),
         "labels": [{"properties": {"show": boo(True), "color": color(INK), "fontSize": fz(dlsize),
                                    "fontFamily": slit(FTS), "labelStyle": slit("Category, percent of total")}}],
         "slices": [{"properties": {"innerRadiusRatio": num(62)}}]}
    if palette:
        o["dataPoint"] = [{"properties": {"fill": color(c)},
                           "selector": {"data": [{"dataViewWildcard": {"matchingOption": 0}}]}}
                          for c in palette[:1]]
    return page.add({"_k": "dn", "position": _pos(x, y, w, h), "visual": {
        "visualType": "donutChart",
        "query": {"queryState": {"Category": {"projections": [proj(cat, active=True)]},
                                 "Y": {"projections": [proj(val)]}}},
        "objects": o,
        "visualContainerObjects": vco(title, sub, panel=True, tooltip=tooltip),
        "drillFilterOtherVisuals": True}})

def scatter(page, x, y, w, h, cat, xm, ym, size=None, title=None, sub=None, legend=False,
            bubble=-20, labels=True, fill=None, colmeasure=None, xtitle=None, ytitle=None,
            fsize=13, tooltip=True):
    q = {"queryState": {"Category": {"projections": [proj(cat, active=True)]},
                        "X": {"projections": [proj(xm)]},
                        "Y": {"projections": [proj(ym)]}}}
    if size:
        q["queryState"]["Size"] = {"projections": [proj(size)]}
    o = {"legend": _legend(legend, fsize),
         "categoryAxis": _axis(True, fsize, xtitle, True),
         "valueAxis": _axis(True, fsize, ytitle, True),
         "categoryLabels": [{"properties": {"show": boo(labels), "color": color(MUTED),
                                            "fontSize": fz(fsize), "fontFamily": slit(FT)}}],
         "bubbles": [{"properties": {"bubbleSize": num(bubble)}}],
         "dataPoint": _dp(fill, colmeasure)}
    return page.add({"_k": "sc", "position": _pos(x, y, w, h), "visual": {
        "visualType": "scatterChart", "query": q, "objects": o,
        "visualContainerObjects": vco(title, sub, panel=True, tooltip=tooltip),
        "drillFilterOtherVisuals": True}})

def mapscatter(page, x, y, w, h, cat, lon, lat, size=None, bounds=None, bubble=-8,
               labels=True, lsize=11, fill=None, tips=None):
    """Couche vivante posee sur le planisphere dessine.

    Les bornes d'axes reprennent exactement la projection du PNG (lon0, lon1, lat0, lat1),
    de sorte qu'un hub tombe au bon endroit sur les continents. Les bulles sont de vraies
    donnees : elles se filtrent, se cliquent et se redimensionnent avec le modele."""
    lo0, lo1, la0, la1 = bounds
    q = {"queryState": {"Category": {"projections": [proj(cat, active=True)]},
                        "X": {"projections": [agg(lon, 1)]},
                        "Y": {"projections": [agg(lat, 1)]}}}
    if size:
        q["queryState"]["Size"] = {"projections": [proj(size)]}
    if tips:
        q["queryState"]["Tooltips"] = {"projections": [proj(t) for t in tips]}
    cax, vax = _axis(False, 9), _axis(False, 9)
    cax[0]["properties"].update({"start": num(lo0), "end": num(lo1),
                                 "gridlineShow": boo(False), "showAxisTitle": boo(False)})
    vax[0]["properties"].update({"start": num(la0), "end": num(la1),
                                 "gridlineShow": boo(False), "showAxisTitle": boo(False)})
    o = {"legend": _legend(False, 10),
         "categoryAxis": cax, "valueAxis": vax,
         "categoryLabels": [{"properties": {"show": boo(labels), "color": color(INK),
                                            "fontSize": fz(lsize), "fontFamily": slit(FTB),
                                            "backgroundColor": color(BG),
                                            "backgroundTransparency": num(35)}}],
         "bubbles": [{"properties": {"bubbleSize": num(bubble)}}],
         "fillPoint": [{"properties": {"show": boo(True)}}],
         "dataPoint": _dp(fill or ORANGE)}
    return page.add({"_k": "sc", "position": _pos(x, y, w, h), "visual": {
        "visualType": "scatterChart", "query": q, "objects": o,
        "visualContainerObjects": vco(None, None, panel=False, tooltip=True),
        "drillFilterOtherVisuals": True}})

def mapvis(page, x, y, w, h, cat, lat, lon, size=None, title=None, sub=None, bubble=0,
           fill=None, tooltip=True, legend=False):
    q = {"queryState": {"Category": {"projections": [proj(cat, active=True)]},
                        "Y": {"projections": [agg(lat, 1)]},
                        "X": {"projections": [agg(lon, 1)]}}}
    if size:
        q["queryState"]["Size"] = {"projections": [proj(size)]}
    o = {"legend": _legend(legend, 12),
         "bubbles": [{"properties": {"bubbleSize": num(bubble)}}],
         "mapStyles": [{"properties": {"mapTheme": slit("dark")}}],
         "dataPoint": _dp(fill or ORANGE)}
    return page.add({"_k": "mp", "position": _pos(x, y, w, h), "visual": {
        "visualType": "map", "query": q, "objects": o,
        "visualContainerObjects": vco(title, sub, panel=True, tooltip=tooltip),
        "drillFilterOtherVisuals": True}})

# ─────────────────────────── tableau ───────────────────────────
HDR_ZONE = 150     # titre + sous-titre + ligne d'en-tete, mesure sur les captures
SUB_H = 26         # ce que rend un tableau sans sous-titre

def row_height(size, rowpad):
    """Hauteur reelle d'une ligne de tableEx, recalee sur les captures de l'utilisateur.

    Verifie contre quatre tableaux de tailles differentes : 13pt/rowpad 8 -> 40,5 px,
    12pt/rowpad 0 -> 22,5 px."""
    return size * 1.33 + 2 * rowpad + 7

def table(page, x, y, w, h, cols, widths, title=None, sub=None, sort=None, sortdir="Descending",
          size=13, hdrsize=13, rowpad=2, tooltip=True, vfilter=None, imageh=None,
          hdrcolor=None, align=None, rows=None, tips=None):
    """cols : liste de références. widths : largeurs en px (somme <= w - 45).
    rows : nombre de lignes attendu, pour verifier qu'aucune barre de defilement n'apparait.
    Les largeurs sont des minimums : FITW, s'il est branche, elargit toute colonne qui
    couperait son en-tete ou sa plus longue valeur."""
    # Remplissage : les lignes s'ecartent pour occuper toute la hauteur du panneau.
    # Un tableau court ne laisse plus un bloc vide sous sa derniere ligne.
    if rows:
        # 40 px de reserve : le PDF du rapport reel a montre une barre de defilement
        # sur des tableaux que le modele donnait a 97 % de remplissage
        libre = (h - 40 - (HDR_ZONE if sub else HDR_ZONE - SUB_H)) / rows - size * 1.33 - 7
        rowpad = int(max(0, min(20, libre / 2)))
    if FITW:
        widths = FITW(cols, widths, w, size, hdrsize, sort)
    s = sum(widths)
    if s > w - 45:
        warn(f"{page.name}: tableau {title!r} colonnes={s} > {w-45} -> defilement horizontal")
    if rows:
        need = (HDR_ZONE if sub else HDR_ZONE - SUB_H) + rows * row_height(size, rowpad)
        if need < h * 0.82:
            warn(f'{title or cols[0]} : {rows} lignes n\'occupent que {need:.0f} px '
                 f'sur {h} px -> panneau a moitie vide (augmenter rowpad ou size)')
        if need > h:
            warn(f"{page.name}: tableau {title!r} {rows} lignes exigent {need:.0f}px > {h}px "
                 f"-> barre de defilement")
    if len(cols) != len(widths):
        raise ValueError(f"{title}: {len(cols)} colonnes pour {len(widths)} largeurs")
    q = {"queryState": {"Values": {"projections": [proj(c) for c in cols]}}}
    if tips:
        q["queryState"]["Tooltips"] = {"projections": [proj(t) for t in tips]}
    if sort:
        e, p, meas = parse(sort)
        q["sortDefinition"] = {"sort": [{"field": {("Measure" if meas else "Column"): {
            "Expression": {"SourceRef": {"Entity": e}}, "Property": p}},
            "direction": sortdir}], "isDefaultSort": True}
    grid = {"gridVertical": boo(True), "gridVerticalColor": color(GRID), "gridVerticalWeight": num(1),
            "gridHorizontal": boo(True), "gridHorizontalColor": color(GRID), "gridHorizontalWeight": num(1),
            "rowPadding": num(rowpad), "outlineColor": color(LINE), "outlineWeight": num(1),
            "textSize": fz(size)}
    if imageh:
        grid["imageHeight"] = num(imageh)
    o = {
        "grid": [{"properties": grid}],
        "columnHeaders": [{"properties": {"fontColor": color('#FFFFFF'),
                                          "backColor": color(hdrcolor or '#241F42'),
                                          "fontSize": fz(hdrsize), "fontFamily": slit(FTB),
                                          "alignment": slit("Left"), "wordWrap": boo(False),
                                          "autoSizeColumnWidth": boo(False),
                                          "outline": slit("Frame")}}],
        "values": [{"properties": {"fontColorPrimary": color(INK), "backColorPrimary": color('#100E1E'),
                                   "fontColorSecondary": color(INK), "backColorSecondary": color('#171430'),
                                   "fontSize": fz(size), "fontFamily": slit(FT),
                                   "wordWrap": boo(False)}}],
        "total": [{"properties": {"totals": boo(False)}}],
        "columnWidth": [{"properties": {"value": num(wd)}, "selector": {"metadata": _qref(c)}}
                        for c, wd in zip(cols, widths)],
    }
    v = {"_k": "tb", "position": _pos(x, y, w, h), "visual": {
        "visualType": "tableEx", "query": q, "objects": o,
        "visualContainerObjects": vco(title, sub, panel=True, tooltip=tooltip),
        "drillFilterOtherVisuals": True}}
    if vfilter:
        v["filterConfig"] = measure_filter(*vfilter)
    return page.add(v)

# ─────────────────────────── segment ───────────────────────────
def slicer(page, x, y, w, h, ref, horizontal=True, single=True, size=13, header=False,
           padding=4, bg=None, fg=None, vfilter=None):
    o = {
        "general": [{"properties": {"orientation": num(1 if horizontal else 2),
                                    "responsive": boo(False),
                                    "outlineColor": color(LINE), "outlineWeight": num(0)}}],
        "selection": [{"properties": {"singleSelect": boo(single),
                                      "strictSingleSelect": boo(False),
                                      "selectAllCheckboxEnabled": boo(False)}}],
        "header": [{"properties": {"show": boo(header)}}],
        "items": [{"properties": {"fontColor": color(fg or MUTED), "background": color(bg or '#171430'),
                                  "fontSize": fz(size), "fontFamily": slit(FTS),
                                  "outline": slit("None"), "padding": num(padding)}}],
        "pips": [{"properties": {"show": boo(False)}}],
    }
    v = {"_k": "ss", "position": _pos(x, y, w, h), "visual": {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [proj(ref)]}}},
        "objects": o,
        "visualContainerObjects": vco(tooltip=False),
        "drillFilterOtherVisuals": True}}
    if vfilter:
        v["filterConfig"] = measure_filter(*vfilter)
    return page.add(v)

# ─────────────────────────── bouton de navigation ───────────────────────────
def navbutton(page, x, y, w, h, target, tip):
    st = lambda k, tr, cfill: {"properties": {"show": boo(True), "transparency": num(tr),
                                              "fillColor": color(cfill)},
                               "selector": {"id": k}}
    return page.add({"_k": "nb", "position": _pos(x, y, w, h), "visual": {
        "visualType": "actionButton",
        "objects": {
            "text": [{"properties": {"show": boo(False)}}] +
                    [{"properties": {"show": boo(False)}, "selector": {"id": k}}
                     for k in ("default", "hover", "selected", "disabled")],
            "icon": [{"properties": {"show": boo(False)}}] +
                    [{"properties": {"show": boo(False)}, "selector": {"id": k}}
                     for k in ("default", "hover", "selected", "disabled")],
            "outline": [{"properties": {"show": boo(False)}}] +
                       [{"properties": {"show": boo(False)}, "selector": {"id": k}}
                        for k in ("default", "hover", "selected", "disabled")],
            "glow": [{"properties": {"show": boo(False)}}],
            "shadow": [{"properties": {"show": boo(False)}}],
            "fill": [{"properties": {"show": boo(True), "transparency": num(100),
                                     "fillColor": color('#FFFFFF')}},
                     st("default", 100, '#FFFFFF'), st("hover", 86, ORANGE),
                     st("selected", 100, '#FFFFFF'), st("disabled", 100, '#FFFFFF')],
        },
        "visualContainerObjects": {
            **_off("title", "background", "border", "dropShadow"),
            "visualLink": [{"properties": {"show": boo(True), "type": slit("PageNavigation"),
                                           "navigationSection": slit(target), "tooltip": slit(tip)}}],
        },
        "drillFilterOtherVisuals": True}})

# ─────────────────────────── écriture du rapport ───────────────────────────
def write_report(root, pages, order, theme_name, images):
    rep = os.path.join(root, 'definition')
    os.makedirs(os.path.join(rep, 'pages'), exist_ok=True)
    for p in pages:
        d = os.path.join(rep, 'pages', p.name, 'visuals')
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(rep, 'pages', p.name, 'page.json'), 'w', encoding='utf-8') as f:
            json.dump(p.json(), f, indent=2, ensure_ascii=False)
        for v in p.visuals:
            vd = os.path.join(d, v["name"])
            os.makedirs(vd, exist_ok=True)
            out = {"$schema": SCHEMA, "name": v["name"], "position": v["position"],
                   "visual": v["visual"]}
            if "filterConfig" in v:
                out["filterConfig"] = v["filterConfig"]
            with open(os.path.join(vd, 'visual.json'), 'w', encoding='utf-8') as f:
                json.dump(out, f, indent=2, ensure_ascii=False)
    with open(os.path.join(rep, 'pages', 'pages.json'), 'w', encoding='utf-8') as f:
        json.dump({"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
                   "pageOrder": order, "activePageName": order[0]}, f, indent=2)
    with open(os.path.join(rep, 'version.json'), 'w', encoding='utf-8') as f:
        json.dump({"$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
                   "version": "2.0.0"}, f, indent=2)
    items = [{"name": n, "path": n, "type": "Image"} for n in sorted(images)]
    items.append({"name": theme_name, "path": theme_name, "type": "CustomTheme"})
    report = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
        "themeCollection": {
            "baseTheme": {"name": "Fluent2-CY26SU08",
                          "reportVersionAtImport": {"visual": "2.12.0", "report": "3.4.0", "page": "2.3.1"},
                          "type": "SharedResources"},
            "customTheme": {"name": theme_name,
                            "reportVersionAtImport": {"visual": "2.12.0", "report": "3.4.0", "page": "2.3.1"},
                            "type": "RegisteredResources"}},
        "objects": {
            "section": [{"properties": {"verticalAlignment": slit("Top")}}],
            "outspacePane": [{"properties": {"expanded": boo(False)}}]},
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources",
             "items": [{"name": "Fluent2-CY26SU08", "path": "BaseThemes/Fluent2-CY26SU08.json",
                        "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources", "items": items}],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                     "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
                     "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True},
    }
    with open(os.path.join(rep, 'report.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
