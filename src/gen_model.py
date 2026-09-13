# -*- coding: utf-8 -*-
"""gen_model: writes the .SemanticModel (TMDL) folder of the MERIDIAN project."""
import csv, os, uuid, shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
SM   = os.path.join(ROOT, 'FedEx.SemanticModel')
DATA = os.path.join(ROOT, 'Donnees')
NS   = uuid.UUID('8f1c2c5e-0d4a-4a71-9b7e-6f3c1d2e4a55')

def lt(*k):
    return str(uuid.uuid5(NS, '|'.join(map(str, k))))

# type -> (TMDL dataType, M type, default formatString)
T = {
    'int':  ('int64',  'Int64.Type',   '#,0'),
    'num':  ('double', 'type number',  '#,0.00'),
    'txt':  ('string', 'type text',    None),
}

class Table:
    def __init__(self, name, cols, hidden=None, sortby=None, fmt=None):
        self.name = name
        self.cols = cols                 # [(column, type, csv_source_or_None)]
        self.hidden = set(hidden or [])
        self.sortby = sortby or {}
        self.fmt = fmt or {}

    def tmdl(self):
        L = [f'table {self.name}', f'\tlineageTag: {lt(self.name)}', '']
        for c, ty, src in self.cols:
            dt, _, df = T[ty]
            f = self.fmt.get(c, df)
            nm = c if c.replace(' ', '').isalnum() and ' ' not in c else f"'{c}'"
            L.append(f'\tcolumn {nm}')
            L.append(f'\t\tdataType: {dt}')
            if c in self.hidden:
                L.append('\t\tisHidden')
            if f:
                L.append(f'\t\tformatString: {f}')
            L.append(f'\t\tlineageTag: {lt(self.name, c)}')
            L.append('\t\tsummarizeBy: none')
            L.append(f'\t\tsourceColumn: {src or c}')
            if c in self.sortby:
                L.append(f'\t\tsortByColumn: {self.sortby[c]}')
            L.append('')
            L.append('\t\tannotation SummarizationSetBy = Automatic')
            L.append('')
        types = ', '.join('{"%s", %s}' % (src or c, T[ty][1]) for c, ty, src in self.cols)
        L += [
            f'\tpartition {self.name} = m',
            '\t\tmode: import',
            '\t\tsource =',
            '\t\t\t\tlet',
            f'\t\t\t\t    Source = Csv.Document(File.Contents(DossierDonnees & "\\{self.name}.csv"), '
            '[Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
            '\t\t\t\t    Entetes = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),',
            f'\t\t\t\t    Types = Table.TransformColumnTypes(Entetes, {{{types}}}, "en-US")',
            '\t\t\t\tin',
            '\t\t\t\t    Types',
            '',
            '\tannotation PBI_ResultType = Table',
            '',
        ]
        return '\n'.join(L)

I, N, X = 'int', 'num', 'txt'

TABLES = [
 Table('D_FiscalYear', [('FiscalYear', I, None), ('FiscalYearLabel', X, None),
                        ('FiscalYearShort', X, None), ('IsCurrent', I, None), ('PeriodEnd', X, None),
                        ('IsFinancial', I, None), ('IsFleet', I, None), ('IsClimate', I, None),
                        ('IsEnergy', I, None)],
       hidden=['IsCurrent', 'IsFinancial', 'IsFleet', 'IsClimate', 'IsEnergy'],
       sortby={'FiscalYearLabel': 'FiscalYear', 'FiscalYearShort': 'FiscalYear'},
       fmt={'FiscalYear': '0'}),

 Table('D_Aircraft', [('AircraftKey', X, None), ('Type', X, 'AircraftType'), ('Manufacturer', X, None),
                      ('Family', X, None), ('Class', X, 'FleetClass'), ('Payload', I, 'PayloadLbs'),
                      ('Owned', I, None), ('Leased', I, None), ('InFleet', I, None),
                      ('NotInService', I, None), ('OnOrder', I, None), ('FleetPayloadLbs', I, None),
                      ('IsBoeing', I, None), ('SortOrder', I, None), ('InServiceSince', I, None)],
       hidden=['AircraftKey', 'IsBoeing', 'SortOrder'],
       sortby={'Type': 'SortOrder'}, fmt={'InServiceSince': '0'}),

 Table('F_Fleet', [('FiscalYear', I, None), ('AircraftKey', X, None), ('Aircraft', I, None),
                   ('PayloadLbs', I, None)], hidden=['AircraftKey'], fmt={'FiscalYear': '0'}),

 Table('F_FleetPlan', [('FiscalYear', I, None), ('AircraftKey', X, None), ('NetChange', I, None),
                       ('Deliveries', I, None), ('Retirements', I, None)],
       hidden=['AircraftKey'], fmt={'FiscalYear': '0'}),

 Table('D_Hub', [('HubKey', X, None), ('Hub', X, None), ('City', X, None), ('Region', X, None),
                 ('Country', X, None), ('Continent', X, None), ('Tier', X, 'HubClass'),
                 ('Acres', I, None), ('Floor area', I, 'SquareFeet'), ('Sort capacity /h', I, 'SortCapacityHr'),
                 ('Lessor', X, None), ('Lease to', I, 'LeaseExpiry'), ('Latitude', N, None),
                 ('Longitude', N, None), ('SortOrder', I, None), ('PiecesPerSqFt', N, None),
                 ('CapacityRank', I, None)],
       hidden=['HubKey', 'SortOrder', 'CapacityRank'], sortby={'Hub': 'SortOrder'},
       fmt={'Lease to': '0', 'Latitude': '0.0000', 'Longitude': '0.0000', 'PiecesPerSqFt': '0.00'}),

 Table('F_Financial', [('FiscalYear', I, None), ('FiscalYearLabel', X, None), ('Revenue', I, None),
                       ('OperatingIncome', I, None), ('NetIncome', I, None), ('EPSDiluted', N, None),
                       ('Capex', I, None), ('OperatingMarginPct', N, None), ('NetMarginPct', N, None),
                       ('CapexIntensityPct', N, None)],
       hidden=['FiscalYearLabel'], fmt={'FiscalYear': '0', 'EPSDiluted': '#,0.00'}),

 Table('F_Segment', [('FiscalYear', I, None), ('Segment', X, None), ('Revenue', I, None),
                     ('OperatingIncome', I, None), ('OperatingMarginPct', N, None)],
       fmt={'FiscalYear': '0'}),

 Table('F_Service', [('Service', X, None), ('ServiceGroup', X, None), ('SortOrder', I, None),
                     ('Revenue', I, None), ('Daily volume (k)', I, 'ADV'), ('Yield ($)', N, 'Yield'),
                     ('ADVPrior', I, None), ('YieldPrior', N, None), ('ADVChange', I, None),
                     ('ADVGrowthPct', N, None)],
       hidden=['SortOrder'], sortby={'Service': 'SortOrder'},
       fmt={'Yield ($)': '$#,0.00', 'YieldPrior': '$#,0.00'}),

 Table('F_Geography', [('FiscalYear', I, None), ('Geography', X, None), ('Revenue', I, None)],
       fmt={'FiscalYear': '0'}),

 Table('F_Freight', [('FiscalYear', I, None), ('ShipmentsPerDay', I, None),
                     ('RevenuePerShipment', N, None), ('WeightPerShipmentLbs', I, None)],
       fmt={'FiscalYear': '0', 'RevenuePerShipment': '$#,0.00'}),

 Table('F_Climate', [('FiscalYear', I, None), ('Scope1', I, None), ('Scope2', I, None),
                     ('Scope1and2', I, None), ('IntensityPerRevenueMn', N, None),
                     ('Scope2Basis', X, None), ('DataStatus', X, None)],
       fmt={'FiscalYear': '0', 'IntensityPerRevenueMn': '#,0.00'}),

 Table('F_Intensity', [('FiscalYear', I, None), ('IntensityPerRevenueMn', N, None),
                       ('IndexBase2009', N, None)],
       fmt={'FiscalYear': '0', 'IntensityPerRevenueMn': '#,0.00', 'IndexBase2009': '#,0.0'}),

 Table('F_Scope3', [('Category', X, None), ('Emissions', I, None), ('SortOrder', I, None)],
       hidden=['SortOrder'], sortby={'Category': 'SortOrder'}),

 Table('F_Electric', [('FiscalYear', I, None), ('ElectricVehicles', I, None), ('GrowthPct', N, None)],
       fmt={'FiscalYear': '0', 'GrowthPct': '#,0.0'}),

 Table('F_Fuel', [('FiscalYear', I, None), ('JetFuelAvoidedMnGal', I, None), ('Scope', X, None),
                  ('Note', X, None)], hidden=['Note'], fmt={'FiscalYear': '0'}),

 Table('F_SAF', [('FiscalYear', I, None), ('SAFMnGal', N, None), ('Note', X, None)],
       hidden=['Note'], fmt={'FiscalYear': '0', 'SAFMnGal': '#,0.0'}),

 Table('D_Target', [('Target', X, None), ('Due', I, 'TargetYear'), ('Commitment', X, 'Detail'),
                    ('Pillar', X, None), ('SortOrder', I, None)],
       hidden=['SortOrder'], sortby={'Target': 'SortOrder'}, fmt={'Due': '0'}),

 Table('F_Network', [('Indicator', X, None), ('Value', I, None), ('Unit', X, None),
                     ('Pillar', X, None), ('SortOrder', I, None), ('Basis', X, None), ('IsKey', I, None)],
       hidden=['SortOrder', 'Value', 'IsKey'], sortby={'Indicator': 'SortOrder'}),

 Table('F_People', [('FiscalYear', I, None), ('FullTime', I, None), ('PartTime', I, None),
                    ('Total', I, None)], fmt={'FiscalYear': '0'}),

 Table('F_Energy', [('FiscalYear', I, None), ('JetFuel', I, None), ('Diesel', I, None),
                    ('Petrol', I, None), ('LPG', I, None), ('GasNGV', I, None),
                    ('Biodiesel', I, None), ('VehicleFuel', I, None), ('Electricity', I, None),
                    ('TotalEnergy', I, None), ('TotalInclScope3', I, None),
                    ('IntensityTJperMn', N, None), ('JetSharePct', N, None)],
       fmt={'FiscalYear': '0', 'IntensityTJperMn': '#,0.00', 'JetSharePct': '#,0.0'}),

 Table('F_EnergySource', [('FiscalYear', I, None), ('Source', X, None), ('Energy', I, None),
                          ('SortOrder', I, None), ('Pillar', X, None)],
       hidden=['SortOrder'], sortby={'Source': 'SortOrder'}, fmt={'FiscalYear': '0'}),

 Table('F_Efficiency', [('FiscalYear', I, None), ('AviationLperATM', N, None),
                        ('AvailableTonMiles', I, None), ('AviationLitres', I, None),
                        ('HDVLperMile', N, None), ('HDVMiles', I, None), ('HDVLitres', I, None)],
       fmt={'FiscalYear': '0', 'AviationLperATM': '#,0.0000', 'HDVLperMile': '#,0.0000'}),

 Table('F_AviationIntensity', [('FiscalYear', I, None), ('ReductionVs2005Pct', I, None)],
       fmt={'FiscalYear': '0'}),
]

RELATIONS = [
 ('F_Fleet', 'AircraftKey', 'D_Aircraft', 'AircraftKey'),
 ('F_FleetPlan', 'AircraftKey', 'D_Aircraft', 'AircraftKey'),
 ('F_Fleet', 'FiscalYear', 'D_FiscalYear', 'FiscalYear'),
 ('F_Financial', 'FiscalYear', 'D_FiscalYear', 'FiscalYear'),
 ('F_Segment', 'FiscalYear', 'D_FiscalYear', 'FiscalYear'),
 ('F_Geography', 'FiscalYear', 'D_FiscalYear', 'FiscalYear'),
 ('F_Freight', 'FiscalYear', 'D_FiscalYear', 'FiscalYear'),
 ('F_Climate', 'FiscalYear', 'D_FiscalYear', 'FiscalYear'),
 ('F_Electric', 'FiscalYear', 'D_FiscalYear', 'FiscalYear'),
 ('F_Fuel', 'FiscalYear', 'D_FiscalYear', 'FiscalYear'),
 ('F_SAF', 'FiscalYear', 'D_FiscalYear', 'FiscalYear'),
 ('F_People', 'FiscalYear', 'D_FiscalYear', 'FiscalYear'),
 ('F_Energy', 'FiscalYear', 'D_FiscalYear', 'FiscalYear'),
 ('F_EnergySource', 'FiscalYear', 'D_FiscalYear', 'FiscalYear'),
]

# ─────────────────────────── measures ───────────────────────────
# (name, DAX expression, formatString, folder, description)
M = []
def m(name, expr, fmt='#,0', folder='', desc=None):
    M.append((name, ' '.join(expr.split()) if '\n' not in expr else expr, fmt, folder, desc))

F_FLEET = '01 Fleet'
F_PAY   = '02 Payload & capacity'
F_MIX   = '03 Fleet mix'
F_HUB   = '04 Hubs & network'
F_FIN   = '05 Financial'
F_VOL   = '06 Volumes & yield'
F_CLI   = '07 Climate'
F_TXT   = '08 Narrative'

# fleet
m('Aircraft', 'VAR y = MAX ( F_Fleet[FiscalYear] ) RETURN CALCULATE ( SUM ( F_Fleet[Aircraft] ), F_Fleet[FiscalYear] = y )', '#,0', F_FLEET, 'Aircraft in the fleet at the close of the fiscal year in context.')
m('Aircraft LY', 'CALCULATE ( [Aircraft], D_FiscalYear[FiscalYear] = MAX ( F_Fleet[FiscalYear] ) - 1 )', '#,0', F_FLEET)
m('Aircraft change', '[Aircraft] - [Aircraft LY]', '+#,0;-#,0;0', F_FLEET)
m('Fleet total', 'CALCULATE ( [Aircraft], REMOVEFILTERS ( D_Aircraft ) )', '#,0', F_FLEET)
m('Aircraft owned', 'SUM ( D_Aircraft[Owned] )', '#,0', F_FLEET)
m('Aircraft leased', 'SUM ( D_Aircraft[Leased] )', '#,0', F_FLEET)
m('Aircraft on order', 'SUM ( D_Aircraft[OnOrder] )', '#,0', F_FLEET)
m('Aircraft in modification', 'SUM ( D_Aircraft[NotInService] )', '#,0', F_FLEET,
  'Delivered aircraft undergoing pre-service modification at 31 May 2026.')
m('Owned share', 'DIVIDE ( [Aircraft owned], [Aircraft owned] + [Aircraft leased] )', '0.0%', F_MIX)
m('Leased share', 'DIVIDE ( [Aircraft leased], [Aircraft owned] + [Aircraft leased] )', '0.0%', F_MIX)
m('Trunk aircraft', 'CALCULATE ( [Aircraft], D_Aircraft[Class] = "Trunk" )', '#,0', F_MIX)
m('Feeder aircraft', 'CALCULATE ( [Aircraft], D_Aircraft[Class] = "Feeder" )', '#,0', F_MIX)
m('Trunk share', 'DIVIDE ( [Trunk aircraft], [Fleet total] )', '0.0%', F_MIX)
m('Boeing aircraft', 'CALCULATE ( [Aircraft], D_Aircraft[IsBoeing] = 1 )', '#,0', F_MIX)
m('Boeing share', 'DIVIDE ( CALCULATE ( [Aircraft], D_Aircraft[IsBoeing] = 1, REMOVEFILTERS ( D_Aircraft ) ), [Fleet total] )',
  '0.0%', F_MIX, 'Share of the total fleet built by Boeing, including the MD-11 trijet.')
m('Manufacturer share', 'DIVIDE ( [Aircraft], [Fleet total] )', '0.0%', F_MIX)

# payload
m('Fleet payload lbs', 'VAR y = MAX ( F_Fleet[FiscalYear] ) RETURN CALCULATE ( SUM ( F_Fleet[PayloadLbs] ), F_Fleet[FiscalYear] = y )', '#,0', F_PAY,
  'Sum of maximum gross structural payload across every aircraft in the fleet.')
m('Fleet payload Mlbs', 'DIVIDE ( [Fleet payload lbs], 1000000 )', '#,0.0', F_PAY)
m('Fleet payload tonnes', 'DIVIDE ( [Fleet payload lbs], 2204.62 )', '#,0', F_PAY)
m('Payload total', 'CALCULATE ( [Fleet payload lbs], REMOVEFILTERS ( D_Aircraft ) )', '#,0', F_PAY)
m('Average payload', 'DIVIDE ( [Fleet payload lbs], [Aircraft] )', '#,0', F_PAY,
  'Average maximum payload per aircraft, in pounds.')
m('Type payload', 'SUM ( D_Aircraft[Payload] )', '#,0', F_PAY)
m('Payload share', 'DIVIDE ( [Fleet payload lbs], [Payload total] )', '0.0%', F_PAY)
m('Boeing payload share',
  'DIVIDE ( CALCULATE ( [Fleet payload lbs], D_Aircraft[IsBoeing] = 1, REMOVEFILTERS ( D_Aircraft ) ), [Payload total] )',
  '0.0%', F_PAY)
m('Trunk payload share',
  'DIVIDE ( CALCULATE ( [Fleet payload lbs], D_Aircraft[Class] = "Trunk", REMOVEFILTERS ( D_Aircraft ) ), [Payload total] )',
  '0.0%', F_PAY)
m('Payload per aircraft type', 'AVERAGE ( D_Aircraft[Payload] )', '#,0', F_PAY)

# fleet plan
m('Deliveries', 'SUM ( F_FleetPlan[Deliveries] )', '#,0', F_FLEET)
m('Retirements', 'SUM ( F_FleetPlan[Retirements] )', '#,0', F_FLEET)
m('Net fleet change', 'SUM ( F_FleetPlan[NetChange] )', '+#,0;-#,0;0', F_FLEET)

# hubs
m('Hubs', 'COUNTROWS ( D_Hub )', '#,0', F_HUB)
m('Sort capacity', 'SUM ( D_Hub[Sort capacity /h] )', '#,0', F_HUB,
  'Combined hourly sorting capacity of the major sorting facilities, in pieces per hour.')
m('Sort capacity k', 'DIVIDE ( [Sort capacity], 1000 )', '#,0', F_HUB)
m('Sq ft', 'SUM ( D_Hub[Floor area] )', '#,0', F_HUB)
m('Footprint Msqft', 'DIVIDE ( [Sq ft], 1000000 )', '#,0.0', F_HUB)
m('Hub acres', 'SUM ( D_Hub[Acres] )', '#,0', F_HUB)
m('Share', 'DIVIDE ( [Sort capacity], CALCULATE ( [Sort capacity], REMOVEFILTERS ( D_Hub ) ) )', '0.0%', F_HUB)
m('Years to lease expiry', 'MIN ( D_Hub[Lease to] ) - 2026', '#,0', F_HUB)
m('Scope 3 kt', 'DIVIDE ( [Scope 3], 1000 )', '#,0', F_CLI,
  'Scope 3 emissions in thousands of metric tons, for readable chart labels.')
m('Fleet change abs', 'ABS ( [vs FY23] )', '#,0', F_FLEET)
m('Payload Mlb by type', 'DIVIDE ( [Fleet payload lbs], 1000000 )', '#,0.0', F_PAY)
m('Sq ft k', 'DIVIDE ( [Sq ft], 1000 )', '#,0', F_HUB)
m('Total lift', '[Fleet payload lbs]', '#,0', F_PAY)
m('Area rank', 'RANKX ( ALL ( D_Hub[Hub] ), [Sq ft],, DESC )', '0', F_HUB)
m('vs FY23',
  'VAR b = CALCULATE ( [Aircraft], REMOVEFILTERS ( D_FiscalYear ), F_Fleet[FiscalYear] = 2023 ) '
  'VAR n = CALCULATE ( [Aircraft], REMOVEFILTERS ( D_FiscalYear ), F_Fleet[FiscalYear] = 2026 ) '
  'RETURN n - b', '+#,0;-#,0;0', F_FLEET, 'Change in the number of aircraft of each type between FY2023 and FY2026.')
m('Hub rank', 'RANKX ( ALL ( D_Hub[Hub] ), [Sort capacity],, DESC )', '0', F_HUB)

# network
def net(label, ind, fmt='#,0'):
    m(label, f'CALCULATE ( SUM ( F_Network[Value] ), F_Network[Indicator] = "{ind}" )', fmt, F_HUB)
net('Countries served', 'Countries & territories served')
net('Airports served', 'Airports served')
net('Vehicles', 'Vehicles in the global network')
net('Own vehicles', 'Motorized vehicles operated')
net('Provider vehicles', 'Service provider vehicles')
net('US facilities', 'U.S. operating facilities')
net('Drop boxes', 'Drop boxes')
net('Retail points US', 'Staffed drop-off points, U.S.')
net('Retail points intl', 'Staffed drop-off points, international')
net('Office stores', 'FedEx Office stores')
net('City stations', 'International city stations')
m('Retail points', '[Retail points US] + [Retail points intl] + [Drop boxes]', '#,0', F_HUB)
m('Reported figure', 'SUM ( F_Network[Value] )', '#,0', F_HUB)

# headcount
m('Employees', 'CALCULATE ( SUM ( F_People[Total] ), F_People[FiscalYear] = MAX ( F_People[FiscalYear] ) )', '#,0', F_HUB)
m('Full-time employees', 'CALCULATE ( SUM ( F_People[FullTime] ), F_People[FiscalYear] = MAX ( F_People[FiscalYear] ) )', '#,0', F_HUB)
m('Part-time employees', 'CALCULATE ( SUM ( F_People[PartTime] ), F_People[FiscalYear] = MAX ( F_People[FiscalYear] ) )', '#,0', F_HUB)

# finance
m('Revenue', 'VAR y = MAX ( F_Financial[FiscalYear] ) RETURN CALCULATE ( SUM ( F_Financial[Revenue] ), F_Financial[FiscalYear] = y )', '#,0', F_FIN, 'Consolidated revenue for the fiscal year in context, USD millions.')
m('Revenue bn', 'DIVIDE ( [Revenue], 1000 )', '#,0.0', F_FIN)
m('Revenue LY', 'CALCULATE ( [Revenue], D_FiscalYear[FiscalYear] = MAX ( F_Financial[FiscalYear] ) - 1 )', '#,0', F_FIN)
m('Revenue growth', 'DIVIDE ( [Revenue] - [Revenue LY], [Revenue LY] )', '+0.0%;-0.0%;0.0%', F_FIN)
m('Operating income', 'VAR y = MAX ( F_Financial[FiscalYear] ) RETURN CALCULATE ( SUM ( F_Financial[OperatingIncome] ), F_Financial[FiscalYear] = y )', '#,0', F_FIN)
m('Operating margin', 'DIVIDE ( [Operating income], [Revenue] )', '0.0%', F_FIN)
m('Net income', 'VAR y = MAX ( F_Financial[FiscalYear] ) RETURN CALCULATE ( SUM ( F_Financial[NetIncome] ), F_Financial[FiscalYear] = y )', '#,0', F_FIN)
m('Net margin', 'DIVIDE ( [Net income], [Revenue] )', '0.0%', F_FIN)
m('EPS', 'VAR y = MAX ( F_Financial[FiscalYear] ) RETURN CALCULATE ( SUM ( F_Financial[EPSDiluted] ), F_Financial[FiscalYear] = y )', '$#,0.00', F_FIN)
m('Capex', 'VAR y = MAX ( F_Financial[FiscalYear] ) RETURN CALCULATE ( SUM ( F_Financial[Capex] ), F_Financial[FiscalYear] = y )', '#,0', F_FIN)
m('Capex intensity', 'DIVIDE ( [Capex], [Revenue] )', '0.0%', F_FIN)
m('Revenue, $m', 'VAR y = MAX ( F_Segment[FiscalYear] ) RETURN CALCULATE ( SUM ( F_Segment[Revenue] ), F_Segment[FiscalYear] = y )', '#,0', F_FIN)
m('Op income, $m', 'VAR y = MAX ( F_Segment[FiscalYear] ) RETURN CALCULATE ( SUM ( F_Segment[OperatingIncome] ), F_Segment[FiscalYear] = y )', '#,0', F_FIN)
m('Margin', 'DIVIDE ( [Op income, $m], [Revenue, $m] )', '0.0%', F_FIN)
m('Segment share', 'DIVIDE ( [Revenue, $m], CALCULATE ( [Revenue, $m], REMOVEFILTERS ( F_Segment[Segment] ) ) )', '0.0%', F_FIN)
m('Geography revenue', 'VAR y = MAX ( F_Geography[FiscalYear] ) RETURN CALCULATE ( SUM ( F_Geography[Revenue] ), F_Geography[FiscalYear] = y )', '#,0', F_FIN)
m('Geography share', 'DIVIDE ( [Geography revenue], CALCULATE ( [Geography revenue], REMOVEFILTERS ( F_Geography[Geography] ) ) )', '0.0%', F_FIN)

# volumes
m('Service revenue', 'SUM ( F_Service[Revenue] )', '#,0', F_VOL)
m('Daily packages', 'SUM ( F_Service[Daily volume (k)] )', '#,0', F_VOL, 'Average daily package volume, thousands of packages.')
m('Daily packages m', 'DIVIDE ( [Daily packages], 1000 )', '#,0.0', F_VOL)
m('Daily packages LY', 'SUM ( F_Service[ADVPrior] )', '#,0', F_VOL)
m('Volume growth', 'DIVIDE ( [Daily packages] - [Daily packages LY], [Daily packages LY] )', '+0.0%;-0.0%;0.0%', F_VOL)
m('Yield', 'DIVIDE ( [Service revenue] * 1000, [Daily packages] * 252 )', '$#,0.00', F_VOL,
  'Revenue per package, derived from annual revenue and 252 operating days.')
m('Reported yield', 'AVERAGE ( F_Service[Yield ($)] )', '$#,0.00', F_VOL)
m('LTL shipments', 'CALCULATE ( SUM ( F_Freight[ShipmentsPerDay] ), F_Freight[FiscalYear] = MAX ( F_Freight[FiscalYear] ) )', '#,0', F_VOL)
m('LTL revenue per shipment', 'CALCULATE ( AVERAGE ( F_Freight[RevenuePerShipment] ), F_Freight[FiscalYear] = MAX ( F_Freight[FiscalYear] ) )', '$#,0.00', F_VOL)
m('LTL shipments series', 'SUM ( F_Freight[ShipmentsPerDay] )', '#,0', F_VOL)
m('LTL yield series', 'AVERAGE ( F_Freight[RevenuePerShipment] )', '$#,0.00', F_VOL)

# climate
m('Scope 1', 'VAR y = MAX ( F_Climate[FiscalYear] ) RETURN CALCULATE ( SUM ( F_Climate[Scope1] ), F_Climate[FiscalYear] = y )', '#,0', F_CLI, 'Direct greenhouse gas emissions, metric tons CO2e.')
m('Scope 2', 'VAR y = MAX ( F_Climate[FiscalYear] ) RETURN CALCULATE ( SUM ( F_Climate[Scope2] ), F_Climate[FiscalYear] = y )', '#,0', F_CLI)
m('Scope 1 and 2', 'VAR y = MAX ( F_Climate[FiscalYear] ) RETURN CALCULATE ( SUM ( F_Climate[Scope1and2] ), F_Climate[FiscalYear] = y )', '#,0', F_CLI)
m('Scope 1 and 2 Mt', 'DIVIDE ( [Scope 1 and 2], 1000000 )', '#,0.00', F_CLI)
m('Scope 1 and 2 base', 'CALCULATE ( [Scope 1 and 2], REMOVEFILTERS ( D_FiscalYear ), F_Climate[FiscalYear] = 2019 )', '#,0', F_CLI)
m('Emissions vs FY2019', 'DIVIDE ( [Scope 1 and 2] - [Scope 1 and 2 base], [Scope 1 and 2 base] )', '+0.0%;-0.0%;0.0%', F_CLI)
m('Scope 3', 'SUM ( F_Scope3[Emissions] )', '#,0', F_CLI)
m('Scope 3 Mt', 'DIVIDE ( [Scope 3], 1000000 )', '#,0.00', F_CLI)
m('Scope 3 share', 'DIVIDE ( [Scope 3], CALCULATE ( [Scope 3], REMOVEFILTERS ( F_Scope3 ) ) )', '0.0%', F_CLI)
m('Carbon intensity', 'AVERAGE ( F_Intensity[IntensityPerRevenueMn] )', '#,0.0', F_CLI,
  'Scope 1 and 2 emissions per million dollars of revenue.')
m('Carbon intensity latest',
  'CALCULATE ( [Carbon intensity], REMOVEFILTERS ( F_Intensity ), F_Intensity[FiscalYear] = 2025 )', '#,0.0', F_CLI)
m('Carbon intensity 2009',
  'CALCULATE ( [Carbon intensity], REMOVEFILTERS ( F_Intensity ), F_Intensity[FiscalYear] = 2009 )', '#,0.0', F_CLI)
m('Intensity reduction',
  'DIVIDE ( [Carbon intensity latest] - [Carbon intensity 2009], [Carbon intensity 2009] )', '+0.0%;-0.0%;0.0%', F_CLI)
m('Electric vehicles', 'CALCULATE ( SUM ( F_Electric[ElectricVehicles] ), F_Electric[FiscalYear] = MAX ( F_Electric[FiscalYear] ) )', '#,0', F_CLI)
m('Electric vehicles series', 'SUM ( F_Electric[ElectricVehicles] )', '#,0', F_CLI)
m('Electric growth', 'VAR y = MAX ( F_Electric[FiscalYear] ) RETURN CALCULATE ( AVERAGE ( F_Electric[GrowthPct] ), F_Electric[FiscalYear] = y )', '+#,0.0;-#,0.0;0', F_CLI)
m('Jet fuel avoided', 'SUM ( F_Fuel[JetFuelAvoidedMnGal] )', '#,0', F_CLI)
m('SAF deployed', 'CALCULATE ( SUM ( F_SAF[SAFMnGal] ), F_SAF[FiscalYear] = MAX ( F_SAF[FiscalYear] ) )', '#,0.0', F_CLI)
m('SAF series', 'SUM ( F_SAF[SAFMnGal] )', '#,0.0', F_CLI)
m('Target year', 'MIN ( D_Target[Due] )', '0', F_CLI)
m('Years to target', 'MIN ( D_Target[Due] ) - 2026', '#,0', F_CLI)

# tile context texts
def txt(name, expr, folder=F_TXT):
    m(name, expr, None, folder)

txt('Fleet context',
    '"" & FORMAT ( [Trunk aircraft], "#,0" ) & " trunk, " & FORMAT ( [Feeder aircraft], "#,0" ) & " feeders"')
txt('Payload context',
    '"" & FORMAT ( [Fleet payload tonnes], "#,0" ) & " t at full load"')
txt('Average payload context',
    '"Heaviest: " & FORMAT ( MAXX ( ALL ( D_Aircraft ), D_Aircraft[Payload] ), "#,0" ) & " lb"')
txt('Boeing context',
    '"" & FORMAT ( [Boeing payload share], "0.0%" ) & " of lift capacity"')
txt('Owned context',
    '"Only " & FORMAT ( [Aircraft leased], "#,0" ) & " on lease"')
txt('Fleet change context',
    '"" & FORMAT ( [Aircraft change], "+#,0;-#,0;0" ) & " aircraft on FY" & ( MAX ( F_Fleet[FiscalYear] ) - 1 - 2000 )')
txt('Net income growth context',
    '"Net margin " & FORMAT ( [Net margin], "0.0%" ) & " · EPS " & FORMAT ( [EPS], "$#,0.00" )')
txt('Capex trend context',
    '"" & FORMAT ( [Capex intensity], "0.0%" ) & " of revenue, a decade low"')
txt('Order context',
    '"" & FORMAT ( [Aircraft in modification], "#,0" ) & " in pre-service work"')
txt('Revenue context',
    '"" & FORMAT ( [Operating margin], "0.0%" ) & " margin, EPS " & FORMAT ( [EPS], "$#,0.00" )')
txt('Volume context',
    '"" & FORMAT ( [Volume growth], "+0.0%;-0.0%;0.0%" ) & " versus prior year"')
txt('Hub context',
    '"" & FORMAT ( [Footprint Msqft], "#,0.0" ) & " million sq ft across " & FORMAT ( [Hubs], "#,0" ) & " facilities"')
txt('Emissions context',
    '"" & FORMAT ( [Emissions vs FY2019], "+0.0%;-0.0%;0.0%" ) & " versus FY2019"')
txt('Intensity context',
    '"" & FORMAT ( [Intensity reduction], "+0.0%;-0.0%;0.0%" ) & " since FY2009"')
txt('EV context',
    '"" & FORMAT ( [Electric growth], "+#,0.0" ) & "% in the latest year"')
txt('Network context',
    '"" & FORMAT ( [Airports served], "#,0" ) & "+ airports · 99% GDP"')
txt('Vehicle context',
    '"" & FORMAT ( [Own vehicles] / 1000, "#,0" ) & "k own · " & FORMAT ( [Provider vehicles] / 1000, "#,0" ) & "k hired"')
txt('Capacity context',
    '"Memphis alone sorts " & FORMAT ( CALCULATE ( [Sort capacity], D_Hub[HubKey] = "MEM" ), "#,0" ) & " per hour"')
txt('Employee context',
    '"" & FORMAT ( [Full-time employees] / 1000, "#,0" ) & ",000 of them full-time"')
txt('LTL context',
    '"" & FORMAT ( [LTL revenue per shipment], "$#,0.00" ) & " per shipment"')
txt('SAF context', '"Blended at 30% minimum"')
txt('Scope 3 context', '"Six categories, FY2025"')
txt('Facilities context',
    '"" & FORMAT ( [City stations], "#,0" ) & "+ city stations"')
txt('Footprint context',
    '"Memphis: " & FORMAT ( CALCULATE ( [Sq ft], D_Hub[HubKey] = "MEM" ) / 1000000, "#,0.0" ) & "m sq ft"')
txt('Acres context', '"On four continents"')
txt('Airports context', '"In 220+ countries"')
txt('Operating income context',
    '"" & FORMAT ( [Operating margin], "0.0%" ) & " of revenue"')
txt('Margin context', '"Adjusted margin 7.0%"')
txt('Revenue growth context',
    '"" & FORMAT ( [Revenue growth], "+0.0%;-0.0%;0.0%" ) & " on prior year"')
txt('Net income context', '"Net margin " & FORMAT ( [Net margin], "0.0%" )')
txt('EPS context', '"Diluted, US GAAP"')
txt('Capex context', '"" & FORMAT ( [Capex intensity], "0.0%" ) & " of revenue"')
txt('Hubs context',
    '"" & FORMAT ( [Footprint Msqft], "#,0.0" ) & "m sq ft, " & FORMAT ( [Hubs], "#,0" ) & " sites"')
txt('Capacity k context',
    '"Memphis sorts " & FORMAT ( CALCULATE ( [Sort capacity], D_Hub[HubKey] = "MEM" ) / 1000, "#,0" ) & "k/h"')

# ─────────────────────────── energy ───────────────────────────
F_ENE = '09 Energy & fuel'

def ey(name, col, fmt='#,0', desc=None):
    m(name, f'VAR y = MAX ( F_Energy[FiscalYear] ) '
            f'RETURN CALCULATE ( SUM ( F_Energy[{col}] ), F_Energy[FiscalYear] = y )',
      fmt, F_ENE, desc)

ey('Jet fuel', 'JetFuel', '#,0', 'Aviation fuel burned, terajoules, as published in the ESG data table.')
ey('Vehicle fuel', 'VehicleFuel', '#,0', 'Diesel, petrol, LPG and natural gas combined, terajoules.')
ey('Electricity used', 'Electricity')
ey('Diesel', 'Diesel')
ey('Biodiesel', 'Biodiesel')
ey('Total energy', 'TotalEnergy', '#,0', 'Scope 1 and 2 energy consumption, terajoules.')
ey('Energy incl. Scope 3', 'TotalInclScope3')
m('Energy intensity',
  'VAR y = MAX ( F_Energy[FiscalYear] ) '
  'RETURN CALCULATE ( AVERAGE ( F_Energy[IntensityTJperMn] ), F_Energy[FiscalYear] = y )',
  '#,0.00', F_ENE, 'Terajoules per million dollars of revenue.')
m('Jet fuel share',
  'VAR y = MAX ( F_Energy[FiscalYear] ) '
  'RETURN CALCULATE ( AVERAGE ( F_Energy[JetSharePct] ), F_Energy[FiscalYear] = y ) / 100',
  '0.0%', F_ENE)
m('Jet fuel PJ', 'DIVIDE ( [Jet fuel], 1000 )', '#,0.0', F_ENE)
m('Total energy PJ', 'DIVIDE ( [Total energy], 1000 )', '#,0.0', F_ENE)
m('Energy by year', 'SUM ( F_EnergySource[Energy] )', '#,0', F_ENE)
m('Terajoules',
  'VAR y = MAX ( F_EnergySource[FiscalYear] ) '
  'RETURN CALCULATE ( SUM ( F_EnergySource[Energy] ), F_EnergySource[FiscalYear] = y )',
  '#,0', F_ENE)
m('Of total',
  'DIVIDE ( [Terajoules], '
  'CALCULATE ( [Terajoules], REMOVEFILTERS ( F_EnergySource ) ) )',
  '0.0%', F_ENE)
m('Jet fuel base',
  'CALCULATE ( [Jet fuel], REMOVEFILTERS ( D_FiscalYear ), F_Energy[FiscalYear] = 2022 )', '#,0', F_ENE)
m('Jet fuel vs FY2022', 'DIVIDE ( [Jet fuel] - [Jet fuel base], [Jet fuel base] )',
  '+0.0%;-0.0%;0.0%', F_ENE)
m('Total energy base',
  'CALCULATE ( [Total energy], REMOVEFILTERS ( D_FiscalYear ), F_Energy[FiscalYear] = 2022 )', '#,0', F_ENE)
m('Energy vs FY2022', 'DIVIDE ( [Total energy] - [Total energy base], [Total energy base] )',
  '+0.0%;-0.0%;0.0%', F_ENE)
m('Aviation efficiency',
  'VAR y = MAX ( F_Efficiency[FiscalYear] ) '
  'RETURN CALCULATE ( AVERAGE ( F_Efficiency[AviationLperATM] ), F_Efficiency[FiscalYear] = y )',
  '#,0.000', F_ENE, 'Litres of jet fuel per available ton mile, FedEx Express fleet.')
m('Aviation litres',
  'VAR y = MAX ( F_Efficiency[FiscalYear] ) '
  'RETURN CALCULATE ( SUM ( F_Efficiency[AviationLitres] ), F_Efficiency[FiscalYear] = y )', '#,0', F_ENE)
m('Aviation litres bn', 'DIVIDE ( [Aviation litres], 1000000000 )', '#,0.00', F_ENE)
m('Available ton miles',
  'VAR y = MAX ( F_Efficiency[FiscalYear] ) '
  'RETURN CALCULATE ( SUM ( F_Efficiency[AvailableTonMiles] ), F_Efficiency[FiscalYear] = y )', '#,0', F_ENE)
m('Available ton miles bn', 'DIVIDE ( [Available ton miles], 1000000000 )', '#,0.0', F_ENE)
m('Aircraft intensity cut',
  'VAR y = MAX ( F_AviationIntensity[FiscalYear] ) '
  'RETURN CALCULATE ( SUM ( F_AviationIntensity[ReductionVs2005Pct] ), F_AviationIntensity[FiscalYear] = y ) / 100',
  '0%', F_ENE, 'Reduction in aircraft emissions intensity against the 2005 baseline.')
m('Efficiency series', 'AVERAGE ( F_Efficiency[AviationLperATM] )', '#,0.000', F_ENE)
m('Energy series', 'SUM ( F_Energy[TotalEnergy] )', '#,0', F_ENE)
m('Jet fuel series', 'SUM ( F_Energy[JetFuel] )', '#,0', F_ENE)

txt('Jet fuel context',
    '"" & FORMAT ( [Jet fuel vs FY2022], "+0.0%;-0.0%;0.0%" ) & " since FY2022"')
txt('Vehicle fuel context',
    '"Diesel is " & FORMAT ( DIVIDE ( [Diesel], [Vehicle fuel] ), "0%" ) & " of it"')
txt('Electricity context', '"96.7 GWh renewable"')
txt('Total energy context',
    '"" & FORMAT ( [Energy vs FY2022], "+0.0%;-0.0%;0.0%" ) & " since FY2022"')
txt('Energy intensity context', '"TJ per $m of revenue"')
txt('Aviation efficiency context',
    '"" & FORMAT ( [Aviation litres bn], "#,0.00" ) & "bn litres flown"')
txt('Jet share context', '"of all Scope 1 and 2 energy"')
txt('Aircraft cut context', '"Cut since 2005"')

# table labels
m('Fleet %', 'FORMAT ( DIVIDE ( [Aircraft], [Fleet total] ), "0.0%" )', None, F_TXT)
m('Lift %', 'FORMAT ( [Payload share], "0.0%" )', None, F_TXT)
m('Ownership',
  'IF ( [Aircraft leased] = 0, "All owned", FORMAT ( [Aircraft owned], "#,0" ) & " owned · " & FORMAT ( [Aircraft leased], "#,0" ) & " leased" )',
  None, F_TXT)
m('Lease label', 'FORMAT ( MIN ( D_Hub[Lease to] ), "0" )', None, F_TXT)


def measures_tmdl():
    L = ['table Metrics', f'\tlineageTag: {lt("Metrics")}', '']
    for name, expr, fmt, folder, desc in M:
        nm = name if (' ' not in name and name.isalnum()) else f"'{name}'"
        if desc:
            L.append(f'\t/// {desc}')
        if '\n' in expr:
            L.append(f'\tmeasure {nm} =')
            for ln in expr.strip().split('\n'):
                L.append('\t\t\t' + ln.strip())
        else:
            L.append(f'\tmeasure {nm} = {expr}')
        if fmt:
            L.append(f'\t\tformatString: {fmt}')
        if folder:
            L.append(f'\t\tdisplayFolder: {folder}')
        L.append(f'\t\tlineageTag: {lt("Metrics", name)}')
        L.append('')
    L += ['\tcolumn Placeholder',
          '\t\tdataType: string',
          '\t\tisHidden',
          f'\t\tlineageTag: {lt("Metrics", "Placeholder")}',
          '\t\tsummarizeBy: none',
          '\t\tsourceColumn: [Placeholder]',
          '',
          '\t\tannotation SummarizationSetBy = Automatic',
          '',
          '\tpartition Metrics = calculated',
          '\t\tmode: import',
          '\t\tsource = ROW ( "Placeholder", "" )',
          '',
          '\tannotation PBI_Id = Metrics',
          '']
    return '\n'.join(L)


def build():
    if os.path.isdir(SM):
        shutil.rmtree(SM)
    d = os.path.join(SM, 'definition', 'tables')
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(SM, 'definition.pbism'), 'w', encoding='utf-8') as f:
        f.write('{\n  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/'
                'definitionProperties/1.0.0/schema.json",\n  "version": "4.2",\n  "settings": {}\n}')
    with open(os.path.join(SM, 'definition', 'database.tmdl'), 'w', encoding='utf-8') as f:
        f.write('database\n\tcompatibilityLevel: 1606\n')
    with open(os.path.join(SM, 'definition', 'expressions.tmdl'), 'w', encoding='utf-8') as f:
        f.write('/// Absolute path of the folder holding the CSV files that feed the model.\n'
                '/// Set this to your own Donnees folder after cloning: Transform data > Manage parameters.\n'
                'expression DossierDonnees = "C:\\FedEx\\Donnees" '
                'meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
                f'\tlineageTag: {lt("DossierDonnees")}\n\n\tannotation PBI_ResultType = Text\n')
    names = [t.name for t in TABLES]
    with open(os.path.join(SM, 'definition', 'model.tmdl'), 'w', encoding='utf-8') as f:
        f.write('model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n'
                '\tdiscourageImplicitMeasures\n\tsourceQueryCulture: en-US\n\tdataAccessOptions\n'
                '\t\tlegacyRedirects\n\t\treturnErrorValuesAsNull\n\n')
        f.write('annotation PBI_QueryOrder = ["' + '", "'.join(names + ['DossierDonnees']) + '"]\n\n')
        f.write('annotation PBI_ProTooling = ["DevMode"]\n\n')
        for n in names + ['Metrics']:
            f.write(f'ref table {n}\n')
    for t in TABLES:
        with open(os.path.join(d, t.name + '.tmdl'), 'w', encoding='utf-8') as f:
            f.write(t.tmdl())
    with open(os.path.join(d, 'Metrics.tmdl'), 'w', encoding='utf-8') as f:
        f.write(measures_tmdl())
    with open(os.path.join(SM, 'definition', 'relationships.tmdl'), 'w', encoding='utf-8') as f:
        for ft, fc, tt, tc in RELATIONS:
            f.write(f'relationship {lt("rel", ft, fc, tt, tc)}\n'
                    f'\tfromColumn: {ft}.{fc}\n\ttoColumn: {tt}.{tc}\n\n')
    # check: every TMDL column exists in the CSV
    bad = []
    for t in TABLES:
        p = os.path.join(DATA, t.name + '.csv')
        if not os.path.exists(p):
            bad.append(f'{t.name}.csv missing'); continue
        head = next(csv.reader(open(p, encoding='utf-8')))
        for c, ty, src in t.cols:
            if (src or c) not in head:
                bad.append(f'{t.name}: column {src or c} missing from the CSV')
        for h in head:
            if h not in [(s or c) for c, ty, s in t.cols]:
                bad.append(f'{t.name}: CSV column {h} not declared')
    print(f'{len(TABLES)} tables, {len(M)} measures, {len(RELATIONS)} relationships')
    for b in bad:
        print('  !! ' + b)
    return not bad


if __name__ == '__main__':
    ok = build()
    print('OK' if ok else 'FAILURES')
