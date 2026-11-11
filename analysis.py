import pandas as pd
import openpyxl
import datetime
from docx import Document

df = pd.read_csv("inventory_raw.csv")

print(df.head())
print(df.columns)
print(df.dtypes)
print(df.isnull().sum())

df.columns = df.columns.str.strip()

def normalize_header(h):
    return h.strip().lower().replace(' ', '_')

normalized_lookup = {
    'toy_id': 'toy_id',
    'toy_name': 'toy_name',
    'category': 'category',
    'supplier': 'supplier',
    'qty_on_hand': 'quantity_on_hand',
    'unit_cost': 'unit_cost',
    'date_received': 'date_received',
    'shelf_loc': 'shelf_location',
    'notes': 'notes'
}
rename_mapping = {col: normalized_lookup[normalize_header(col)]
                   for col in df.columns if normalize_header(col) in normalized_lookup}
df = df.rename(columns=rename_mapping)

# Remove invalid toy IDs
df['toy_id'] = df['toy_id'].astype(str).str.strip()
df = df[df['toy_id'].str.match(r'^T\d+$', na=False)]

# Remove duplicate product rows based on toy_id
df = df.drop_duplicates(subset=['toy_id'], keep='first')

# Remove extra spaces from text columns and convert 'nan'/empty strings to None
text_cols = ['toy_id', 'toy_name', 'category', 'supplier', 'shelf_location', 'notes']
for col in text_cols:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)
        df[col] = df[col].replace({'nan': None, 'NaN': None, 'None': None, '': None})

# Make category names consistent (Title Case, keeping STEM uppercase)
def clean_category(val):
    if pd.isna(val) or not str(val).strip():
        return None
    val_clean = str(val).strip().title()
    return 'STEM' if val_clean == 'Stem' else val_clean

df['category'] = df['category'].apply(clean_category)

# Normalize shelf_location casing so codes like "d2" and "D2" aren't treated as different
df['shelf_location'] = df['shelf_location'].apply(lambda v: v.upper() if isinstance(v, str) else v)

# Convert cost values to numeric
df['unit_cost'] = df['unit_cost'].astype(str).str.replace('$', '', regex=False).str.strip()
df['unit_cost'] = pd.to_numeric(df['unit_cost'], errors='coerce')

# Convert quantity_on_hand to integers
df['quantity_on_hand'] = pd.to_numeric(df['quantity_on_hand'], errors='coerce').fillna(0).astype(int)

# Convert mixed date formats to proper dates (YYYY-MM-DD)
df['date_received'] = pd.to_datetime(df['date_received'], format='mixed', errors='coerce')

# Save the cleaned data (containing exactly the requested columns)
df.to_csv("clean_inventory.csv", index=False)
print("Cleaned inventory data successfully saved to 'clean_inventory.csv'.")

# Calculate inventory value
df['inventory_value'] = df['quantity_on_hand'] * df['unit_cost']

# COMPUTE METRICS
print("\n--- INVENTORY ANALYSIS METRICS ---")

# 1. Total inventory value
total_value = df['inventory_value'].sum()
print(f"Total Inventory Value: ${total_value:,.2f}")

# 2. Average unit cost
average_unit_cost = df['unit_cost'].mean()
print(f"Average Unit Cost: ${average_unit_cost:,.2f}")

# 3. Aging Stock (assuming today is 2026-07-06)
today = pd.Timestamp("2026-07-06")
df['days_on_shelf'] = (today - df['date_received']).dt.days

# Skip items with missing dates from aging calculations
missing_date_rows = df[df['date_received'].isna()]
missing_date_count = len(missing_date_rows)
if missing_date_count:
    print(f"\nNote: {missing_date_count} SKU(s) have no usable date_received and are "
          f"excluded from the aging analysis: {', '.join(missing_date_rows['toy_id'])}")

old_stock = df[df['days_on_shelf'] > 90]
aged_skus_count = len(old_stock)
total_aged_value = old_stock['inventory_value'].sum()
print(f"SKUs on shelf > 90 days: {aged_skus_count} (out of {len(df) - missing_date_count} SKUs with a known date)")
print(f"Total Value of Aged Stock: ${total_aged_value:,.2f}")

# 4. Category breakdown
category_values = df.groupby('category')['inventory_value'].sum().sort_values(ascending=False)
print("\nTop 3 Categories by Inventory Value:")
for i, (cat, val) in enumerate(category_values.head(3).items(), 1):
    print(f"  {i}. {cat}: ${val:,.2f}")

lowest_avg_cost_category = df.groupby('category')['unit_cost'].mean().idxmin()
lowest_avg_cost_value = df.groupby('category')['unit_cost'].mean().min()
print(f"Category with Lowest Average Unit Cost: {lowest_avg_cost_category} (${lowest_avg_cost_value:,.2f})")

# 5. Pikachu & Unicorn feature items
pikachu_qty = df[df['toy_name'].str.contains('Pikachu', case=False, na=False)]['quantity_on_hand'].sum()
unicorn_val = df[df['toy_name'].str.contains('Unicorn', case=False, na=False)]['inventory_value'].sum()
print(f"\nTotal Pikachu quantity on hand: {pikachu_qty}")
print(f"Total Unicorn inventory value: ${unicorn_val:,.2f}")

# 6. Low stock alerts (quantity < 5)
low_stock_items = df[df['quantity_on_hand'] < 5]
print(f"\nItems with quantity < 5: {len(low_stock_items)}")
for idx, row in low_stock_items.iterrows():
    print(f"  ID: {row['toy_id']}, Name: {row['toy_name']}, Qty: {row['quantity_on_hand']}")

# CREATE SUPPLIER SUMMARY DATA
# Identify products that need to be reordered (quantity < 5)
df['is_reorder'] = df['quantity_on_hand'] < 5

# Group by supplier and calculate required metrics
supplier_summary = df.groupby('supplier').agg(
    total_value=('inventory_value', 'sum'),
    sku_count=('toy_id', 'count'),
    reorder_count=('is_reorder', 'sum')
).reset_index()

# Assign contact names for each supplier
supplier_contacts = {
    'Nintendo Partners': 'Mario Croft',
    'Rainbow Toys Co.': 'Iris Bow',
    'BrickWorld': 'Mason Stone',
    'SkyTech Toys': 'Skyler Cloud',
    'Messy Fun Ltd.': 'Paige Splatter',
    'Timber Tracks': 'Woody Forrest',
    'Hero Gear': 'Bruce Wayne',
    'Enchanted Isle': 'Luna Wand',
    'Discovery Den': 'Diana Jones',
    'MindBender': 'Charles Xavier',
    'BlastZone': 'Rex Danger',
    'Galaxy Gifts': 'Luke Skywalker',
    'WindRiders': 'Gale Force',
    'Family Fun Inc.': 'Bob Parr',
    'PopPlay': 'Bubbles Fizz',
    'Dino Depot': 'Rex Fossil',
    'Circus Skills': 'Jules Ringmaster',
    'Unknown': 'Agent Smith'
}

supplier_summary['contact_name'] = supplier_summary['supplier'].map(supplier_contacts).fillna('Unknown Contact')
supplier_summary['letter_date'] = '2026-07-06'

# Reorder columns: supplier, contact_name, total_value, sku_count, reorder_count, letter_date
supplier_summary = supplier_summary[[
    'supplier', 'contact_name', 'total_value', 'sku_count', 'reorder_count', 'letter_date'
]]

print("\n--- Supplier Summary Data ---")
print(supplier_summary)

# Build Excel workbook
# CREATE EXCEL WORKBOOK (inventory_analysis.xlsx)
from openpyxl.styles import PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Start openpyxl workbook
wb = openpyxl.Workbook()

# Style constants for a premium professional look
FONT_NAME = 'Segoe UI'
font_title = openpyxl.styles.Font(name=FONT_NAME, size=16, bold=True, color='1F497D')
font_subtitle = openpyxl.styles.Font(name=FONT_NAME, size=10, italic=True, color='595959')
font_section_header = openpyxl.styles.Font(name=FONT_NAME, size=11, bold=True, color='FFFFFF')
font_data_header = openpyxl.styles.Font(name=FONT_NAME, size=11, bold=True, color='FFFFFF')
font_bold = openpyxl.styles.Font(name=FONT_NAME, size=10, bold=True)
font_regular = openpyxl.styles.Font(name=FONT_NAME, size=10)

fill_navy = PatternFill(start_color='1F497D', end_color='1F497D', fill_type='solid')
fill_zebra = PatternFill(start_color='F2F5F8', end_color='F2F5F8', fill_type='solid')

thin_border = Border(
    left=Side(style='thin', color='D9D9D9'),
    right=Side(style='thin', color='D9D9D9'),
    top=Side(style='thin', color='D9D9D9'),
    bottom=Side(style='thin', color='D9D9D9')
)

align_left = Alignment(horizontal='left', vertical='center')
align_right = Alignment(horizontal='right', vertical='center')
align_center = Alignment(horizontal='center', vertical='center')

# 1. Summary Sheet
ws_summary = wb.active
ws_summary.title = "Summary"
ws_summary.views.sheetView[0].showGridLines = True

# Title block
ws_summary['A1'] = "Rainbow Shelf Toys"
ws_summary['A1'].font = font_title
ws_summary['A2'] = "Inventory Audit & Performance Summary"
ws_summary['A2'].font = font_subtitle

# Metadata
ws_summary['A4'] = "Prepared By:"
ws_summary['A4'].font = font_bold
ws_summary['B4'] = "Badal Biswa"
ws_summary['B4'].font = font_regular

ws_summary['A5'] = "Store Location:"
ws_summary['A5'].font = font_bold
ws_summary['B5'] = "Rainbow Shelf Toys"
ws_summary['B5'].font = font_regular

ws_summary['A6'] = "Report Date:"
ws_summary['A6'].font = font_bold
ws_summary['B6'] = "2026-07-06"
ws_summary['B6'].font = font_regular

# Section: Key Inventory Metrics
ws_summary.merge_cells('A8:B8')
ws_summary['A8'] = "KEY INVENTORY METRICS"
ws_summary['A8'].font = font_section_header
ws_summary['A8'].fill = fill_navy
ws_summary['A8'].alignment = align_center

metrics = [
    ("Total Inventory Value", total_value, "$#,##0.00"),
    ("Average Unit Cost", average_unit_cost, "$#,##0.00"),
    ("Number of Aged SKUs (>90 days)", aged_skus_count, "#,##0"),
    ("Value of Aged Inventory", total_aged_value, "$#,##0.00"),
    ("Number of Low-Stock SKUs (<5 units)", len(low_stock_items), "#,##0")
]

row_num = 9
for label, val, num_fmt in metrics:
    ws_summary.cell(row=row_num, column=1, value=label).font = font_regular
    ws_summary.cell(row=row_num, column=1).alignment = align_left
    ws_summary.cell(row=row_num, column=1).border = thin_border
    
    cell_val = ws_summary.cell(row=row_num, column=2, value=val)
    cell_val.font = font_bold
    cell_val.alignment = align_right
    cell_val.number_format = num_fmt
    cell_val.border = thin_border
    row_num += 1

if missing_date_count:
    ws_summary.cell(row=row_num, column=1,
                     value=f"Note: {missing_date_count} SKU(s) have no recorded date_received "
                           f"and are excluded from the aging figures above.").font = font_subtitle
    ws_summary.merge_cells(f'A{row_num}:B{row_num}')
    row_num += 1

# Section: Feature Items Results
row_num += 1 # Empty row
ws_summary.merge_cells(f'A{row_num}:B{row_num}')
ws_summary[f'A{row_num}'] = "FEATURE ITEMS ANALYSIS"
ws_summary[f'A{row_num}'].font = font_section_header
ws_summary[f'A{row_num}'].fill = fill_navy
ws_summary[f'A{row_num}'].alignment = align_center
row_num += 1

features = [
    ("Total Pikachu Quantity on Hand", pikachu_qty, "#,##0"),
    ("Total Unicorn Inventory Value", unicorn_val, "$#,##0.00")
]

for label, val, num_fmt in features:
    ws_summary.cell(row=row_num, column=1, value=label).font = font_regular
    ws_summary.cell(row=row_num, column=1).alignment = align_left
    ws_summary.cell(row=row_num, column=1).border = thin_border
    
    cell_val = ws_summary.cell(row=row_num, column=2, value=val)
    cell_val.font = font_bold
    cell_val.alignment = align_right
    cell_val.number_format = num_fmt
    cell_val.border = thin_border
    row_num += 1

# Section: Top Categories by Inventory Value
row_num += 1 # Empty row
ws_summary.cell(row=row_num, column=1, value="TOP 3 CATEGORIES").font = font_section_header
ws_summary.cell(row=row_num, column=1).fill = fill_navy
ws_summary.cell(row=row_num, column=1).alignment = align_left
ws_summary.cell(row=row_num, column=1).border = thin_border

ws_summary.cell(row=row_num, column=2, value="INVENTORY VALUE").font = font_section_header
ws_summary.cell(row=row_num, column=2).fill = fill_navy
ws_summary.cell(row=row_num, column=2).alignment = align_right
ws_summary.cell(row=row_num, column=2).border = thin_border
row_num += 1

for cat, val in category_values.head(3).items():
    ws_summary.cell(row=row_num, column=1, value=cat).font = font_regular
    ws_summary.cell(row=row_num, column=1).alignment = align_left
    ws_summary.cell(row=row_num, column=1).border = thin_border
    
    cell_val = ws_summary.cell(row=row_num, column=2, value=val)
    cell_val.font = font_regular
    cell_val.alignment = align_right
    cell_val.number_format = "$#,##0.00"
    cell_val.border = thin_border
    row_num += 1

# 2. Clean_Data Sheet
ws_clean = wb.create_sheet(title="Clean_Data")
ws_clean.views.sheetView[0].showGridLines = True

headers_clean = [col for col in df.columns if col not in ['is_reorder', 'days_on_shelf']]

# Let's add headers to sheet
for col_num, header in enumerate(headers_clean, 1):
    cell = ws_clean.cell(row=1, column=col_num, value=header)
    cell.font = font_data_header
    cell.fill = fill_navy
    cell.alignment = align_center
    cell.border = thin_border

# Write data rows
for row_num, row_data in enumerate(df[headers_clean].values, 2):
    is_even = (row_num % 2 == 0)
    for col_num, val in enumerate(row_data, 1):
        cell = ws_clean.cell(row=row_num, column=col_num)
        cell.font = font_regular
        cell.border = thin_border
        
        if is_even:
            cell.fill = fill_zebra
            
        col_name = headers_clean[col_num - 1]
        
        if pd.isna(val):
            cell.value = ""
        else:
            cell.value = val
            
        if col_name == 'toy_id':
            cell.alignment = align_center
        elif col_name in ['toy_name', 'category', 'supplier', 'shelf_location', 'notes']:
            cell.alignment = align_left
        elif col_name == 'quantity_on_hand':
            cell.alignment = align_right
            cell.number_format = "#,##0"
            if not pd.isna(val):
                cell.value = int(val)
        elif col_name in ['unit_cost', 'inventory_value']:
            cell.alignment = align_right
            cell.number_format = "$#,##0.00"
            if not pd.isna(val):
                cell.value = float(val)
        elif col_name == 'date_received':
            cell.alignment = align_center
            if isinstance(val, pd.Timestamp):
                cell.value = val.strftime('%Y-%m-%d')
            elif isinstance(val, str) and len(val) > 10:
                cell.value = val[:10]

# 3. MailMerge Sheet 
ws_merge = wb.create_sheet(title="MailMerge")
ws_merge.views.sheetView[0].showGridLines = True

headers_merge = list(supplier_summary.columns)
for col_num, header in enumerate(headers_merge, 1):
    cell = ws_merge.cell(row=1, column=col_num, value=header)
    cell.font = font_data_header
    cell.fill = fill_navy
    cell.alignment = align_center
    cell.border = thin_border

for row_num, row_data in enumerate(supplier_summary.values, 2):
    is_even = (row_num % 2 == 0)
    for col_num, val in enumerate(row_data, 1):
        cell = ws_merge.cell(row=row_num, column=col_num)
        cell.font = font_regular
        cell.border = thin_border
        
        if is_even:
            cell.fill = fill_zebra
            
        col_name = headers_merge[col_num - 1]
        
        if pd.isna(val):
            cell.value = ""
        else:
            cell.value = val
            
        if col_name in ['supplier', 'contact_name']:
            cell.alignment = align_left
        elif col_name == 'total_value':
            cell.alignment = align_right
            cell.number_format = "$#,##0.00"
            if not pd.isna(val):
                cell.value = float(val)
        elif col_name in ['sku_count', 'reorder_count']:
            cell.alignment = align_right
            cell.number_format = "#,##0"
            if not pd.isna(val):
                cell.value = int(val)
        elif col_name == 'letter_date':
            cell.alignment = align_center
            if isinstance(val, pd.Timestamp):
                cell.value = val.strftime('%Y-%m-%d')
            elif isinstance(val, str) and len(val) > 10:
                cell.value = val[:10]

# Skip placeholder supplier "Unknown" when creating letters
mailmerge_note_row = len(supplier_summary) + 3
ws_merge.cell(row=mailmerge_note_row, column=1,
              value="Note: 'Unknown' is a placeholder for products with no recorded "
                    "supplier in the source data (e.g. Mystery Grab Bag) and does not "
                    "receive a printed letter.").font = font_subtitle
ws_merge.merge_cells(f'A{mailmerge_note_row}:F{mailmerge_note_row}')
for ws in [ws_summary, ws_clean, ws_merge]:
    for col in ws.columns:
        max_len = 0
        for cell in col:
            if cell.coordinate in ws.merged_cells:
                continue
            if cell.row in [1, 2] and ws.title == "Summary":
                continue
            val_str = str(cell.value or '')
            if len(val_str) > max_len:
                max_len = len(val_str)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

wb.save("inventory_analysis.xlsx")
print("Workbook 'inventory_analysis.xlsx' successfully created with sheets Summary, Clean_Data, and MailMerge.")

# Create supplier letters
# STEP 7: CREATE WORD SUPPLIER LETTERS (supplier_notice.docx)
# Generate Word document containing letters for all suppliers
doc_letters = Document()

# Keep "Unknown" in MailMerge, but skip its supplier letter
letter_recipients = supplier_summary[supplier_summary['supplier'] != 'Unknown'].reset_index(drop=True)

for i, row in letter_recipients.iterrows():
    # Date at the top
    p_date = doc_letters.add_paragraph()
    p_date.add_run(f"Date: {row['letter_date']}").bold = True
    
    # Salutation
    doc_letters.add_paragraph(f"Dear {row['contact_name']},")
    
    # Paragraph 1
    doc_letters.add_paragraph("Rainbow Shelf Toys is reviewing its inventory before an upcoming audit.")
    
    # Paragraph 2
    total_val_formatted = f"${row['total_value']:,.2f}"
    p_val = doc_letters.add_paragraph()
    p_val.add_run("The total value of products supplied by ")
    p_val.add_run(row['supplier']).bold = True
    p_val.add_run(" is ")
    p_val.add_run(total_val_formatted).bold = True
    p_val.add_run(".")
    
    # Paragraph 3
    p_reorder = doc_letters.add_paragraph()
    p_reorder.add_run("Our records show that ")
    p_reorder.add_run(str(row['reorder_count'])).bold = True
    p_reorder.add_run(" of your products currently have fewer than five units in stock and may require reordering.")
    
    # Closing
    p_close = doc_letters.add_paragraph()
    p_close.add_run("Thank you,\n").italic = True
    p_close.add_run("Maya Chen\n").bold = True
    p_close.add_run("Rainbow Shelf Toys").italic = True
    
    # Add page break if it is not the last supplier
    if i < len(letter_recipients) - 1:
        doc_letters.add_page_break()

doc_letters.save("supplier_notice.docx")
print(f"Word document 'supplier_notice.docx' successfully created containing notice letters "
      f"for {len(letter_recipients)} suppliers (placeholder 'Unknown' supplier excluded).")