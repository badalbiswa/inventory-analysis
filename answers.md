TOY STORE INVENTORY ANALYSIS — ANSWERS
Student: Badal Biswa
Store: Rainbow Shelf Toys

1. **DATA CLEANING**
a. ***How many rows did you remove or flag as invalid (duplicates, junk rows, blank IDs)?***
   - 2 blank rows were skipped (lines 2 and 31 in the raw CSV).
   - 1 junk row with a blank ID and invalid data was removed (line 29 in the raw CSV: ",???,,,N/A,free,unknown,,ignore").
   - 1 duplicate row based on toy_id was removed (line 28 in the raw CSV: "T017,Unicorn Headband,Accessories,Rainbow Toys Co.,19,$57.22,2025-02-19,B2,DUPLICATE?").
   - Total rows removed/skipped: 4 rows (2 blank, 1 junk, 1 duplicate).

b. ***List at least five distinct data-quality issues you found and how you fixed each:***
   1. Messy Column Headers: Column names had leading/trailing spaces (e.g., " toy_id ", " supplier", " Unit_Cost ").
      - Fix: Stripped whitespace using `.columns.str.strip()` and renamed them to standardized snake_case format.
   2. Missing and Invalid IDs (Junk Rows): Row 29 was missing a valid ID and contained placeholder values.
      - Fix: Filtered rows using the regex pattern `^T\d+$` on `toy_id` to ensure only valid IDs are kept.
   3. Duplicate Product Records: Row 28 was a duplicate entry for toy ID `T017` ("Unicorn Headband").
      - Fix: Used `.drop_duplicates(subset=['toy_id'], keep='first')` to drop the duplicate entry while keeping the original.
   4. Dollar Signs in Currency Fields: Several values in the cost column had a "$" prefix (e.g., "$39.06", "$9.02").
      - Fix: Stripped "$" characters using `.str.replace('$', '', regex=False)` and cast to float.
   5. Extra Spaces in Text Columns: Values contained multiple internal or leading/trailing spaces (e.g., "  Superhero Cape Set  " and "Pikachu  Keychain").
      - Fix: Stripped leading/trailing spaces and replaced internal multiple spaces with a single space using `.str.replace(r'\s+', ' ', regex=True)`.
   6. Inconsistent Category Casing: Categories were inconsistently capitalized (e.g., "Plush" vs "plush", "electronics" vs "Electronics").
      - Fix: Applied Title Case normalization using `.str.title()` and mapped "Stem" back to "STEM" to preserve acronym capitalization.
   7. Inconsistent Date Formats: Dates used mixed formats (e.g., "YYYY-MM-DD", "MM/DD/YYYY", "MM-DD-YYYY", and "unknown").
      - Fix: Parsed with `pd.to_datetime(..., format='mixed', errors='coerce')` to standardize formats to YYYY-MM-DD, converting invalid dates to NaT.

2. **INVENTORY VALUE**
a. ***What is the total inventory value (sum of quantity_on_hand × unit_cost) for all valid toys?***
   - $36,758.67

b. ***What is the average unit cost across all valid rows (weighted by row, not by quantity)?***
   - $50.18

3. **AGING ON THE SHELF**
a. ***Using date_received and assuming today's date is 2026-07-06, how many SKUs have been on the shelf more than 90 days?***
   - 20 SKUs
   - Note: 6 items with missing date_received values were excluded because their age could not be calculated.

b. ***What is the total value of stock aged more than 90 days?***
   - $29,275.29 (based on the 20 SKUs with a known date_received)

4. **CATEGORY ANALYSIS**
a. ***Which three categories have the highest total inventory value?***
   1. Plush: $7,814.93
   2. Outdoor: $5,924.48
   3. Accessories: $5,693.92

b. ***Which category has the lowest average unit cost?***
   - Misc ($12.00)

5. **PIKACHU & UNICORN FEATURE ITEMS**
a. ***Total quantity on hand for all items with "Pikachu" in the name (case-insensitive):***
   - 152 units
   - Items included:
     - T001: PIKACHU PLUSH (LARGE) (46 units)
     - T002: Pikachu Keychain (43 units)
     - T016: Pikachu Trading Cards (Booster) (27 units)
     - T021: Pikachu Lunchbox (36 units)

b. ***Total inventory value for all items with "Unicorn" in the name (case-insensitive):***
   - $3,797.18
   - Items included:
     - T003: Sparkle Unicorn ($1,554.35)
     - T004: Crystal Unicorn Figurine ($647.01)
     - T017: UNICORN HEADBAND ($1,087.18)
     - T022: Enchanted Unicorn Puzzle ($508.64)

6. **Low Stock**
a. ***How many items have quantity_on_hand strictly less than 5?***
   - 1 item

b. ***List their toy_id and toy_name:***
   - T999: Mystery Grab Bag (Quantity on hand: 3)

**REFLECTION**
The easiest part of this assignment was opening the files and creating the project and output files. The hardest part, and the part that took the most time, was cleaning the raw inventory data. There were many problems with the raw data that had to be fixed before the analysis would be accurate. I had to review the data after each cleaning step to make sure only valid products remained.

The most enjoyable part was getting the calculations to work. I calculated the total inventory value, average unit cost, aged stock, category totals, Pikachu quantity, Unicorn inventory value, and low-stock items. I tried to complete as much of the assignment as I could on my own, and when I could not figure something out, I used Antigravity for help. It helped me understand the errors and work through the parts I was stuck on. This assignment showed me how important data cleaning is before doing any analysis.