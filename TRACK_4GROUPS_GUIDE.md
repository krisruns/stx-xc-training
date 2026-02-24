# 🏃 Track Training - 4 Groups System

## 📦 What You Have

A complete 10-week track training progression (Weeks 25-34) with **4 groups** only:
- 🟡 Gold
- 🟢 Green  
- ⚪ White
- 🔵 Freshman

---

## 📥 Your Files

### **Main File - Excel Workbook:**
**STX_Track_Weeks_25-34_4Groups.xlsx**
- 10 tabs (one per week)
- Ready to edit in Excel or Google Sheets
- Format compatible with csv_to_html_v2.py and csv_to_markdown_v2.py

### **Individual CSV Files:**
- week25_schedule.csv through week34_schedule.csv
- Each week as a separate file
- Perfect for version control / git

### **Generation Script:**
- generate_track_4groups.py - Recreates everything if needed

### **Sample Outputs:**
- week33_schedule.md - Peak week markdown
- week33_schedule.html - Peak week HTML

---

## 📊 Schedule Overview

**Weeks 25-34:** November 10, 2025 - January 18, 2026

| Week | Phase | Freshman | White | Green | Gold |
|------|-------|----------|-------|-------|------|
| 25 | Base Building | 15 mi | 20 mi | 25 mi | 30 mi |
| 26 | Thanksgiving | 18 mi | 24 mi | 30 mi | 36 mi |
| 27 | Building | 21 mi | 28 mi | 35 mi | 42 mi |
| 28 | Continued Build | 24 mi | 32 mi | 40 mi | 48 mi |
| 29 | Pre-Break Peak | 27 mi | 36 mi | 45 mi | 54 mi |
| 30 | Pre-Christmas | 21 mi | 28 mi | 35 mi | 42 mi |
| 31 | Christmas Break | 27 mi | 36 mi | 45 mi | 54 mi |
| 32 | Post-Break Build | 27 mi | 36 mi | 45 mi | 54 mi |
| **33** | **PEAK WEEK** | **30 mi** | **40 mi** | **50 mi** | **60 mi** |
| 34 | Post-Peak | 28 mi | 38 mi | 48 mi | 58 mi |

---

## 🎯 CSV Format

Each week has this structure:

```csv
Week,Day,Group,Status,Pre,Main_Workout,Post,Miles,Notes
25,Mon,Gold,,,4mi easy,,4,Base Building
25,Mon,Green,,,3mi easy,,3,
25,Mon,White,,,3mi easy,,3,
25,Mon,Freshman,,,2mi easy,,2,
```

**Key Columns:**
- **Week** - Week number (25-34)
- **Day** - Mon, Tue, Wed, Thu, Fri, Sat, Sun
- **Group** - Gold, Green, White, Freshman
- **Status** - Leave blank for normal days, use "Racer" or "Non-Racer" for race days
- **Pre** - Pre-run warmup (currently blank, can add Dynamics, etc.)
- **Main_Workout** - The run (e.g., "4mi easy", "Long Run 6mi", "REST")
- **Post** - Post-run work (currently blank, can add Mobility, Strides, etc.)
- **Miles** - Total mileage
- **Notes** - Training phase (shows on Monday)

---

## ✏️ Editing Workflow

### **Option 1: Edit Excel Workbook (Easiest)**
1. Open `STX_Track_Weeks_25-34_4Groups.xlsx`
2. Click between tabs to view different weeks
3. Edit cells directly
4. Save
5. Export individual sheets as CSV if needed for git

### **Option 2: Edit Individual CSVs**
1. Open `week25_schedule.csv` (or any week)
2. Edit in Excel, Google Sheets, or text editor
3. Save

### **Option 3: Edit and Regenerate**
1. Modify `generate_track_4groups.py` 
2. Run: `python generate_track_4groups.py`
3. Recreates all files from scratch

---

## 🎨 Generating HTML/Markdown

### **Generate for One Week:**
```bash
# Markdown
python csv_to_markdown_v2.py week25_schedule.csv

# HTML
python csv_to_html_v2.py week25_schedule.csv

# Both
python csv_to_markdown_v2.py week25_schedule.csv && python csv_to_html_v2.py week25_schedule.csv
```

### **Generate All 10 Weeks:**
```bash
# Markdown for all weeks
for week in {25..34}; do
    python csv_to_markdown_v2.py week${week}_schedule.csv
done

# HTML for all weeks
for week in {25..34}; do
    python csv_to_html_v2.py week${week}_schedule.csv
done
```

---

## 🏁 Adding Race Days

If some groups race and others don't, use the **Status** column:

### **Example: Saturday Race Day**

```csv
Week,Day,Group,Status,Pre,Main_Workout,Post,Miles,Notes
25,Sat,Gold,Racer,Dynamics,RACE - 5K,Cooldown,6,Meet Name
25,Sat,Green,Racer,Dynamics,RACE - 5K,Cooldown,6,
25,Sat,White,Non-Racer,Dynamics,Long Run 6mi,Mobility A,6,
25,Sat,Freshman,Non-Racer,Dynamics,Long Run 4mi,Drills,4,
```

This will create **two sections** on Saturday:
1. **Racers** - Gold, Green racing
2. **Non-Racers** - White, Freshman doing long run

---

## 💡 Common Modifications

### **Add Pre/Post Work:**
```csv
Week,Day,Group,Status,Pre,Main_Workout,Post,Miles,Notes
25,Mon,Gold,,Dynamics,4mi easy,Strides + Mobility A,4,
```

### **Change a Workout:**
```csv
Week,Day,Group,Status,Pre,Main_Workout,Post,Miles,Notes
25,Tue,Gold,,Dynamics,3mi@T + 4x200m@R,Strides,7,
```

### **Adjust Mileage:**
Just change the Miles column and update Main_Workout to match:
```csv
Before: 25,Mon,Gold,,,4mi easy,,4,
After:  25,Mon,Gold,,,5mi easy,,5,
```

---

## 🔧 Key Scripts You Need

### **For Track Schedules (4 groups):**
- `csv_to_markdown_v2.py` - Generates markdown
- `csv_to_html_v2.py` - Generates HTML
- Both support Status column for Racer/Non-Racer splits

### **Regenerating Everything:**
- `generate_track_4groups.py` - Recreates all CSVs and Excel file

---

## 📚 Training Notes

**All workouts are EASY running:**
- This is base-building phase
- No speed work yet
- Focus on aerobic development
- Track workouts come later

**Long Runs:**
- Saturday only
- 18-25% of weekly volume
- Vary by group

**Rest Day:**
- Sunday is always OFF
- Critical for recovery

**Peak Week (33):**
- Highest volume: 60mi (Gold) down to 30mi (Freshman)
- Week of January 5-11, 2026
- Then reduce slightly in Week 34

---

## 🎯 Quick Commands

```bash
# View Excel file
open STX_Track_Weeks_25-34_4Groups.xlsx

# Generate Week 33 (peak week) outputs
python csv_to_markdown_v2.py week33_schedule.csv
python csv_to_html_v2.py week33_schedule.csv

# View HTML in browser
open week33_schedule.html

# Generate all weeks
for w in {25..34}; do 
    python csv_to_markdown_v2.py week${w}_schedule.csv
    python csv_to_html_v2.py week${w}_schedule.csv
done
```

---

## ✨ What Makes This Different

**vs. Original 6-Group System:**
- ❌ NO separate JV/Varsity groups
- ✅ JUST 4 core groups (simpler!)
- ✅ Use Status column for race day splits when needed

**vs. XC System:**
- ✅ SAME 4 groups
- ✅ SAME v2 scripts work
- ✅ SAME Status/Racer flexibility
- ✅ Just different phase and mileage targets

---

## 📁 Recommended Setup

```
stx-track-training/
├── STX_Track_Weeks_25-34_4Groups.xlsx  ← Edit this!
├── csv_to_markdown_v2.py
├── csv_to_html_v2.py
├── generate_track_4groups.py
├── week25_schedule.csv
├── week26_schedule.csv
│   ... (all weeks)
└── week34_schedule.csv
```

---

## 🆘 Troubleshooting

**Q: I edited the Excel file, how do I get updated CSVs?**
A: Export each sheet individually, or edit the CSV files directly instead.

**Q: My HTML/markdown looks wrong**
A: Make sure you're using csv_to_html_v2.py and csv_to_markdown_v2.py (v2 versions!)

**Q: Can I add a 5th group?**
A: Yes, just add more rows to the CSV with the new group name. Scripts will handle it.

**Q: The Status column isn't working**
A: Make sure values are exactly "Racer" or "Non-Racer" (case-sensitive), and you're using v2 scripts.

---

That's it! You now have a clean 4-group track training system that works exactly like your XC system.
