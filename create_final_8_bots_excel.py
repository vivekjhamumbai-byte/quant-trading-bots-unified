"""
Create Final Excel with 8 BOTS (duplicate GBI-RBI removed)
"""
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill

wb = openpyxl.Workbook()
wb.remove(wb.active)

# =============== SHEET 1: FINAL 8 BOTS ===============
ws = wb.create_sheet("FINAL 8 BOTS CONFIGURATION", 0)
ws.column_dimensions['A'].width = 30
ws.column_dimensions['B'].width = 18
ws.column_dimensions['C'].width = 18
ws.column_dimensions['D'].width = 25
ws.column_dimensions['E'].width = 18
ws.column_dimensions['F'].width = 15

# Title
ws['A1'] = "FINAL 8 BOTS CONFIGURATION (DUPLICATE GBI-RBI REMOVED)"
ws['A1'].font = Font(bold=True, size=12, color="FFFFFF")
ws['A1'].fill = PatternFill(start_color="002060", end_color="002060", fill_type="solid")
ws.merge_cells('A1:F1')

# Headers
headers = ["Bot Name", "Entry Time", "Exit Time", "Instruments", "Max Positions", "Risk/Trade"]
for col, header in enumerate(headers, 1):
    cell = ws.cell(row=3, column=col, value=header)
    cell.font = Font(bold=True, color="FFFFFF")
    cell.fill = PatternFill(start_color="333333", end_color="333333", fill_type="solid")
    cell.alignment = Alignment(horizontal="center", wrap_text=True)

# FINAL 8 BOTS DATA
bots_final = [
    ["1. O V NIFTY", "09:30", "15:10", "NIFTY Futures + Options", "Unlimited", "2700"],
    ["2. SENSEX Hero-Zero", "15:09", "15:39", "SENSEX Options", "Multiple", "2700"],
    ["3. ORB Lite", "09:25", "15:10", "NIFTY + BANKNIFTY", "Unlimited", "2700"],
    ["4. ORB-OV", "09:25", "15:10", "All Indices + F&O", "Unlimited", "2700"],
    ["5. Signal Bot", "09:25", "15:10", "Indices + Stocks", "Unlimited", "2700"],
    ["6. GBI-RBI", "09:25", "15:10", "Green/Red Bar Patterns", "Unlimited", "2700"],
    ["7. bot_page_paper (Trail SL)", "Manual", "15:10", "All (Manual Selection)", "Manual", "Variable"],
    ["8. Scalper Bot", "09:25", "15:09", "NIFTY, BANKNIFTY, Stocks", "Unlimited", "2700"],
]

row = 4
for bot in bots_final:
    for col, value in enumerate(bot, 1):
        cell = ws.cell(row=row, column=col, value=value)
        cell.alignment = Alignment(horizontal="left", wrap_text=True)
    row += 1

# =============== SHEET 2: SHARED EXIT RULES ===============
ws = wb.create_sheet("SHARED EXIT RULES")
ws.column_dimensions['A'].width = 35
ws.column_dimensions['B'].width = 30
ws.column_dimensions['C'].width = 45

ws['A1'] = "SHARED EXIT MANAGER (ALL BOTS USE THIS)"
ws['A1'].font = Font(bold=True, size=11, color="FFFFFF")
ws['A1'].fill = PatternFill(start_color="002060", end_color="002060", fill_type="solid")
ws.merge_cells('A1:C1')

row = 3
headers = ["Phase", "Trigger", "Action / Stop Level"]
for col, header in enumerate(headers, 1):
    cell = ws.cell(row=row, column=col, value=header)
    cell.font = Font(bold=True)
    cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")

exit_phases = [
    ["Phase 1: Hard Stop", "Opening position (any loss)", "Close if premium <= entry * (1 - 0.08) = -8%"],
    ["Phase 2: Breakeven", "Premium +5% gain", "Move stop to entry price = BREAKEVEN"],
    ["Phase 3: Trail", "Premium +10% gain", "Stop trails 5% below peak = TRAILING STOP"],
    ["Ladder Rung 0", "peak_profit >= 1000", "Ladder activates (START)"],
    ["Ladder Rung 1+", "Peak continues", "500 steps (Trail SL uses 300)"],
    ["Force Close", "15:09 (Scalper) or 15:10", "Exit all remaining positions"],
]

row += 1
for phase in exit_phases:
    for col, value in enumerate(phase, 1):
        cell = ws.cell(row=row, column=col, value=value)
        cell.alignment = Alignment(horizontal="left", wrap_text=True)
    row += 1

# =============== SHEET 3: INSTRUMENT MASTER ===============
ws = wb.create_sheet("INSTRUMENT MASTER")
ws.column_dimensions['A'].width = 15
ws.column_dimensions['B'].width = 15
ws.column_dimensions['C'].width = 20

headers = ["Symbol", "Lot Size (NSE)", "Type"]
for col, header in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=header)
    cell.font = Font(bold=True)
    cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")

# Indices
indices = [
    ("NIFTY", 65, "INDEX"),
    ("BANKNIFTY", 40, "INDEX"),
    ("SENSEX", 10, "INDEX"),
    ("FINNIFTY", 40, "INDEX"),
    ("MIDCAPNIFTY", 75, "INDEX"),
]

row = 2
for symbol, lot_size, instr_type in indices:
    ws.cell(row=row, column=1, value=symbol)
    ws.cell(row=row, column=2, value=lot_size)
    ws.cell(row=row, column=3, value=instr_type)
    row += 1

# Sample stocks
stocks = [
    ("RELIANCE", 1, "STOCK"),
    ("INFY", 1, "STOCK"),
    ("TCS", 1, "STOCK"),
    ("SBIN", 1, "STOCK"),
    ("ICICIBANK", 1, "STOCK"),
    ("AXISBANK", 1, "STOCK"),
]

for symbol, lot_size, instr_type in stocks:
    ws.cell(row=row, column=1, value=symbol)
    ws.cell(row=row, column=2, value=lot_size)
    ws.cell(row=row, column=3, value=instr_type)
    row += 1

# Save
wb.save("D:\\Bot 8.1.2026\\FINAL_8_BOTS_COMPLETE.xlsx")
print("=" * 70)
print("SUCCESS! FINAL 8 BOTS EXCEL CREATED")
print("=" * 70)
print("\nFINAL BOT LIST (8 BOTS):")
print("1. O V NIFTY: 09:30 -> 15:10")
print("2. SENSEX Hero-Zero: 15:09 -> 15:39")
print("3. ORB Lite: 09:25 -> 15:10")
print("4. ORB-OV: 09:25 -> 15:10")
print("5. Signal Bot: 09:25 -> 15:10")
print("6. GBI-RBI: 09:25 -> 15:10")
print("7. bot_page_paper (Trail SL): Manual -> 15:10")
print("8. Scalper Bot: 09:25 -> 15:09")
print("\nDuplicate REMOVED: gbi-rbi-bot (was bot #9)")
print("\nFile: D:\\Bot 8.1.2026\\FINAL_8_BOTS_COMPLETE.xlsx")
print("=" * 70)
