# -*- coding: utf-8 -*-
"""render_pages: PNG preview of the pages from the PBIR JSON, to check the layout
(overlaps, margins, over-long text) before delivery."""
import csv, json, math, os, re, glob
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
REP  = os.path.join(ROOT, 'FedEx.Report')
RES  = os.path.join(REP, 'StaticResources', 'RegisteredResources')
DATA = os.path.join(ROOT, 'Donnees')
OUT  = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'apercus'))

FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FR = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def F(sz, bold=False):
    return ImageFont.truetype(FB if bold else FR, max(6, int(sz)))

def hexc(s):
    s = (s or '#FFFFFF').strip("'").lstrip('#')
    return tuple(int(s[i:i+2], 16) for i in (0, 2, 4))

def val(o, *path):
    """Walks down a PBIR object to the literal value."""
    try:
        for p in path:
            o = o[p]
        v = o
        while isinstance(v, dict):
            if 'expr' in v: v = v['expr']
            elif 'Literal' in v: v = v['Literal']
            elif 'Value' in v: v = v['Value']
            elif 'solid' in v: v = v['solid']
            elif 'color' in v: v = v['color']
            else: return None
        if isinstance(v, str):
            v = v.strip("'")
            if v == 'true':  return True
            if v == 'false': return False
            if v.endswith('D'):
                try: return float(v[:-1])
                except Exception: return v
        return v
    except Exception:
        return None

# ─────────── real values of the measures shown in cards ───────────
def load(name):
    with open(os.path.join(DATA, name + '.csv'), encoding='utf-8') as f:
        return list(csv.DictReader(f))

def num(x):
    try: return float(x)
    except Exception: return 0.0

def compute():
    ac  = load('D_Aircraft'); fl = load('F_Fleet'); fp = load('F_FleetPlan')
    hub = load('D_Hub'); fin = load('F_Financial'); seg = load('F_Segment')
    srv = load('F_Service'); frt = load('F_Freight'); cli = load('F_Climate')
    itn = load('F_Intensity'); s3 = load('F_Scope3'); ev = load('F_Electric')
    saf = load('F_SAF'); net = load('F_Network'); ppl = load('F_People')
    ene = load('F_Energy'); esr = load('F_EnergySource'); eff = load('F_Efficiency')
    e25 = [r for r in ene if r['FiscalYear'] == '2025'][0]
    e22 = [r for r in ene if r['FiscalYear'] == '2022'][0]
    ef24 = [r for r in eff if r['FiscalYear'] == '2024'][0]

    fleet26 = [r for r in fl if r['FiscalYear'] == '2026']
    n_ac = sum(num(r['Aircraft']) for r in fleet26)
    pay  = sum(num(r['PayloadLbs']) for r in fleet26)
    owned = sum(num(r['Owned']) for r in ac); leased = sum(num(r['Leased']) for r in ac)
    boeing = sum(num(r['InFleet']) for r in ac if r['IsBoeing'] == '1')
    boeing_pay = sum(num(r['FleetPayloadLbs']) for r in ac if r['IsBoeing'] == '1')
    trunk = sum(num(r['InFleet']) for r in ac if r['FleetClass'] == 'Trunk')
    feeder = sum(num(r['InFleet']) for r in ac if r['FleetClass'] == 'Feeder')
    sortcap = sum(num(r['SortCapacityHr']) for r in hub)
    sqft = sum(num(r['SquareFeet']) for r in hub)
    f26 = [r for r in fin if r['FiscalYear'] == '2026'][0]
    adv = sum(num(r['ADV']) for r in srv); advp = sum(num(r['ADVPrior']) for r in srv)
    N = {r['Indicator']: num(r['Value']) for r in net}
    c25 = [r for r in cli if r['FiscalYear'] == '2025'][0]
    c19 = [r for r in cli if r['FiscalYear'] == '2019'][0]
    i25 = [r for r in itn if r['FiscalYear'] == '2025'][0]
    i09 = [r for r in itn if r['FiscalYear'] == '2009'][0]
    s3t = sum(num(r['Emissions']) for r in s3)
    ev25 = [r for r in ev if r['FiscalYear'] == '2025'][0]
    p26 = [r for r in ppl if r['FiscalYear'] == '2026'][0]
    frt26 = [r for r in frt if r['FiscalYear'] == '2026'][0]
    mem = [r for r in hub if r['HubKey'] == 'MEM'][0]

    f = lambda v, d=0: f'{v:,.{d}f}'
    V = {
      'Aircraft': f(n_ac), 'Fleet payload Mlbs': f(pay/1e6, 1),
      'Average payload': f(pay/n_ac), 'Boeing share': f(boeing/n_ac*100, 1) + '%',
      'Owned share': f(owned/(owned+leased)*100, 1) + '%',
      'Aircraft on order': f(sum(num(r['OnOrder']) for r in ac)),
      'Daily packages m': f(adv/1000, 1), 'Revenue bn': f(num(f26['Revenue'])/1000, 1),
      'Countries served': f(N['Countries & territories served']),
      'Employees': f(num(p26['Total'])),
      'Hubs': f(len(hub)), 'Sort capacity': f(sortcap), 'Sort capacity k': f(sortcap/1000), 'Footprint Msqft': f(sqft/1e6, 1),
      'Hub acres': f(sum(num(r['Acres']) for r in hub)),
      'Airports served': f(N['Airports served']),
      'Vehicles': f(N['Vehicles in the global network']),
      'Electric vehicles': f(num(ev25['ElectricVehicles'])),
      'US facilities': f(N['U.S. operating facilities']),
      'LTL shipments': f(num(frt26['ShipmentsPerDay'])),
      'Scope 1 and 2 Mt': f(num(c25['Scope1and2'])/1e6, 2),
      'Carbon intensity latest': f(num(i25['IntensityPerRevenueMn']), 1),
      'Scope 3 Mt': f(s3t/1e6, 2),
      'SAF deployed': f(num([r for r in saf if r['FiscalYear']=='2025'][0]['SAFMnGal']), 1),
      'Operating income': f(num(f26['OperatingIncome'])),
      'Operating margin': f(num(f26['OperatingMarginPct']), 1) + '%',
      'Net income': f(num(f26['NetIncome'])), 'EPS': '$' + f(num(f26['EPSDiluted']), 2),
      'Capex': f(num(f26['Capex'])),
      # context lines
      'Fleet context': f'{f(trunk)} trunk · {f(feeder)} feeders',
      'Payload context': f'{f(pay/2204.62)} t at full load',
      'Average payload context': f'Heaviest: {f(max(num(r["PayloadLbs"]) for r in ac))} lb',
      'Boeing context': f'{f(boeing_pay/pay*100,1)}% of lift capacity',
      'Owned context': f'Only {f(leased)} aircraft on lease',
      'Order context': f'{f(sum(num(r["NotInService"]) for r in ac))} in pre-service work',
      'Revenue context': f'{f(num(f26["OperatingMarginPct"]),1)}% margin · EPS ${f(num(f26["EPSDiluted"]),2)}',
      'Volume context': f'{(adv/advp-1)*100:+.1f}% versus prior year',
      'Hubs context': f'{f(sqft/1e6,1)}m sq ft across {len(hub)} sites',
      'Capacity k context': f'Memphis alone sorts {f(num(mem["SortCapacityHr"])/1000)}k/h',
      'Footprint context': f'Memphis alone: {f(num(mem["SquareFeet"])/1e6,1)}m sq ft',
      'Acres context': 'On four continents',
      'Airports context': 'In 220+ countries',
      'Scope 3 context': 'Six categories, FY2025',
      'Facilities context': f'{f(N["International city stations"])}+ city stations abroad',
      'Operating income context': f'Margin {f(num(f26["OperatingMarginPct"]),1)}% of revenue',
      'Margin context': 'Adjusted margin 7.0%',
      'Revenue growth context': '+7.7% on the prior year',
      'Net income context': f'Net margin {num(f26["NetIncome"])/num(f26["Revenue"])*100:.1f}%',
      'EPS context': 'Diluted, US GAAP',
      'Capex context': f'{num(f26["CapexIntensityPct"]):.1f}% of revenue',
      'Emissions context': f'{(num(c25["Scope1and2"])/num(c19["Scope1and2"])-1)*100:+.1f}% versus FY2019',
      'Intensity context': f'{(num(i25["IntensityPerRevenueMn"])/num(i09["IntensityPerRevenueMn"])-1)*100:+.1f}% since FY2009',
      'EV context': f'{num(ev25["GrowthPct"]):+.1f}% in the latest year',
      'Network context': f'{f(N["Airports served"])}+ airports · 99% of GDP',
      'Vehicle context': f'{f(N["Motorized vehicles operated"]/1000)}k own · {f(N["Service provider vehicles"]/1000)}k contracted',
      'Capacity context': f'Memphis alone sorts {f(num(mem["SortCapacityHr"]))} per hour',
      'Employee context': f'{f(num(p26["FullTime"])/1000)},000 of them full-time',
      'LTL context': f'${f(num(frt26["RevenuePerShipment"]),2)} per shipment',
      'SAF context': 'Blended at a 30% minimum',
      'Jet fuel': f(num(e25['JetFuel'])), 'Vehicle fuel': f(num(e25['VehicleFuel'])),
      'Electricity used': f(num(e25['Electricity'])),
      'Total energy PJ': f(num(e25['TotalEnergy'])/1000, 1),
      'Energy intensity': f(num(e25['IntensityTJperMn']), 2),
      'Aircraft intensity cut': '32%',
      'Aviation efficiency': f(num(ef24['AviationLperATM']), 3),
      'Jet fuel context': f'{(num(e25["JetFuel"])/num(e22["JetFuel"])-1)*100:+.1f}% since FY2022',
      'Vehicle fuel context': f'Diesel is {num(e25["Diesel"])/num(e25["VehicleFuel"])*100:.0f}% of it',
      'Electricity context': '96.7 GWh renewable',
      'Total energy context': f'{(num(e25["TotalEnergy"])/num(e22["TotalEnergy"])-1)*100:+.1f}% since FY2022',
      'Energy intensity context': 'TJ per $m of revenue',
      'Aircraft cut context': 'Intensity cut since 2005',
    }
    return V

VALUES = compute()
# the strings read in DAX from the model are authoritative: the preview must show
# exactly what Power BI displays, otherwise it lies to me about overflows
try:
    import json as _j
    _rv = _j.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    'rendered_values.json'), encoding='utf-8'))
    VALUES.update(_rv.get('cards', {}))
except Exception:
    pass

# ─────────── series for the charts ───────────
def series_for(vis):
    """Returns an approximate [(label, value)] for drawing a chart."""
    try:
        qs = vis['query']['queryState']
        cat = qs.get('Category', {}).get('projections', [{}])[0]
        cf = cat.get('field', {})
        ce = list(cf.values())[0]
        tbl = ce['Expression']['SourceRef']['Entity']; ccol = ce['Property']
        yv = qs['Y']['projections'][0]['field']
        ym = list(yv.values())[0]['Property']
    except Exception:
        return []
    MAP = {
      'Sort capacity': ('D_Hub', 'Hub', 'SortCapacityHr'), 
      'Daily packages': ('F_Service', 'Service', 'ADV'), 'Service revenue': ('F_Service', 'Service', 'Revenue'),
      'Revenue': ('F_Financial', 'FiscalYearLabel', 'Revenue'),
      'Operating margin': ('F_Financial', 'FiscalYearLabel', 'OperatingMarginPct'),
      'Scope 3': ('F_Scope3', 'Category', 'Emissions'),
      'Scope 3 kt': ('F_Scope3', 'Category', 'Emissions'),
      'vs FY2023': ('D_Aircraft', 'AircraftType', 'InFleet'),
      'Carbon intensity': ('F_Intensity', 'FiscalYear', 'IntensityPerRevenueMn'),
      'Scope 1 and 2': ('F_Climate', 'FiscalYear', 'Scope1and2'),
      'Electric vehicles series': ('F_Electric', 'FiscalYear', 'ElectricVehicles'),
      'LTL shipments series': ('F_Freight', 'FiscalYear', 'ShipmentsPerDay'),
      'LTL yield series': ('F_Freight', 'FiscalYear', 'RevenuePerShipment'),
      'Network indicator': ('F_Network', 'Indicator', 'Value'),
      'Revenue, $m': ('F_Segment', 'Segment', 'Revenue'),
      'Reported figure': ('F_Network', 'Indicator', 'Value'),
      'Terajoules': ('F_EnergySource', 'Source', 'Energy'),
      'Energy by year': ('F_EnergySource', 'FiscalYear', 'Energy'),
      'Retirements': ('F_FleetPlan', 'FiscalYear', 'Retirements'),
      'Jet fuel series': ('F_Energy', 'FiscalYear', 'JetFuel'),
      'Energy series': ('F_Energy', 'FiscalYear', 'TotalEnergy'),
      'Sq ft': ('D_Hub', 'Hub', 'SquareFeet'),
      'Footprint Msqft': ('D_Hub', 'Continent', 'SquareFeet'),
      'Deliveries': ('F_FleetPlan', 'FiscalYear', 'Deliveries'),
      'Aircraft': ('F_Fleet', 'FiscalYear', 'Aircraft'),
    }
    if ym not in MAP:
        return []
    t, lc, vc = MAP[ym]
    rows = load(t)
    agg = {}
    for r in rows:
        agg[r[lc]] = agg.get(r[lc], 0) + num(r[vc])
    out = sorted(agg.items(), key=lambda kv: -kv[1])
    return out[:16]

# ─────────── rendering ───────────
def draw_page(pdir, outfile):
    W, H = 1600, 900
    im = Image.new('RGB', (W, H), (10, 9, 18))
    d = ImageDraw.Draw(im, 'RGBA')
    vis = []
    for vf in glob.glob(os.path.join(pdir, 'visuals', '*', 'visual.json')):
        vis.append(json.load(open(vf, encoding='utf-8')))
    vis.sort(key=lambda v: v['position'].get('z', 0))
    boxes = []
    for v in vis:
        p = v['position']; x, y, w, h = p['x'], p['y'], p['width'], p['height']
        V = v['visual']; t = V['visualType']
        vco = V.get('visualContainerObjects', {})
        # panel
        if val(vco, 'background', 0, 'properties', 'show') is True:
            c = hexc(val(vco, 'background', 0, 'properties', 'color'))
            tr = val(vco, 'background', 0, 'properties', 'transparency') or 0
            d.rounded_rectangle([x, y, x + w, y + h], radius=12,
                                fill=c + (int(255 * (1 - tr / 100)),))
            bc = val(vco, 'border', 0, 'properties', 'color')
            if bc:
                d.rounded_rectangle([x, y, x + w, y + h], radius=12, outline=hexc(bc), width=1)
        ttl = val(vco, 'title', 0, 'properties', 'text')
        sub = val(vco, 'subTitle', 0, 'properties', 'text')
        ty = y + 10
        if ttl:
            ts = val(vco, 'title', 0, 'properties', 'fontSize') or 16
            d.text((x + 14, ty), ttl, font=F(ts * 1.33, True),
                   fill=hexc(val(vco, 'title', 0, 'properties', 'fontColor')))
            ty += ts * 1.7
        if sub:
            ss = val(vco, 'subTitle', 0, 'properties', 'fontSize') or 12
            d.text((x + 14, ty), sub[:120], font=F(ss * 1.30),
                   fill=hexc(val(vco, 'subTitle', 0, 'properties', 'fontColor')))
            ty += ss * 1.7
        top = ty + 6

        if t == 'image':
            nm = val(V, 'objects', 'general', 0, 'properties', 'imageUrl')
            try:
                nm = v['visual']['objects']['general'][0]['properties']['imageUrl']['expr']['ResourcePackageItem']['ItemName']
                src = Image.open(os.path.join(RES, nm)).convert('RGBA')
                sc = val(V, 'objects', 'imageScaling', 0, 'properties', 'imageScalingType')
                if sc == 'Fill':
                    src = src.resize((max(1, w), max(1, h)))
                else:
                    src.thumbnail((max(1, w), max(1, h)))
                im.paste(src, (x + (w - src.width) // 2, y + (h - src.height) // 2), src)
            except Exception:
                pass
        elif t == 'textbox':
            paras = V['objects']['general'][0]['properties']['paragraphs']
            for para in paras:
                cx = x + 6
                al = para.get('horizontalTextAlignment', 'left')
                runs = para['textRuns']
                tw = sum(F(float(r['textStyle']['fontSize'].rstrip('pt')) * 1.33,
                           'Bold' in r['textStyle']['fontFamily']).getlength(r['value']) for r in runs)
                if al == 'center': cx = x + (w - tw) / 2
                elif al == 'right': cx = x + w - tw - 6
                for r in runs:
                    fs = float(r['textStyle']['fontSize'].rstrip('pt')) * 1.33
                    fo = F(fs, 'Bold' in r['textStyle']['fontFamily'] or 'Semibold' in r['textStyle']['fontFamily'])
                    d.text((cx, y + (h - fs * 1.2) / 2), r['value'], font=fo,
                           fill=hexc(r['textStyle']['color']))
                    cx += fo.getlength(r['value'])
                    if cx > x + w + 2:
                        d.rectangle([x, y, x + w, y + h], outline=(255, 0, 0), width=2)
        elif t == 'card':
            try:
                pr = V['query']['queryState']['Values']['projections'][0]['field']
                mname = list(pr.values())[0]['Property']
            except Exception:
                mname = '?'
            s = VALUES.get(mname, mname)
            fs = (val(V, 'objects', 'labels', 0, 'properties', 'fontSize') or 20) * 1.33
            fo = F(fs, True)
            col = hexc(val(V, 'objects', 'labels', 0, 'properties', 'color'))
            wrap = val(V, 'objects', 'wordWrap', 0, 'properties', 'show')
            lines = [s]
            if wrap and fo.getlength(s) > w - 12:
                words = s.split(); lines = ['']
                for wd in words:
                    if fo.getlength((lines[-1] + ' ' + wd).strip()) > w - 12:
                        lines.append(wd)
                    else:
                        lines[-1] = (lines[-1] + ' ' + wd).strip()
            th = len(lines) * fs * 1.18
            yy = y + (h - th) / 2
            for ln in lines:
                lw = fo.getlength(ln)
                d.text((x + (w - lw) / 2, yy), ln, font=fo, fill=col)
                if lw > w:
                    d.rectangle([x, y, x + w, y + h], outline=(255, 0, 0), width=2)
                yy += fs * 1.18
            if th > h:
                d.rectangle([x, y, x + w, y + h], outline=(255, 120, 0), width=2)
        elif t == 'tableEx':
            cols = V['query']['queryState']['Values']['projections']
            widths = [val(c, 'properties', 'value') or 80 for c in V['objects']['columnWidth']]
            hs = (val(V, 'objects', 'columnHeaders', 0, 'properties', 'fontSize') or 11) * 1.33
            ts = (val(V, 'objects', 'grid', 0, 'properties', 'textSize') or 12) * 1.33
            rp = val(V, 'objects', 'grid', 0, 'properties', 'rowPadding') or 2
            hc = hexc(val(V, 'objects', 'columnHeaders', 0, 'properties', 'backColor'))
            cx = x + 8
            d.rectangle([x + 8, top, x + 8 + sum(widths), top + hs * 1.9], fill=hc + (255,))
            for c, wd in zip(cols, widths):
                nm = c.get('nativeQueryRef', '?')
                fo = F(hs, True)
                s = nm
                while fo.getlength(s) > wd - 8 and len(s) > 3:
                    s = s[:-1]
                if s != nm:
                    d.rectangle([cx, top, cx + wd, top + hs * 1.9], outline=(255, 0, 0), width=2)
                d.text((cx + 4, top + hs * 0.4), s, font=fo, fill=(255, 255, 255))
                cx += wd
            rh = ts * 1.35 + rp * 2
            n = int((y + h - (top + hs * 1.9) - 6) / rh)
            for i in range(max(0, n)):
                yy = top + hs * 1.9 + i * rh
                d.rectangle([x + 8, yy, x + 8 + sum(widths), yy + rh],
                            fill=((16, 14, 30) if i % 2 == 0 else (23, 20, 48)) + (255,))
                cx = x + 8
                for wd in widths:
                    d.line([cx, yy, cx, yy + rh], fill=(42, 38, 69))
                    d.text((cx + 4, yy + rp), '·' * max(3, int(wd / 18)), font=F(ts),
                           fill=(150, 145, 180))
                    cx += wd
            if sum(widths) > w - 45:
                d.rectangle([x, y, x + w, y + h], outline=(255, 0, 0), width=3)
        elif t == 'scatterChart' and val(V, 'objects', 'categoryAxis', 0, 'properties', 'start') is not None:
            # hub layer laid over the planisphere: drawn with the same bounds
            ax0 = float(val(V, 'objects', 'categoryAxis', 0, 'properties', 'start'))
            ax1 = float(val(V, 'objects', 'categoryAxis', 0, 'properties', 'end'))
            ay0 = float(val(V, 'objects', 'valueAxis', 0, 'properties', 'start'))
            ay1 = float(val(V, 'objects', 'valueAxis', 0, 'properties', 'end'))
            hubs = load('D_Hub')
            mxc = max(num(r['SortCapacityHr']) for r in hubs) or 1
            fo = F(11 * 1.33, True)
            for r in hubs:
                lo, la = num(r['Longitude']), num(r['Latitude'])
                px_ = x + (lo - ax0) / (ax1 - ax0) * w
                py_ = y + (ay1 - la) / (ay1 - ay0) * h
                rr = 4 + 13 * (num(r['SortCapacityHr']) / mxc) ** 0.55
                d.ellipse([px_ - rr * 2.2, py_ - rr * 2.2, px_ + rr * 2.2, py_ + rr * 2.2],
                          fill=(255, 106, 31, 40))
                d.ellipse([px_ - rr, py_ - rr, px_ + rr, py_ + rr], fill=(255, 106, 31, 240))
                if val(V, 'objects', 'categoryLabels', 0, 'properties', 'show') is True:
                    d.text((px_ + rr + 4, py_ - 8), r['Hub'], font=fo, fill=(246, 244, 255))
        elif t in ('barChart', 'columnChart', 'clusteredColumnChart', 'lineChart', 'stackedColumnChart', 'areaChart',
                   'lineStackedColumnComboChart', 'donutChart', 'map', 'scatterChart'):
            data = series_for(V)
            ax, ay = x + 14, top
            aw, ah = w - 28, y + h - top - 14
            if not data:
                d.rectangle([ax, ay, ax + aw, ay + ah], outline=(60, 55, 95), width=1)
                d.text((ax + aw / 2 - 30, ay + ah / 2), t, font=F(13), fill=(110, 104, 144))
            elif t == 'barChart':
                mx = max(v for _, v in data) or 1
                n = min(len(data), max(1, int(ah / 22)))   # real height of a category
                bh = ah / n
                for i, (k, vv) in enumerate(data[:n]):
                    yy = ay + i * bh
                    lw = 150
                    s = k
                    fo = F(13)
                    while fo.getlength(s) > lw and len(s) > 3:
                        s = s[:-1]
                    d.text((ax, yy + bh * 0.2), s, font=fo, fill=(194, 188, 217))
                    bl = (aw - lw - 60) * vv / mx
                    d.rectangle([ax + lw, yy + bh * 0.18, ax + lw + bl, yy + bh * 0.78],
                                fill=(255, 106, 31, 235))
                    d.text((ax + lw + bl + 6, yy + bh * 0.24), f'{vv:,.0f}', font=F(12),
                           fill=(246, 244, 255))
            elif t in ('columnChart', 'clusteredColumnChart', 'stackedColumnChart', 'lineStackedColumnComboChart'):
                data = sorted(data, key=lambda kv: kv[0])
                mx = max(v for _, v in data) or 1
                n = len(data)
                bw = aw / max(n, 1)
                for i, (k, vv) in enumerate(data):
                    hh = (ah - 34) * vv / mx
                    d.rectangle([ax + i * bw + bw * 0.18, ay + ah - 24 - hh,
                                 ax + i * bw + bw * 0.82, ay + ah - 24], fill=(139, 92, 246, 235))
                    fo = F(11)
                    s = str(k)
                    while fo.getlength(s) > bw and len(s) > 2:
                        s = s[:-1]
                    d.text((ax + i * bw + 2, ay + ah - 20), s, font=fo, fill=(194, 188, 217))
            elif t in ('lineChart', 'areaChart'):
                data = sorted(data, key=lambda kv: kv[0])
                mx = max(v for _, v in data) or 1
                mn = min(v for _, v in data)
                pts = []
                for i, (k, vv) in enumerate(data):
                    px = ax + aw * i / max(1, len(data) - 1)
                    py = ay + ah - 26 - (ah - 40) * (vv - mn * 0.9) / (mx - mn * 0.9 or 1)
                    pts.append((px, py))
                d.line(pts, fill=(255, 106, 31), width=3)
                for px, py in pts:
                    d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(255, 106, 31))
            elif t == 'donutChart':
                cx0, cy0 = ax + aw / 2, ay + ah / 2
                r = min(aw, ah) / 2 - 10
                tot = sum(v for _, v in data) or 1
                a0 = -90
                pal = [(255, 106, 31), (139, 92, 246), (45, 212, 191), (251, 191, 36), (96, 165, 250)]
                for i, (k, vv) in enumerate(data):
                    a1 = a0 + 360 * vv / tot
                    d.pieslice([cx0 - r, cy0 - r, cx0 + r, cy0 + r], a0, a1, fill=pal[i % 5])
                    a0 = a1
                d.ellipse([cx0 - r * 0.62, cy0 - r * 0.62, cx0 + r * 0.62, cy0 + r * 0.62],
                          fill=(21, 19, 39))
            elif t == 'map':
                d.rectangle([ax, ay, ax + aw, ay + ah], fill=(16, 20, 38, 255))
                hubs = load('D_Hub')
                for r in hubs:
                    la, lo = num(r['Latitude']), num(r['Longitude'])
                    px = ax + aw * (lo + 180) / 360
                    py = ay + ah * (90 - la) / 180
                    rr = 3 + 12 * (num(r['SortCapacityHr']) / 484000) ** 0.5
                    d.ellipse([px - rr, py - rr, px + rr, py + rr], fill=(255, 106, 31, 190))
                d.text((ax + 6, ay + ah - 18), 'map (approximate render)', font=F(11),
                       fill=(110, 104, 144))
        boxes.append((x, y, w, h, t, v['name']))
    # panel overlap check
    im.save(outfile)
    return boxes


def main():
    os.makedirs(OUT, exist_ok=True)
    files = []
    for pdir in sorted(glob.glob(os.path.join(REP, 'definition', 'pages', 'p*'))):
        if not os.path.isdir(pdir):
            continue
        name = os.path.basename(pdir)
        o = os.path.join(OUT, name + '.png')
        draw_page(pdir, o)
        files.append(o)
        print('rendered', name)
    return files

if __name__ == '__main__':
    main()
