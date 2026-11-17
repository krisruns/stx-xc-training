# STX XC Training Site — Workflow Guide

## Setup Summary

- **Files live in:** `Documents/stx-xc-training/` (local Git repo)
- **Site hosted at:** https://krisruns.github.io/stx-xc-training/
- **Data source:** Google Sheets (Training Master)
- **Tools:** VS Code, Python 3 (Anaconda), Git

---

## Weekly Workflow — New Week Schedule

Follow these steps in order each week.

### Step 1: Export Google Sheet
1. Open **Training Master** in Google Sheets
2. **File → Download → Comma Separated Values (.csv)**
3. Save to `Documents/stx-xc-training/` replacing existing `Training Master - Training_Overview.csv`

### Step 2: Open VS Code and Pull Latest Changes
1. Open VS Code
2. In the bottom left corner, click the **sync icon** (circular arrows) to pull any changes from GitHub
3. Open the terminal: **Terminal → New Terminal**

### Step 3: Generate Weekly Schedule CSVs
```bash
python3 overview_to_week_schedule.py
```
This reads the Training Master CSV and generates weekly CSVs in the `/weekly_schedules` folder.

### Step 4: Generate Workout Pace Pages
```bash
python3 generate_workout_pace_mk4.py
```
This reads the weekly CSVs and generates workout-specific pace pages in `/pace_pages`.

### Step 5: Generate Week HTML
```bash
python3 week_schedule_mk46.py
```
Enter the week number when prompted. This generates `weekXX.html` in the root folder.

### Step 6: Deploy to GitHub
```bash
python3 deploy.py
```
- Review the list of changed files
- Type `y` to confirm
- Enter a commit message (e.g., `Add week 41 schedule`) or press Enter for default
- Site goes live in ~30 seconds

---

## Other Scripts

| Script | Purpose | How to Run |
|--------|---------|------------|
| `generate_groups_mk6.py` | Assign athletes to training groups based on VDOT | `python3 generate_groups_mk6.py` |
| `generate_training_overview.py` | Generate training overview HTML from master CSV | `python3 generate_training_overview.py` |
| `csv_to_markdown.py` | Convert weekly CSV to markdown format | `python3 csv_to_markdown.py weekXX.csv` |
| `inspect_paces.py` | Debug training paces CSV column structure | `python3 inspect_paces.py` |

---

## Key Files

| File | Description |
|------|-------------|
| `Training Master - Training_Overview.csv` | Master training plan (exported from Google Sheets) |
| `training_paces.csv` | Jack Daniels VDOT lookup table |
| `Athlete_Groups - Data.csv` | Athlete performance data for VDOT calculations |
| `Roster.csv` | Full team roster |
| `workout_library.csv` | Workout descriptions and key points |
| `weekly_schedules/weekXX.csv` | Generated weekly schedule CSVs |
| `pace_pages/` | Generated workout pace HTML pages |
| `athlete_groups.html` | Current training group assignments |
| `deploy.py` | Deployment script — pushes changes to GitHub |

---

## Multi-Computer Workflow

If working from a **secondary machine** (e.g., editing HTML at school):

1. Open VS Code
2. **Always pull first** — click the sync icon in the bottom left
3. Make your edits
4. Go to **Source Control** panel, stage changes with **+**, write a commit message, click **Commit**, then **Sync Changes**

> **Important:** Python scripts should only be run from your **main machine** (Mac with Anaconda). HTML editing can be done from any machine.

---

## Git Quick Reference

| Task | VS Code | Terminal |
|------|---------|----------|
| Pull latest changes | Click sync icon (bottom left) | `git pull` |
| Stage all changes | Click **+** next to Changes in Source Control | `git add .` |
| Commit | Type message, click Commit ✓ | `git commit -m "message"` |
| Push | Click Sync Changes | `git push origin main` |
| Full deploy | — | `python3 deploy.py` |

---

## Troubleshooting

**Script can't find CSV file**
Make sure you're running the script from the repo root in VS Code terminal. Check with:
```bash
pwd
```
Should show `.../Documents/stx-xc-training`

**Wrong Python version / pandas not found**
Make sure VS Code is using the Anaconda interpreter:
- Press `Cmd+Shift+P` → **Python: Select Interpreter** → choose the Anaconda path

**Nothing to deploy**
If `deploy.py` says "Nothing to deploy", your local files match GitHub already. Make sure you saved your files in VS Code before running.

**Merge conflict on secondary machine**
If you see a merge conflict after pulling, open VS Code's Source Control panel — it will highlight the conflicting lines with options to accept current or incoming changes.
