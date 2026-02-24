# STX Track Training Schedules - Weeks 25-34

## 📦 What You Have

I've generated **all 10 weeks** of your track training progression in multiple formats:

### Individual CSV Files (one per week):
- `week25_schedule.csv` through `week34_schedule.csv`
- Easy to edit in Excel, Google Sheets, or any text editor
- Same format as the XC schedules

### Excel Workbook (all weeks in one file):
- **`track_training_weeks_25-34.xlsx`** ⭐
- One tab per week (10 tabs total)
- Easy to navigate between weeks
- Perfect for overview and planning

### Generation Scripts:
- `generate_track_schedules.py` - Creates all CSV files and Excel workbook
- `csv_to_markdown_track.py` - Converts CSV to markdown (handles 6 groups)

---

## 🎯 Quick Overview

**Weeks Included:** 25-34 (November 10, 2025 - January 18, 2026)

**Groups (6 total):**
- 🔵 Freshman
- ⚪ White
- 🟢 Green JV & Green Varsity
- 🟡 Gold JV & Gold Varsity

**Training Phases:**
- **Week 25:** JV Base Building (Varsity on rest)
- **Week 26:** Varsity enters (Thanksgiving week)
- **Weeks 27-29:** Progressive build toward peak
- **Week 30:** Pre-Christmas reduced volume
- **Week 31:** Christmas break recovery
- **Week 32:** Post-break build
- **Week 33:** 🏔️ **PEAK MILEAGE WEEK**
- **Week 34:** Post-peak maintenance

---

## 📊 Peak Mileage (Week 33)

| Group | Weekly Miles |
|-------|-------------:|
| **Freshman** | 30 mi |
| **White** | 40 mi |
| **Green JV** | 50 mi |
| **Green Varsity** | 44 mi |
| **Gold JV** | 60 mi |
| **Gold Varsity** | 50 mi |

---

## ✏️ How to Use

### Option 1: Edit Individual Week CSVs
```bash
# Open in Excel/Sheets
week25_schedule.csv

# Make changes, save, then generate markdown:
python csv_to_markdown_track.py week25_schedule.csv
```

### Option 2: Use the Excel Workbook
```bash
# Open the workbook
track_training_weeks_25-34.xlsx

# Navigate between weeks using tabs
# Make edits across multiple weeks easily
# Export individual sheets as CSV if needed
```

### Option 3: Regenerate Everything
```bash
# If you modify the Python script with new data:
python generate_track_schedules.py

# This creates fresh copies of all 10 CSVs + Excel workbook
```

---

## 🔄 CSV Format (Same as XC)

| Week | Day | Group | Pre | Main_Workout | Post | Miles | Notes |
|------|-----|-------|-----|--------------|------|-------|-------|
| 25 | Mon | Freshman | | 2mi easy | | 2 | JV Base Building |
| 25 | Mon | White | | 3mi easy | | 3 | JV Base Building |
| ... | ... | ... | ... | ... | ... | ... | ... |

**Columns:**
- **Week** - Week number (25-34)
- **Day** - Mon, Tue, Wed, Thu, Fri, Sat, Sun
- **Group** - Freshman, White, Green JV, Green Varsity, Gold JV, Gold Varsity
- **Pre** - Pre-run warmup (currently empty, can add Dynamics later)
- **Main_Workout** - The run (e.g., "4mi easy", "Long Run 6mi", "REST")
- **Post** - Post-run work (currently empty, can add mobility/strength)
- **Miles** - Total mileage for that day
- **Notes** - Training phase description (shows on Monday)

---

## 📝 Generating Markdown Output

To create clean markdown schedules from the CSVs:

```bash
python csv_to_markdown_track.py week33_schedule.csv
```

This creates `week33_schedule.md` with:
- Color-coded emojis (🔵🟢⚪🟡)
- Weekly totals separated by JV/Varsity
- Daily workouts grouped by level
- Clean formatting for GitHub

**Example Output:**
```markdown
# Track Week 33 Training Schedule
**PEAK MILEAGE WEEK**

## 📊 Weekly Mileage Totals

**JV Groups:**
🔵 Freshman: 30 mi | ⚪ White: 40 mi | 🟢 Green JV: 50 mi | 🟡 Gold JV: 60 mi

**Varsity Groups:**
🟢 Green Varsity: 44 mi | 🟡 Gold Varsity: 50 mi

## MONDAY

**WORKOUT:**

*JV Groups:*
- 🔵 Freshman: 4mi easy — 4 mi
- ⚪ White: 6mi easy — 6 mi
...
```

---

## 🎨 Key Differences from XC Format

### More Groups
- XC: 4 groups (Gold, Green, White, Freshman)
- Track: 6 groups (adds Green Varsity & Gold Varsity)

### Simpler Workouts
- XC: Complex workouts (intervals, tempo, hills, etc.)
- Track: All "easy" running or "long run" in base phase
- Later phases will add track-specific workouts

### Staggered Start
- Week 25: Only JV groups train
- Week 26: Varsity enters after XC season ends

---

## 💡 Customization Tips

### Adding Pre/Post Work
Edit the CSV to add warmup and cooldown:
```csv
Week,Day,Group,Pre,Main_Workout,Post,Miles,Notes
25,Mon,Gold JV,Dynamics,4mi easy,Mobility A,4,JV Base Building
```

### Changing Mileage
Simply edit the Miles column and Main_Workout description:
```csv
Before: 25,Mon,Freshman,,2mi easy,,2,
After:  25,Mon,Freshman,,3mi easy,,3,
```

### Modifying the Script
All training data is in `generate_track_schedules.py` in the `weeks_data` dictionary. Edit the numbers and re-run to regenerate everything.

---

## 📁 Recommended Setup

```
stx-track-training/
├── track_training_weeks_25-34.xlsx    (📊 Main file - edit here)
├── week25_schedule.csv                (Individual weeks)
├── week26_schedule.csv
├── ...
├── week34_schedule.csv
├── generate_track_schedules.py        (Regenerate all files)
└── csv_to_markdown_track.py           (Create markdown)
```

---

## 🚀 Quick Commands

```bash
# View all weeks at once
open track_training_weeks_25-34.xlsx

# Generate markdown for Week 33 (peak week)
python csv_to_markdown_track.py week33_schedule.csv

# Recreate all files from scratch
python generate_track_schedules.py
```

---

## 📌 Important Notes

1. **Base Phase Only:** These weeks are ALL easy running to build aerobic base
2. **No Workouts Yet:** Track-specific interval/tempo work comes in later phases
3. **Sunday = REST:** Every group has Sunday off
4. **Varsity Start Late:** Green/Gold Varsity start Week 26 (after XC season)
5. **Christmas Break:** Week 31 has normal volume despite holiday (athletes training on break)
6. **Peak Week 33:** Jan 5-11 is the highest mileage before track workouts begin

---

## ✨ Next Steps

1. **Review the Excel workbook** - `track_training_weeks_25-34.xlsx`
2. **Make any adjustments** to mileage/schedule as needed
3. **Generate markdown** for posting to GitHub:
   ```bash
   python csv_to_markdown_track.py week25_schedule.csv
   ```
4. **Commit to version control** - CSVs are git-friendly!

---

Questions or need modifications? The scripts are straightforward Python and easy to customize!
