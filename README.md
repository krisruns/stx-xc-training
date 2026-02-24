# STX XC Training Schedule - Simplified Format

## 📁 What You Get

This system replaces your complex HTML files with a **simple CSV + auto-generation** workflow.

### Files:
- **`week12_schedule.csv`** - Easy-to-edit schedule (edit this in Excel/Sheets)
- **`csv_to_markdown.py`** - Generates clean markdown for GitHub
- **`csv_to_html.py`** - Generates simple filterable HTML
- **`week12_schedule.md`** - Auto-generated markdown (commit to GitHub)
- **`week12_schedule.html`** - Auto-generated HTML with filtering

---

## ✏️ Editing Workflow

### **Your Current Process:**
1. ❌ Edit massive HTML file (~500+ lines)
2. ❌ Copy/paste workout sections
3. ❌ Manually update styles and filters
4. ❌ Risk breaking JavaScript
5. ❌ 30+ minutes per week

### **New Process:**
1. ✅ Open CSV in Excel/Sheets
2. ✅ Edit workouts (plain text)
3. ✅ Run: `python csv_to_markdown.py week12_schedule.csv`
4. ✅ Commit to GitHub
5. ✅ **5 minutes per week**

---

## 🔧 CSV Format

Super simple, just 8 columns:

| Week | Day | Group | Pre | Main_Workout | Post | Miles | Notes |
|------|-----|-------|-----|--------------|------|-------|-------|
| 12 | Mon | Gold | Dynamics | 8mi easy | Strides + Weights | 8 | |
| 12 | Mon | Green | Dynamics | 6.5mi easy | Strides | 6.5 | |

**Tips:**
- Leave cells blank for "none" (like rest days)
- Pre = warmup activities (Dynamics, etc.)
- Post = cooldown (Strides, Mobility, etc.)
- Notes = special instructions (optional)

---

## 🚀 Quick Start

### Option 1: Markdown Only (Simplest)
```bash
python csv_to_markdown.py week12_schedule.csv
git add week12_schedule.md
git commit -m "Week 12 schedule"
git push
```

### Option 2: Both Markdown + HTML
```bash
python csv_to_markdown.py week12_schedule.csv
python csv_to_html.py
git add week12_schedule.md week12_schedule.html
git commit -m "Week 12 schedule"
git push
```

### Option 3: Auto-Script (Create once)
```bash
# Create update_schedule.sh
#!/bin/bash
python csv_to_markdown.py week$1_schedule.csv
python csv_to_html.py week$1_schedule.csv
git add week$1_schedule.*
git commit -m "Week $1 schedule"
git push

# Then just run:
./update_schedule.sh 12
```

---

## 📊 What It Generates

### Markdown Output:
- Clean GitHub-readable format
- Tables for each day
- Weekly totals at top
- Pace key at bottom
- **Perfect for viewing on GitHub**

### HTML Output (Optional):
- Minimal, fast-loading design
- Click-to-filter by group
- Mobile-friendly
- ~100 lines vs your current ~500+ lines
- **Same filtering, 80% less code**

---

## 🎯 Benefits

| Before | After |
|--------|-------|
| 500+ lines of HTML | 30 lines of CSV |
| Complex nested divs | Simple spreadsheet |
| 30 min to edit | 5 min to edit |
| Easy to break | Hard to break |
| Manual updates | Auto-generated |
| Hard to version control | Git-friendly |

---

## 🔄 Adapting for Other Weeks

### Method 1: Copy CSV
```bash
cp week12_schedule.csv week13_schedule.csv
# Edit week13_schedule.csv
python csv_to_markdown.py week13_schedule.csv
```

### Method 2: Template
Keep a blank template with all groups/days, just fill in workouts:
```csv
Week,Day,Group,Pre,Main_Workout,Post,Miles,Notes
13,Mon,Gold,,,,,
13,Mon,Green,,,,,
...
```

---

## 💡 Pro Tips

1. **Use formulas in Excel** to auto-calculate weekly totals
2. **Keep workout menu** in separate CSV (your current Workout Menu 1.csv works great)
3. **Version control the CSV** - easy to see week-to-week changes in git diff
4. **Link to workout groups** - just put "See workout groups" in Notes column
5. **Multi-week planning** - put weeks 12-15 all in one CSV if you want

---

## 🆘 Need Changes?

Easy to modify the scripts:

**Want different styling?** → Edit CSS in `csv_to_html.py` (lines 30-60)  
**Want more columns?** → Add to CSV, update script  
**Want emojis in headers?** → Edit `generate_markdown()` function  
**Want workout links?** → Add URL column to CSV  

---

## 📝 Next Steps

1. **Test with Week 12** - make sure you like the output
2. **Create Week 13** - practice the workflow
3. **Archive old HTML files** - you won't need them anymore
4. **Enjoy your free time** - spend 25 minutes less per week on formatting!

---

Questions? The scripts are simple Python - easy to customize to your exact needs.
