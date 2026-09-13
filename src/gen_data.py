# -*- coding: utf-8 -*-
"""MERIDIAN: generation of the CSV files behind the FedEx model.
Every value comes from public FedEx sources (10-K FY2026 and FY2025, Statistical
Book Q4 FY2026 and FY2025, Corporate Responsibility reports, press releases).
No value is estimated unless the Source column says so explicitly.
"""
import csv, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Donnees')
OUT = os.path.abspath(OUT)
os.makedirs(OUT, exist_ok=True)

def w(name, header, rows):
    p = os.path.join(OUT, name + '.csv')
    with open(p, 'w', newline='', encoding='utf-8') as f:
        c = csv.writer(f, lineterminator='\n')
        c.writerow(header)
        c.writerows(rows)
    print(f'{name}.csv  {len(rows)} rows')

# ───────────────────────── D_Aircraft ─────────────────────────
# 10-K FY2026 Item 2 (owned / leased / not yet placed in service) + max gross structural payload
AC = [
    # Key, Type, Manufacturer, Family, Class, Payload lbs, Owned, Leased, NotInService, OnOrder, Order, FirstYear
    ('B777F',  'Boeing 777F',      'Boeing',  'Widebody jet',  'Trunk',  233300, 56, 3, 0, 10, 1, 2009),
    ('MD11',   'Boeing MD-11',     'Boeing',  'Trijet',        'Trunk',  192600, 29, 0, 0,  0, 2, 1991),
    ('B767F',  'Boeing 767F',      'Boeing',  'Widebody jet',  'Trunk',  127100,152, 0, 1,  0, 3, 2014),
    ('A306',   'Airbus A300-600',  'Airbus',  'Widebody jet',  'Trunk',  106600, 57, 0, 0,  0, 4, 1994),
    ('B752',   'Boeing 757-200',   'Boeing',  'Narrowbody jet','Trunk',   63000, 86, 0, 0,  0, 5, 2008),
    ('AT76F',  'ATR 72-600F',      'ATR',     'Turboprop',     'Feeder',  19290, 27, 0, 2, 15, 6, 2020),
    ('AT72',   'ATR 72',           'ATR',     'Turboprop',     'Feeder',  17970, 19, 0, 0,  0, 7, 1990),
    ('AT42',   'ATR 42',           'ATR',     'Turboprop',     'Feeder',  12070, 16, 0, 0,  0, 8, 1988),
    ('C408',   'Cessna 408','Textron','Turboprop',  'Feeder',   6000, 39, 0, 2, 11, 9, 2022),
    ('C208B',  'Cessna 208B',      'Textron', 'Turboprop',     'Feeder',   2830,216, 0, 0,  0,10, 1985),
]
rows = []
for k, t, m, fam, cls, pay, own, lea, nis, order, o, fy in AC:
    tot = own + lea
    rows.append([k, t, m, fam, cls, pay, own, lea, tot, nis, order,
                 pay * tot, 1 if m == 'Boeing' else 0, o, fy])
w('D_Aircraft',
  ['AircraftKey','AircraftType','Manufacturer','Family','FleetClass','PayloadLbs','Owned','Leased',
   'InFleet','NotInService','OnOrder','FleetPayloadLbs','IsBoeing','SortOrder','InServiceSince'],
  rows)

# ───────────────────────── F_Fleet: headcount by fiscal year ─────────────────────────
# Stat Book Q4 FY2026 (FY2024-FY2026) and Q4 FY2025 (FY2023)
FLEET = {
    'B752':  {2023:115, 2024: 92, 2025: 90, 2026: 86},
    'B767F': {2023:128, 2024:138, 2025:145, 2026:152},
    'MD11':  {2023: 46, 2024: 37, 2025: 34, 2026: 29},
    'B777F': {2023: 53, 2024: 57, 2025: 59, 2026: 59},
    'A306':  {2023: 65, 2024: 65, 2025: 58, 2026: 57},
    'C208B': {2023:234, 2024:233, 2025:226, 2026:216},
    'C408':  {2023:  9, 2024: 19, 2025: 27, 2026: 39},
    'AT72':  {2023: 19, 2024: 19, 2025: 19, 2026: 19},
    'AT76F': {2023: 13, 2024: 20, 2025: 24, 2026: 27},
    'AT42':  {2023: 18, 2024: 18, 2025: 16, 2026: 16},
}
pay = {r[0]: r[5] for r in AC}
rows = []
for k, d in FLEET.items():
    for fy, n in sorted(d.items()):
        rows.append([fy, k, n, n * pay[k]])
w('F_Fleet', ['FiscalYear','AircraftKey','Aircraft','PayloadLbs'], rows)

# ───────────────────────── F_FleetPlan: planned changes ─────────────────────────
# Stat Book Q4 FY2026: planned deliveries (+) and retirements (-) FY2027-FY2032
PLAN = {
    'B777F': {2027: 5, 2028: 5},
    'MD11':  {2028:-2, 2029:-6, 2030:-7, 2031:-7, 2032:-7},
    'C408':  {2027: 9, 2028: 2},
    'AT76F': {2027: 5, 2028: 4, 2029: 4, 2030: 2},
}
rows = []
for k, d in PLAN.items():
    for fy, n in sorted(d.items()):
        rows.append([fy, k, n, max(n,0), -min(n,0)])
w('F_FleetPlan', ['FiscalYear','AircraftKey','NetChange','Deliveries','Retirements'], rows)

# ───────────────────────── D_Hub ─────────────────────────
# 10-K FY2026 Item 2: table of major sorting facilities. Lat/lon = airport reference (WGS84).
HUBS = [
 ('MEM','Memphis SuperHub','Memphis','Tennessee','United States','North America','Primary',967,5115929,484000,'Memphis-Shelby County Airport Authority',2036,35.0424,-89.9767,1),
 ('IND','Indianapolis Hub','Indianapolis','Indiana','United States','North America','National',449,3229112,164000,'Indianapolis Airport Authority',2053,39.7173,-86.2944,2),
 ('MIA','Miami Gateway','Miami','Florida','United States','North America','National',35,284809,7000,'Aero Miami FX, LLC',2041,25.7959,-80.2870,3),
 ('AFW','Fort Worth Alliance','Fort Worth','Texas','United States','North America','Regional',168,987388,76000,'Fort Worth Alliance Airport Authority',2041,32.9876,-97.3188,4),
 ('EWR','Newark','Newark','New Jersey','United States','North America','Regional',70,634193,156000,'Port Authority of NY & NJ',2030,40.6925,-74.1687,5),
 ('OAK','Oakland','Oakland','California','United States','North America','Regional',75,587700,63000,'Port of Oakland',2036,37.7213,-122.2207,6),
 ('ORD','Chicago','Chicago','Illinois','United States','North America','Metropolitan',54,481350,21000,'City of Chicago',2028,41.9742,-87.9073,7),
 ('LAX','Los Angeles','Los Angeles','California','United States','North America','Metropolitan',34,305300,23000,'City of Los Angeles',2025,33.9416,-118.4085,8),
 ('ATL','Atlanta','Atlanta','Georgia','United States','North America','Metropolitan',35,291525,22600,'City of Atlanta',2030,33.6407,-84.4277,9),
 ('ANC','Anchorage','Anchorage','Alaska','United States','North America','International',64,417300,25000,'State of Alaska DOT&PF',2078,61.1744,-149.9964,10),
 ('CDG','Paris CDG','Roissy','Ile-de-France','France','Europe','International',123,1798368,59000,'Aeroports de Paris',2048,49.0097,2.5479,11),
 ('LGG','Liege','Liege','Wallonia','Belgium','Europe','International',23,1027952,33700,'Liege Airport',2036,50.6374,5.4432,12),
 ('CGN','Cologne','Cologne','North Rhine-Westphalia','Germany','Europe','International',14,731267,17900,'Cologne Bonn Airport',2040,50.8659,7.1427,13),
 ('CAN','Guangzhou','Guangzhou','Guangdong','China','Asia-Pacific','International',155,873006,36000,'Guangdong Airport Management Corp.',2029,23.3924,113.2988,14),
 ('KIX','Osaka','Osaka','Kansai','Japan','Asia-Pacific','International',17,425206,9000,'Kansai Airports',2029,34.4347,135.2440,15),
]
# Rank by sorting capacity, computed here rather than in DAX: a visual filter on a
# column is applied reliably by Power BI, a filter on a measure is not.
_ordre = {h[0]: i + 1 for i, h in enumerate(sorted(HUBS, key=lambda x: -x[9]))}
rows = [[h[0],h[1],h[2],h[3],h[4],h[5],h[6],h[7],h[8],h[9],h[10],h[11],h[12],h[13],h[14],
         round(h[9]/h[8],2) if h[8] else 0, _ordre[h[0]]] for h in HUBS]
w('D_Hub', ['HubKey','Hub','City','Region','Country','Continent','HubClass','Acres','SquareFeet',
            'SortCapacityHr','Lessor','LeaseExpiry','Latitude','Longitude','SortOrder',
            'PiecesPerSqFt','CapacityRank'], rows)

# ───────────────────────── F_Financial ─────────────────────────
# 10-K / XBRL SEC. Amounts in millions of USD.
FIN = [
 (2015,47453,None,None,None,4347),
 (2016,50365,None,None,None,4818),
 (2017,60319,None,None,None,5116),
 (2018,65450,None,None,None,5663),
 (2019,69693,4466, 540, 2.03,5490),
 (2020,69217,2417,1286, 4.90,5868),
 (2021,83959,5857,5231,19.45,5884),
 (2022,93512,6245,3826,14.33,6763),
 (2023,90155,4912,3972,15.48,6174),
 (2024,87693,5559,4331,17.21,5176),
 (2025,87926,5217,4092,16.81,4055),
 (2026,94720,5463,4433,18.55,3809),
]
rows = []
for fy,rev,oi,ni,eps,capex in FIN:
    rows.append([fy, f'FY{fy}', rev, oi if oi is not None else '', ni if ni is not None else '',
                 eps if eps is not None else '', capex,
                 round(oi/rev*100,2) if oi else '', round(ni/rev*100,2) if ni else '',
                 round(capex/rev*100,2)])
w('F_Financial', ['FiscalYear','FiscalYearLabel','Revenue','OperatingIncome','NetIncome','EPSDiluted',
                  'Capex','OperatingMarginPct','NetMarginPct','CapexIntensityPct'], rows)

# ───────────────────────── F_Segment ─────────────────────────
# 10-K FY2025 (recast FY2023-FY2025) and 10-K FY2026 / Stat Book FY2026 for FY2026.
SEG = [
 (2023,'Federal Express',75884,4193),(2023,'FedEx Freight',10084,1936),(2023,'Corporate & other',4187,-1217),
 (2024,'Federal Express',74663,4819),(2024,'FedEx Freight', 9429,1821),(2024,'Corporate & other',3601,-1081),
 (2025,'Federal Express',75304,4885),(2025,'FedEx Freight', 8892,1489),(2025,'Corporate & other',3730,-1157),
 (2026,'Federal Express',82273,5912),(2026,'FedEx Freight', 8795, 616),(2026,'Corporate & other',3652,-1065),
]
rows = [[fy,s,r,o, round(o/r*100,2) if r else ''] for fy,s,r,o in SEG]
w('F_Segment', ['FiscalYear','Segment','Revenue','OperatingIncome','OperatingMarginPct'], rows)

# ───────────────────────── F_Service: service lines ─────────────────────────
# Stat Book Q4 FY2026: revenue, average daily volume (thousands), yield per package.
SERV = [
 ('U.S. priority',            'U.S. domestic',      1, 11603, 1654, 26.13,  1600, 25.30),
 ('U.S. deferred',            'U.S. domestic',      2,  5700, 1061, 18.76,   968, 18.59),
 ('U.S. ground',              'U.S. domestic',      3, 37335,11205, 12.07, 10727, 11.73),
 ('International priority',   'International export',4, 9639,  562, 62.77,   622, 55.37),
 ('International economy',    'International export',5, 5925,  518, 40.87,   491, 43.33),
 ('International domestic',   'International',      6,  4725, 1806,  9.81,  1823,  9.53),
]
rows = []
for name,grp,o,rev,adv,y,adv25,y25 in SERV:
    rows.append([name,grp,o,rev,adv,y,adv25,y25, round(adv-adv25,0), round((adv/adv25-1)*100,2)])
w('F_Service', ['Service','ServiceGroup','SortOrder','Revenue','ADV','Yield','ADVPrior','YieldPrior',
                'ADVChange','ADVGrowthPct'], rows)

# ───────────────────────── F_Geography ─────────────────────────
GEO = [(2023,'United States',64890),(2023,'International',25265),
       (2024,'United States',63531),(2024,'International',24162),
       (2025,'United States',62916),(2025,'International',25010)]
w('F_Geography', ['FiscalYear','Geography','Revenue'], [[a,b,c] for a,b,c in GEO])

# ───────────────────────── F_Freight: LTL ─────────────────────────
LTL = [
 (2020,102959,272.56,None),(2021,108409,282.95,None),(2022,111699,334.57,None),
 (2023, 99720,379.76,None),(2024, 93987,376.81,946),(2025, 90083,373.52,920),(2026, 86141,386.63,931),
]
w('F_Freight', ['FiscalYear','ShipmentsPerDay','RevenuePerShipment','WeightPerShipmentLbs'],
  [[a,b,c,d if d else ''] for a,b,c,d in LTL])

# ───────────────────────── F_Climate: GHG ─────────────────────────
# Corporate Responsibility reports + Independent Accountants Review Reports (EY).
CLI = [
 (2019,15406173, 995988,16402161,235.35,'Market-based','Published'),
 (2020,15235320, 948280,16183600,233.81,'Market-based','Published'),
 (2021,16659841, 935792,17595633,209.57,'Market-based','Published'),
 (2022,None,None,17978328,192.26,'Not disclosed','Chart'),
 (2023,None,None,16723617,185.50,'Not disclosed','Chart'),
 (2024,14842148, 898484,15740632,179.50,'Location-based','Assured'),
 (2025,13932537, 952744,14885281,169.29,'Location-based','Assured'),
]
rows = []
for fy,s1,s2,tot,inten,basis,status in CLI:
    rows.append([fy, s1 if s1 else '', s2 if s2 else '', tot, inten, basis, status])
w('F_Climate', ['FiscalYear','Scope1','Scope2','Scope1and2','IntensityPerRevenueMn','Scope2Basis','DataStatus'], rows)

# Long-run intensity series FY2009-FY2025
INT = [(2009,427.28),(2010,407.38),(2011,376.36),(2012,353.68),(2013,336.43),(2014,316.26),
       (2015,310.06),(2016,292.23),(2017,251.13),(2018,247.55),(2019,235.35),(2020,233.81),
       (2021,209.57),(2022,192.26),(2023,185.50),(2024,179.50),(2025,169.29)]
w('F_Intensity', ['FiscalYear','IntensityPerRevenueMn','IndexBase2009'],
  [[fy,v, round(v/427.28*100,1)] for fy,v in INT])

# Scope 3 FY2025 by category
S3 = [('Purchased goods',2581809,1),
      ('Capital goods',1274556,2),
      ('Fuel & energy-related',3141136,3),
      ('Upstream transport',6782566,4),
      ('Business travel',195091,5),
      ('Employee commuting',903670,6)]
w('F_Scope3', ['Category','Emissions','SortOrder'], [[a,b,c] for a,b,c in S3])

# ───────────────────────── F_Electric: electric vehicles ─────────────────────────
EV = [(2022,3552),(2023,7136),(2024,8018),(2025,9446)]
w('F_Electric', ['FiscalYear','ElectricVehicles','GrowthPct'],
  [[fy,n, round((n/EV[i-1][1]-1)*100,1) if i else ''] for i,(fy,n) in enumerate(EV)])

# ───────────────────────── F_Fuel: fuel avoided and SAF ─────────────────────────
FUEL = [(2021, 65,'Fleet modernisation & fuel savings',''),
        (2022,150,'Fleet modernisation & fuel savings',''),
        (2023,147,'Fleet modernisation & fuel savings',''),
        (2025,120,'Fleet modernisation & fuel savings','')]
w('F_Fuel', ['FiscalYear','JetFuelAvoidedMnGal','Scope','Note'], [[a,b,c,d] for a,b,c,d in FUEL])

SAF = [(2024,3.0,'Reported as "more than 3 million gallons"'),(2025,16.5,'Blended SAF deployed')]
w('F_SAF', ['FiscalYear','SAFMnGal','Note'], [[a,b,c] for a,b,c in SAF])

# ───────────────────────── D_Target: targets ─────────────────────────
TGT = [
 ('Carbon-neutral operations',2040,'The whole company','Enterprise',1),
 ('Electric vehicle purchases',2030,'All parcel PUD vehicle purchases','Ground',2),
 ('Zero-emission parcel fleet',2040,'The whole parcel PUD fleet','Ground',3),
 ('Alternative aviation fuel',2030,'30% of jet fuel, blended','Air',4),
 ('Aircraft emissions intensity',2034,'-40% versus 2005','Air',5),
 ('Trijet retirement',2032,'MD-11 fleet fully retired','Air',6),
 ('Renewable electricity',2028,'500 GWh sourced','Facilities',7),
 ('Renewable electricity',2033,'1,300 GWh sourced','Facilities',8),
 ('Renewable electricity',2040,'All facility electricity','Facilities',9),
]
w('D_Target', ['Target','TargetYear','Detail','Pillar','SortOrder'], [list(t) for t in TGT])

# ───────────────────────── F_Network: network indicators ─────────────────────────
# 10-K FY2026 Item 1 & Item 2 (values as published, often approximate).
NET = [
 ('Countries & territories served',       220,   'countries', 'Reach',        1,'over 220'),
 ('Share of global GDP connected',         99,   '%',         'Reach',        2,'more than 99%'),
 ('Airports served',                      650,   'airports',  'Air',          3,'more than 650'),
 ('Aircraft in fleet',                    700,   'aircraft',  'Air',          4,'10-K FY2026'),
 ('Major sorting hubs',                    15,   'hubs',      'Air',          5,'10-K FY2026 property table'),
 ('Motorized vehicles operated',        82000,   'vehicles',  'Ground',       6,'Federal Express, approximately'),
 ('Service provider vehicles',         100000,   'vehicles',  'Ground',       7,'owned or leased by independent service providers'),
 ('Vehicles in the global network',    180000,   'vehicles',  'Ground',       8,'over 180,000'),
 ('U.S. operating facilities',           1085,   'facilities','Facilities',   9,'approximately'),
 ('Canadian sorting & distribution centres',96,  'facilities','Facilities',  10,'as reported'),
 ('International city stations',         1000,   'stations',  'Facilities',  11,'over 1,000'),
 ('FedEx Office stores',                 2000,   'stores',    'Retail',      12,'approximately'),
 ('Commercial print plants',               16,   'plants',    'Retail',      13,'as reported'),
 ('Drop boxes',                         23000,   'drop boxes','Retail',      14,'approximately'),
 ('Staffed drop-off points, U.S.',      25000,   'locations', 'Retail',      15,'approximately'),
 ('Staffed drop-off points, international',37000,'locations', 'Retail',      16,'approximately'),
 ('Permanent employees',               530000,   'people',    'People',      17,'300,000 full-time + 230,000 part-time'),
 ('Federal Express segment employees', 452000,   'people',    'People',      18,'233,000 full-time + 219,000 part-time'),
 ('Independent service providers',       5300,   'companies', 'People',      19,'approximately'),
]
KEY = {'Countries & territories served','Airports served','Vehicles in the global network',
       'Motorized vehicles operated','U.S. operating facilities','International city stations',
       'FedEx Office stores','Drop boxes','Staffed drop-off points, U.S.',
       'Staffed drop-off points, international','Permanent employees'}
w('F_Network', ['Indicator','Value','Unit','Pillar','SortOrder','Basis','IsKey'],
  [list(n) + [1 if n[0] in KEY else 0] for n in NET])

# ───────────────────────── F_People: headcount ─────────────────────────
PPL = [(2025,300000,210000,510000),(2026,300000,230000,530000)]
w('F_People', ['FiscalYear','FullTime','PartTime','Total'], [list(p) for p in PPL])


# ───────────────────────── F_Energy: consumption ─────────────────────────
# Corporate Responsibility reports 2025 (FY22-FY24) and 2026 (FY23-FY25), energy
# data tables. Published in terajoules; FedEx does not publish a volume in gallons.
ENERGY = [
 (2022, 199401, 39947, 4888, 1088, 121, 3204,  8839, 261624, 315227, None),
 (2023, 184725, 36698, 3848,  971,  80, 3114,  8842, 242513, 304179, 3.37),
 (2024, 173540, 33600, 3318,  725,  13,  149,  8983, 226307, 279376, 3.19),
 (2025, 160209, 32654, 2937,  702,  57,  956,  9888, 214849, 265065, 3.01),
]
rows = []
for fy, jet, dsl, pet, lpg, gas, bio, el, t12, t3, inten in ENERGY:
    veh = dsl + pet + lpg + gas
    rows.append([fy, jet, dsl, pet, lpg, gas, bio, veh, el, t12, t3,
                 inten if inten else '', round(jet / t12 * 100, 1)])
w('F_Energy', ['FiscalYear','JetFuel','Diesel','Petrol','LPG','GasNGV','Biodiesel',
               'VehicleFuel','Electricity','TotalEnergy','TotalInclScope3',
               'IntensityTJperMn','JetSharePct'], rows)

# Breakdown by source, for a stacked chart
SRC = [('Jet fuel', 1), ('Diesel', 2), ('Electricity', 3), ('Petrol', 4),
       ('LPG', 5), ('Natural gas', 6)]
KEY = {'Jet fuel': 1, 'Diesel': 2, 'Electricity': 8, 'Petrol': 3, 'LPG': 4, 'Natural gas': 5}
rows = []
for fy, jet, dsl, pet, lpg, gas, bio, el, t12, t3, inten in ENERGY:
    vals = {'Jet fuel': jet, 'Diesel': dsl, 'Electricity': el, 'Petrol': pet,
            'LPG': lpg, 'Natural gas': gas}
    for name, o in SRC:
        rows.append([fy, name, vals[name], o, 'Air' if name == 'Jet fuel'
                     else ('Facilities' if name in ('Electricity', 'Natural gas') else 'Ground')])
w('F_EnergySource', ['FiscalYear','Source','Energy','SortOrder','Pillar'], rows)

# ───────────────────────── F_Efficiency ─────────────────────────
# CDP Climate Change responses 2024 (FY23) and 2025 (FY24): FedEx Express scope.
EFF = [
 (2023, 0.192027, 24886538316, 4778885873, 0.303517, 1016301616, 308464775),
 (2024, 0.187650, 24330569515, 4565624482, 0.298990,  942121122, 281685013),
]
w('F_Efficiency', ['FiscalYear','AviationLperATM','AvailableTonMiles','AviationLitres',
                   'HDVLperMile','HDVMiles','HDVLitres'], [list(e) for e in EFF])

# Reduction in aircraft emissions intensity against 2005
AVI = [(2024, 30), (2025, 32)]
w('F_AviationIntensity', ['FiscalYear','ReductionVs2005Pct'], [list(a) for a in AVI])

# ───────────────────────── D_FiscalYear ─────────────────────────
rows = [[fy, f'FY{fy}', f'FY{str(fy)[2:]}', 1 if fy == 2026 else 0,
         'Year ended 31 May ' + str(fy),
         1 if 2015 <= fy <= 2026 else 0,     # published financial years
         1 if 2023 <= fy <= 2026 else 0,     # fleet years
         1 if 2019 <= fy <= 2025 else 0,     # climate years
         1 if 2022 <= fy <= 2025 else 0,     # energy years
         ] for fy in range(2015, 2027)]
w('D_FiscalYear', ['FiscalYear','FiscalYearLabel','FiscalYearShort','IsCurrent','PeriodEnd',
                   'IsFinancial','IsFleet','IsClimate','IsEnergy'], rows)

print('\nTotal fleet payload:', sum(r[11] for r in [[*x] for x in
      [[k,t,m,fam,cls,p,o,l,o+l,n,od,p*(o+l),0,0,0] for k,t,m,fam,cls,p,o,l,n,od,_,_ in AC]]), 'lbs')
