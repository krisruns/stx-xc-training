# STX Training Site — Workflow Guide

*Updated November 16, 2026. Replaces the March 2026 version, which described the spring track process (Google Sheet → weekly CSVs → `week_schedule_mk46.py`).*

## Setup Summary

- **Files live in:** `Documents/stx-xc-training/` (local Git repo, synced through iCloud: `~/Library/Mobile Documents/com~apple~CloudDocs/Documents/stx-xc-training/`)
- **Site hosted at:** https://krisruns.github.io/stx-xc-training/
- **Planning source:** the schedule markdown files (see below). The Training Master Google Sheet was not used for fall 2026.
- **Tools:** VS Code, Python 3, Git
- **Pace data:** `athlete_groups.html` (VDOTs) and `training_paces.csv` (pace chart), both in the repo folder

---

## Schedule Files

One markdown file per phase. Week numbers run through the whole year, so `weekN.html` files from different files never collide.

| File | Weeks | Dates | Status |
|:--|:--|:--|:--|
| `STX_XC_2026_Complete_Schedule_Weeks_1-23.md` | 1–23 | May 25 – Nov 1, 2026 | Final record, don't edit |
| `STX_2026-27_Post_Season_Winter_Base_Schedule_Weeks_24-32.md` | 24–32 | Nov 2, 2026 – Jan 3, 2027 | Drafted |
| `STX_2027_Track_Schedule_Weeks_33-52.md` | 33–52 | Jan 4 – May 23, 2027 | Template, workouts TBD |

The latest copy of each also lives in the Coaching project in Claude.

---

## Weekly Workflow

### Step 1: Pull Latest Changes
1. Open VS Code
2. Click the **sync icon** (circular arrows, bottom left) to pull any changes from GitHub
3. Open the terminal: **Terminal → New Terminal**

### Step 2: Update the Schedule File
Edit the week in the right markdown file (format rules are below). If the plan was changed in a Claude chat, replace the file with the newest copy from that chat or the Coaching project.

### Step 3: Generate the Week Pages
In the VS Code terminal:
```bash
python3 generate_weekly_html_mk2.py
```
1. Pick the schedule file by number. The menu lists them in season order.
2. Enter the weeks you want, for example `26` or `25-28`.
3. If those pages already exist, it asks once whether to overwrite them.

It writes `weekN.html` to the repo folder, plus pace pages (Step 4). Read any `WARNING` lines. They usually mean a weekly header doesn't match the sum of the days.

> Use the terminal, not the **Run** button. The Run button wraps the iCloud path in extra quotes and Python can't find the file.

**Optional flags:**

| Flag | What it does |
|:--|:--|
| `--md FILE` | Skip the file menu |
| `--weeks 25,26` | Skip the week prompt |
| `--force` | Overwrite without asking |
| `--yes` | Generate every week in the file |

### Step 4: Pace Pages (Automatic)
Step 3 also builds the pace pages, as long as `athlete_groups.html` and `training_paces.csv` are in the repo folder. If either is missing, the script prints a NOTE and makes the week pages without pace links.

For each workout with paced reps (`@T`, `@I`, `@R`, `@RP`) it:
- writes `pace_pages/weekN_{day}_paces.html`, for example `week26_wednesday_paces.html`
- writes a separate page for JV or Post Season workouts, for example `week26_wednesday_postseason_paces.html`
- adds a **⏱ Paces** button next to that workout on the week page

Each athlete's times come from their VDOT on `athlete_groups.html` and the Training Paces chart:

| Code | Chart column |
|:--|:--|
| `@T` | Tempo |
| `@I` and `@RP` | 5K pace |
| `@R` | Mile pace |

Distances that aren't on the chart (such as 800m@I) are scaled from the nearest distance in the same zone. Timed or mile segments (`20min@T`, `2mi@T`) show a per-mile pace.

**Before running:** update `athlete_groups.html` when the roster or VDOTs change. The pace pages are only as current as that file.

**Special workouts (hills, odd distances):** make that page by hand, for example in a Claude chat, and save it with the same file name. The script only overwrites pages it made itself, and it prints `Kept hand-made ...` for the rest. This season's fall pace pages are all hand-made, so they're safe. To let the script take a page back over, delete it and run again.

### Step 5: Review
Open the new pages in a browser and check the totals, override rows (Varsity/JV or Base/Post Season), and the ⏱ Paces pages.

### Step 6: Deploy to GitHub
```bash
python3 deploy.py
```
- Review the list of changed files
- Type `y` to confirm
- Enter a commit message (e.g., `Add week 26 schedule`) or press Enter for the default
- Site goes live in about 30 seconds

---

## Schedule File Format

Each week is a heading, an optional note in italics, then one table:

```markdown
## **WEEK 26: NOVEMBER 16–22, 2026** — Nike Cross Regionals

| Day | Blue (20 mi) | White (24 mi) | Green (28 mi) | Gold (32 mi) |
|:----|:---|:---|:---|:---|
| **Mon** | Easy *3mi* | Easy *4mi* | Easy *4.5mi* | Easy *5mi* |
| **Tue** | **Fartlek 1 — 3x(1:00 on/4:00 steady)** *4mi* | ... |
| **Sun** | **REST** | **REST** | **REST** | **REST** |
```

| Cell type | Example |
|:--|:--|
| Easy run | `Easy *4mi*` or `Easy *4mi + 5x20sec strides*` |
| Time only | `Easy *20-30min*` (miles worked out from the group's easy pace) |
| Workout | `**4x1000m@T w/1:00 + 4x200m@R** *6mi*` |
| Long run | `**Long Run** *8mi*` |
| Race | `**Nike Cross Regionals** *6mi*` |
| Rest | `**REST**` |

**Override tables** go directly under the main table, listing only the days and groups that differ (blank cells follow the main table):
- `#### JV Overrides`: the main table is Varsity
- `#### Post Season Overrides`: the main table is the Base group (not racing)

**Minutes to miles.** For time-only cells, the script uses these easy paces. Edit `PACE_MIN_PER_MILE` near the top of the script if they change.

| Gold | Green | White | Blue |
|:--|:--|:--|:--|
| 7:30/mi | 8:00/mi | 8:30/mi | 9:00/mi |

**Headers** should equal the sum of the days. The script calculates its own totals and warns you when a header doesn't match.

---

## Training Rules Built Into the Plans

- Weekly mileage goes up no more than 10% during a build.
- Winter peak is capped at XC peak plus the smaller of 5 miles or 10% (Blue 28, White 38.5, Green 49.5, Gold 60).
- Sunday is a rest day unless it's a race day.

---

## Retired Scripts (Spring 2026 Track Process)

Not used for fall 2026. Kept for reference until the track planning process is decided.

| Script | Purpose |
|:--|:--|
| `overview_to_week_schedule.py` | Training Master CSV → weekly CSVs in `weekly_schedules/` |
| `generate_workout_pace_mk10.py` (and earlier versions) | Training Master CSV → pace pages; replaced by the pace pages in `generate_weekly_html_mk2.py` |
| `week_schedule_mk46.py` | Weekly CSV → `weekXX.html` |
| `csv_to_markdown.py` | Weekly CSV → markdown |
| `inspect_paces.py` | Debug the training paces CSV |

Still in use: `generate_groups_mk6.py` (athlete groups by VDOT), `generate_training_overview.py`, `deploy.py`.

---

## Multi-Computer Workflow

If working from a **secondary machine** (e.g., editing at school):

1. Open VS Code
2. **Always pull first:** click the sync icon in the bottom left
3. Make your edits
4. In the **Source Control** panel, stage changes with **+**, write a commit message, click **Commit**, then **Sync Changes**

> Run the Python scripts from your main Mac. Editing markdown or HTML can be done from any machine.

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

**"can't open file ... /"/Users/..." No such file or directory"**
That's the Run button's quoting. Run `python3 generate_weekly_html_mk2.py` in the terminal instead.

**Which Python am I using?**
VS Code shows it in the bottom-right status bar when a `.py` file is open. In the terminal:
```bash
which python3
python3 --version
```
`/opt/homebrew/...` is Homebrew Python. A path with `anaconda3` is Anaconda. To switch: `Cmd+Shift+P` → **Python: Select Interpreter**. The weekly page script only needs standard Python. The older scripts that use pandas need the Anaconda interpreter.

**The file menu doesn't list a schedule**
The markdown file must be in the repo folder and have `Schedule` in its name. Check you're in the right folder with `pwd`.

**WARNING: header says X mi but the days add up to Y**
Fix the header in the markdown to match the days, or fix the day that's wrong.

**No ⏱ Paces buttons on the week page**
The script printed `NOTE: no pace pages this run`, meaning `athlete_groups.html` or `training_paces.csv` isn't in the repo folder. The workout also needs a pace code written right after the distance, like `6x300m@R`. Fartleks, progressions and hill loops don't get a pace page.

**A pace page shows "no VDOT"**
That athlete has no VDOT on `athlete_groups.html`.

**Nothing to deploy**
Your local files already match GitHub. Make sure you saved your files before running `deploy.py`.

**Merge conflict on a secondary machine**
Open the Source Control panel. VS Code highlights the conflicting lines with options to accept current or incoming changes.
