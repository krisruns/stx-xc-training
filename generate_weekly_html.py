#!/usr/bin/env python3
"""
generate_weekly_html.py

Reads the STX XC markdown season schedule and produces one styled weekly
HTML page per week (Week 1 ... Week 23). The page layout/CSS/JS ("Easy Run"
modal, group filters, colors, etc.) is baked into this script as constants
(STYLE_BLOCK / SCRIPT_BLOCK / MODAL_BLOCK below) so every generated page
uses the exact same format every time - no template file needed.

Usage:
    # Simplest: run it from inside the folder with the schedule .md and the
    # support pages (mobility-strength.html, etc). It auto-detects the
    # markdown file, writes output into the same folder (so the ref-page
    # links keep working), and prompts for which week(s) you want:
    python3 generate_weekly_html.py
    # -> Using schedule markdown: STX_XC_2026_Complete_Schedule_Weeks_1-23.md
    # -> Using output folder: /Users/you/.../stx-xc-training
    # -> Which week(s) do you want to generate? (e.g. 5, 5-7, 5,9,14-16, or 'all') [1-23]: 14-16

    # Explicit paths (e.g. running from a different folder):
    python3 generate_weekly_html.py \
        --md STX_XC_2026_Complete_Schedule_Weeks_1-23.md \
        --outdir out/

    # Non-interactive range, e.g. just weeks 14-16 (won't touch week1.html..week13.html):
    python3 generate_weekly_html.py --start 14 --end 16

    # Specific, possibly non-contiguous weeks:
    python3 generate_weekly_html.py --weeks 9,14,22

    # Regenerate everything, no prompts, overwriting freely:
    python3 generate_weekly_html.py --yes --force

Flags:
    --md PATH         schedule markdown file (auto-detected in the current
                      folder if omitted - looks for *Schedule*.md, then any *.md)
    --outdir DIR      where to write weekN.html files (defaults to the
                      current folder if omitted)
    --weeks 1,2,3     generate exactly these week numbers (overrides --start/--end)
    --start N [--end M]  generate a contiguous range; --end defaults to the last
                      week found in the markdown file if omitted
    --yes / -y        skip the interactive week-selection prompt and generate every week
    --force           overwrite existing weekN.html files without asking
    If --md/--outdir aren't given, the script tries to find/default them
    itself and only prompts you if it can't (e.g. more than one .md file is
    present). If --weeks/--start/--yes aren't given, it prompts for which
    week(s) you want - a single number, a range like 5-7, a comma list like
    5,9,14-16, or 'all' - and asks for confirmation before overwriting any
    weekN.html that already exists.

To change the page's look/behavior for every future week: edit STYLE_BLOCK,
SCRIPT_BLOCK, or MODAL_BLOCK below (these were originally lifted from the
hand-built week13.html example) - there's nothing else to keep in sync.

Notes / assumptions (read this if a week looks off):
  - Workout "type" is inferred per table CELL from the markdown wording:
      REST            -> cell is "**REST**"
      Long Run        -> bold label contains "long run"
      Race            -> bold label contains a race/meet keyword
                          (race, trial, invitational, classic, showcase,
                          regional, championships, meet, tiger run,
                          alumni run, run for the gold, haunted woods,
                          palatine, state)
      Quality/Workout -> bold label with rep/pace patterns
                          (fartlek, progression, hill repeats, NxM, @T/@I/@R,
                          distances like 800m/1000m/1200m/1600m/200m/300m/400m)
      Easy            -> everything else (default)
  - Pre/post routine tags are assigned by (day-of-week, type):
        Monday + easy      -> Foot Drills, Dynamics, Buildups / Strides, Mobility/Strength A
        other day + easy   -> WU, Dynamics, stride progression / Strides, Mobility/Strength A
        quality            -> WU, Dynamics, stride progression /
                                 Strides+Mobility A   (if the workout already ends in strides, i.e. "@R"/"200m")
                                 Mobility/Strength B  (otherwise)
        long run           -> Awesomizer, Lunge Matrix / Strides, Mobility A, 24s
        race               -> Race Day WU / Post Race
        rest               -> (no pre/post, shown as a plain REST row)
    These rules were reverse-engineered from the one hand-built example
    (Week 13) and are easy to edit below in `build_workout()` if St. X
    coaches want different wording.
  - The "info" (i) icon + Easy Run modal is only attached to Easy workouts,
    matching the reference page.
  - A day gets the small "👥 Groups" button whenever at least one group's
    workout that day is a "quality" session (matches the reference page,
    where only Wed/Thu had it in Week 13).
  - If a markdown row is missing trailing cells (a couple of weeks have
    this - e.g. Week 3 Sunday only lists 3 of 4 groups), the last present
    cell's content is reused for the missing group(s) and a warning is
    printed so you can double check the source markdown.
"""

import argparse
import os
import re
import sys

DAY_ORDER = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_FULL = {
    "Mon": "MONDAY", "Tue": "TUESDAY", "Wed": "WEDNESDAY", "Thu": "THURSDAY",
    "Fri": "FRIDAY", "Sat": "SATURDAY", "Sun": "SUNDAY",
}
GROUP_DISPLAY_ORDER = ["Gold", "Green", "White", "Blue"]
GROUP_CLASS = {"Gold": "gold", "Green": "green", "White": "white", "Blue": "blue"}

RACE_KEYWORDS = [
    "race", "trial", "invitational", "classic", "showcase", "regional",
    "championships", "meet", "tiger run", "alumni run", "run for the gold",
    "haunted woods", "palatine", "state",
]
QUALITY_KEYWORDS = ["fartlek", "progression", "hill repeats"]
QUALITY_PATTERNS = [
    re.compile(r"\d+\s*x", re.I),          # "5x800m", "3x(1:00 on/4:00 off)"
    re.compile(r"@[tirp]", re.I),          # "@T", "@I", "@R", "@RP"
    re.compile(r"\d{3,4}m", re.I),         # 200m/300m/400m/800m/1000m/1200m/1600m
]

REF_WARMUP = "STX_XC_Movement___Warmup_Reference.html"
REF_FOOT = "STX_XC_Foot_Drills_Reference.html"
REF_MOBILITY = "mobility-strength.html"


# ---------------------------------------------------------------------------
# Fixed page format (CSS / JS / "Easy Run" modal) - reused verbatim for
# every generated week so the output format never varies. Originally
# lifted from the hand-built week13.html example. Edit these three
# constants to change the look/behavior of every future generated page.
# ---------------------------------------------------------------------------

STYLE_BLOCK = """    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; max-width: 1000px; margin: 20px auto; padding: 0 20px; background: #fafafa; }
        h1 { color: #2c5530; border-bottom: 3px solid #4a7c59; padding-bottom: 10px; }
        .subtitle { color: #666; margin-bottom: 20px; }
        .totals { display: flex; gap: 10px; margin: 20px 0; flex-wrap: wrap; }
        .total { padding: 15px 20px; background: white; border-radius: 6px; flex: 1; min-width: 140px; text-align: center; cursor: pointer; transition: all 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .total:hover { transform: translateY(-2px); box-shadow: 0 2px 6px rgba(0,0,0,0.15); }
        .total.gold { border-left: 4px solid #DAA520; }
        .total.gold.active { background: #DAA520; color: white; }
        .total.green { border-left: 4px solid #4a7c59; }
        .total.green.active { background: #4a7c59; color: white; }
        .total.white { border-left: 4px solid #888; }
        .total.white.active { background: #888; color: white; }
        .total.freshman, .total.blue { border-left: 4px solid #4169E1; }
        .total.freshman.active, .total.blue.active { background: #4169E1; color: white; }
        .total-label { font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px; }
        .total-miles { font-size: 1.8rem; font-weight: 700; }
        .filters { margin: 20px 0; text-align: center; }
        .filter-btn { padding: 8px 16px; margin: 0 5px 5px 0; border: 2px solid #4a7c59; background: white; color: #4a7c59; border-radius: 4px; cursor: pointer; font-size: 0.9rem; transition: all 0.2s; }
        .filter-btn:hover, .filter-btn.active { background: #4a7c59; color: white; }
        
        /* Week Notes Section */
        .week-notes { 
            margin: 25px 0; 
            border-radius: 8px; 
            overflow: hidden; 
            background: #FFF9E6; 
            border: 3px solid #DAA520; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        }
        .notes-header { 
            background: linear-gradient(135deg, #DAA520 0%, #B8860B 100%); 
            padding: 15px 20px; 
            color: white; 
            font-size: 1.2rem; 
            font-weight: 700; 
            letter-spacing: 0.5px; 
        }
        .notes-content { 
            padding: 20px; 
            color: #333; 
        }
        .notes-content p { 
            margin: 0 0 10px 0; 
        }
        .notes-content ul { 
            margin: 10px 0 0 20px; 
        }
        .notes-content li { 
            margin-bottom: 5px; 
        }
        
        .day { margin: 25px 0; border-radius: 8px; overflow: hidden; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .day-header { 
            background: linear-gradient(135deg, #2c5530 0%, #4a7c59 100%); 
            padding: 15px 20px; 
            color: white; 
            font-size: 1.2rem; 
            font-weight: 700; 
            letter-spacing: 0.5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .groups-btn {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            padding: 6px 12px;
            border-radius: 4px;
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 600;
            transition: all 0.2s;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        .groups-btn:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-1px);
        }
        .back-btn {
            display: inline-block;
            margin-bottom: 12px;
            padding: 7px 14px;
            background: white;
            color: #2c5530;
            border: 2px solid #4a7c59;
            border-radius: 4px;
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 600;
            transition: all 0.2s;
        }
        .back-btn:hover {
            background: #4a7c59;
            color: white;
        }
        .day-content { padding: 20px; }
        .status-section { margin-bottom: 25px; }
        .status-section:last-child { margin-bottom: 0; }
        .status-title { font-size: 1.1rem; font-weight: 700; color: #2c5530; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 2px solid #e0e0e0; }
        .section { margin-bottom: 20px; }
        .section:last-child { margin-bottom: 0; }
        .section-label { font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: #666; margin-bottom: 10px; letter-spacing: 0.5px; }
        .workout-item { padding: 10px 15px; margin-bottom: 8px; border-radius: 4px; display: flex; align-items: center; gap: 12px; transition: all 0.2s; }
        .workout-item:last-child { margin-bottom: 0; }
        .workout-item.hidden { display: none; }
        .workout-item.gold { background: #FFF9E6; border-left: 4px solid #DAA520; }
        .workout-item.green { background: #F0F9F0; border-left: 4px solid #4a7c59; }
        .workout-item.white { background: #F5F5F5; border-left: 4px solid #888; }
        .workout-item.freshman, .workout-item.blue { background: #E6F0FF; border-left: 4px solid #4169E1; }
        .workout-item:hover { transform: translateX(5px); }
        .group-badge { font-weight: 700; min-width: 80px; font-size: 0.9rem; text-transform: uppercase; }
        .group-badge.gold { color: #B8860B; }
        .group-badge.green { color: #2c5530; }
        .group-badge.white { color: #555; }
        .group-badge.freshman, .group-badge.blue { color: #1E3A8A; }
        .workout-desc { flex: 1; font-size: 0.95rem; display: flex; align-items: center; gap: 8px; }
        .workout-details { flex: 1; display: flex; flex-direction: column; gap: 4px; }
        .workout-pre, .workout-post { font-size: 0.85rem; color: #666; }
        .workout-pre { font-style: italic; }
        .workout-post { font-style: italic; }
        .ref-link { 
            color: #4a7c59; 
            text-decoration: none; 
            border-bottom: 1px dotted #4a7c59;
            transition: all 0.2s;
        }
        .ref-link:hover { 
            color: #2c5530; 
            border-bottom-style: solid;
        }
        .pace-link {
            display: inline-block;
            margin-left: 8px;
            padding: 3px 10px;
            background: #1976d2;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 0.8rem;
            font-weight: 600;
            transition: all 0.2s;
        }
        .pace-link:hover {
            background: #1565c0;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .workout-miles { font-weight: 700; font-size: 1rem; white-space: nowrap; }
        .info-icon { 
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #4a7c59;
            color: white;
            font-size: 0.75rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
            flex-shrink: 0;
        }
        .info-icon:hover {
            background: #2c5530;
            transform: scale(1.1);
        }
        
        /* Modal Styles */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.6);
            overflow-y: auto;
        }
        .modal.active { display: flex; align-items: center; justify-content: center; }
        .modal-content {
            background: white;
            padding: 30px;
            border-radius: 12px;
            max-width: 600px;
            width: 90%;
            max-height: 90vh;
            overflow-y: auto;
            position: relative;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            margin: 20px;
        }
        .modal-close {
            position: absolute;
            top: 15px;
            right: 20px;
            font-size: 2rem;
            font-weight: 700;
            color: #999;
            cursor: pointer;
            transition: color 0.2s;
        }
        .modal-close:hover { color: #333; }
        .modal-content h2 {
            color: #2c5530;
            margin: 0 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 3px solid #4a7c59;
        }
        .modal-section {
            margin-bottom: 20px;
        }
        .modal-section h3 {
            color: #4a7c59;
            font-size: 1.1rem;
            margin: 0 0 10px 0;
        }
        .modal-section p {
            color: #333;
            line-height: 1.6;
            margin: 0;
        }
        .key-points {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        .key-points li {
            padding: 8px 0 8px 25px;
            position: relative;
            color: #333;
            line-height: 1.5;
        }
        .key-points li:before {
            content: "→";
            position: absolute;
            left: 0;
            color: #4a7c59;
            font-weight: 700;
        }
        .pace-chart-link {
            background: #e8f5e8;
            border: 2px solid #4a7c59;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 20px;
            text-align: center;
        }
        .pace-chart-link a {
            color: #2c5530;
            text-decoration: none;
            font-weight: 600;
            font-size: 1.05rem;
        }
        .pace-chart-link a:hover {
            color: #4a7c59;
            text-decoration: underline;
        }
        
        @media (max-width: 768px) {
            .totals { flex-direction: column; }
            .workout-item { flex-direction: column; align-items: flex-start; gap: 8px; }
            .workout-miles { align-self: flex-end; }
            .modal-content { padding: 20px; margin: 10px; }
        }
    </style>"""

SCRIPT_BLOCK = """    <script>
        let currentFilter = null;
        
        function filterGroup(group) {
            currentFilter = group;
            document.querySelectorAll('.workout-item').forEach(item => {
                item.classList.toggle('hidden', item.dataset.group !== group);
            });
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            document.querySelectorAll('.total').forEach(t => t.classList.remove('active'));
            document.getElementById('total-' + group).classList.add('active');
        }
        
        function showAll() {
            currentFilter = null;
            document.querySelectorAll('.workout-item').forEach(item => item.classList.remove('hidden'));
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelector('.filter-btn').classList.add('active');
            document.querySelectorAll('.total').forEach(t => t.classList.remove('active'));
        }
        
        function openModal(workoutId) {
            const modal = document.getElementById('modal-' + workoutId);
            if (modal) {
                modal.classList.add('active');
                document.body.style.overflow = 'hidden';
            }
        }
        
        function closeModal(workoutId) {
            const modal = document.getElementById('modal-' + workoutId);
            if (modal) {
                modal.classList.remove('active');
                document.body.style.overflow = 'auto';
            }
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            if (event.target.classList.contains('modal')) {
                event.target.classList.remove('active');
                document.body.style.overflow = 'auto';
            }
        }
        
        // Close modal with Escape key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                document.querySelectorAll('.modal.active').forEach(modal => {
                    modal.classList.remove('active');
                    document.body.style.overflow = 'auto';
                });
            }
        });
    </script>"""

MODAL_BLOCK = """    <div id="modal-easy-run" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal('easy-run')">&times;</span>
            <h2>Easy Run</h2>
            
            <div class="modal-section">
                <h3>Overview</h3>
                <p>Conversational pace run for aerobic base building. Should be able to speak in complete sentences.</p>
            </div>
            <div class="modal-section">
                <h3>Key Points</h3>
                <ul class="key-points">
                    <li>• True easy effort - don't push the pace</li>
<li>• This builds your aerobic engine</li>
                </ul>
            </div>
            <div class="modal-section"><h3>Pace</h3><p>E pace from chart, conversational</p></div>
            <div class="modal-section"><h3>Duration</h3><p>varies</p></div>
        </div>
    </div>"""


# ---------------------------------------------------------------------------
# Markdown parsing
# ---------------------------------------------------------------------------

def parse_cell(raw):
    """Split a markdown table cell into (bold_label, italic_qty, plain_text)."""
    cell = raw.strip()
    bold_m = re.search(r"\*\*(.+?)\*\*", cell)
    label = bold_m.group(1).strip() if bold_m else None
    remainder = cell[:bold_m.start()] + cell[bold_m.end():] if bold_m else cell
    ital_m = re.search(r"\*([^*]+)\*", remainder)
    qty = ital_m.group(1).strip() if ital_m else None
    plain = remainder
    if ital_m:
        plain = remainder[:ital_m.start()] + remainder[ital_m.end():]
    plain = plain.strip()
    return label, qty, plain


def extract_miles(qty_text):
    if not qty_text:
        return None
    m = re.match(r"([\d.]+)\s*mi", qty_text)
    return float(m.group(1)) if m else None


def classify(label, cell_raw):
    if cell_raw.strip() == "**REST**" or (label and label.strip().upper() == "REST"):
        return "rest"
    if not label:
        return "easy"
    ll = label.lower()
    if "long run" in ll:
        return "long_run"
    if "rest" in ll:
        return "rest"
    if "easy" in ll:
        return "easy"
    if any(k in ll for k in RACE_KEYWORDS):
        return "race"
    if any(k in ll for k in QUALITY_KEYWORDS) or any(p.search(ll) for p in QUALITY_PATTERNS):
        return "quality"
    return "easy"


def parse_markdown(md_text):
    """Return a list of week dicts: {num, date_range, title, groups:[...], days: {abbr: {group: cell}}}"""
    # The "— Title" suffix after the header is optional: some weeks (e.g. a
    # source file's Week 14) only have "## **WEEK N: DATE**" with no title,
    # so that part of the header must not be required or the whole week
    # silently fails to match and gets skipped.
    week_re = re.compile(
        r"## \*\*WEEK (\d+): ([^*]+)\*\*[ \t]*(?:—[ \t]*([^\n]+))?\n(.*?)"
        r"(?=\n## \*\*WEEK \d+:|\n## \*\*MILEAGE SUMMARY|\Z)",
        re.S,
    )
    weeks = []
    for m in week_re.finditer(md_text):
        num = int(m.group(1))
        date_range = m.group(2).strip()
        title = (m.group(3) or "").strip()
        body = m.group(4)

        lines = body.splitlines()
        header_idx = next((i for i, l in enumerate(lines) if l.strip().startswith("| Day")), None)
        if header_idx is None:
            print(f"WARNING: no table found for Week {num}", file=sys.stderr)
            continue

        table_lines = []
        for l in lines[header_idx:]:
            if l.strip().startswith("|"):
                table_lines.append(l.strip())
            else:
                break

        header_cells = [c.strip() for c in table_lines[0].strip("|").split("|")]
        group_cells = header_cells[1:]
        groups = []
        for gc in group_cells:
            gm = re.match(r"(\w+)\s*\(([\d.]+)\s*mi\)", gc.strip())
            if gm:
                groups.append({"name": gm.group(1), "total": float(gm.group(2))})
            else:
                groups.append({"name": gc.strip(), "total": None})

        # table_lines[1] is the separator row (":---|:---")
        data_lines = table_lines[2:]

        days = {}
        for dl in data_lines:
            cells = [c.strip() for c in dl.strip("|").split("|")]
            day_abbr = re.sub(r"\*\*", "", cells[0]).strip()
            if day_abbr not in DAY_ORDER:
                continue
            group_vals = cells[1:]
            if len(group_vals) < len(groups):
                print(
                    f"WARNING: Week {num} {day_abbr} row has {len(group_vals)} "
                    f"cells but {len(groups)} groups expected - padding with last cell",
                    file=sys.stderr,
                )
                while len(group_vals) < len(groups):
                    group_vals.append(group_vals[-1] if group_vals else "**REST**")
            days[day_abbr] = {groups[i]["name"]: group_vals[i] for i in range(len(groups))}

        weeks.append({
            "num": num,
            "date_range": date_range,
            "title": title,
            "groups": groups,
            "days": days,
        })
    return weeks


# ---------------------------------------------------------------------------
# Workout classification -> render data
# ---------------------------------------------------------------------------

def ref_link(url, text):
    return f'<a href="{url}" target="_blank" class="ref-link">{text}</a>'


def render_items(items):
    """items: list of (url_or_None, text) -> joined HTML string with ', ' separators."""
    parts = []
    for url, text in items:
        parts.append(ref_link(url, text) if url else text)
    return ", ".join(parts)


def build_workout(day_abbr, group_name, cell_raw):
    label, qty, plain = parse_cell(cell_raw)
    wtype = classify(label, cell_raw)
    miles = extract_miles(qty)

    if wtype == "rest":
        return {
            "type": "rest", "desc": "REST", "pre": None, "post": None,
            "miles": None, "info_icon": False,
        }

    if wtype == "easy":
        desc = f"{miles:g}mi easy" if miles is not None else (plain or qty or "Easy")
        if day_abbr == "Mon":
            pre = [(REF_FOOT, "Foot Drills"), (REF_WARMUP, "Dynamics"), (None, "Buildups")]
        else:
            pre = [(REF_WARMUP, "WU"), (REF_WARMUP, "Dynamics"), (None, "stride progression")]
        post = [(REF_WARMUP, "Strides"), (REF_MOBILITY, "Mobility/Strength A")]
        return {
            "type": "easy", "desc": desc, "pre": render_items(pre), "post": render_items(post),
            "miles": miles, "info_icon": True,
        }

    if wtype == "long_run":
        desc = f"Long Run {miles:g}mi" if miles is not None else (label or "Long Run")
        pre = [(REF_WARMUP, "Awesomizer"), (REF_WARMUP, "Lunge Matrix")]
        post = [(REF_WARMUP, "Strides"), (REF_MOBILITY, "Mobility A"), (None, "24s")]
        return {
            "type": "long_run", "desc": desc, "pre": render_items(pre), "post": render_items(post),
            "miles": miles, "info_icon": False,
        }

    if wtype == "race":
        desc = label or "Race"
        pre = [(REF_WARMUP, "Race Day WU")]
        post = [(REF_WARMUP, "Post Race")]
        return {
            "type": "race", "desc": desc, "pre": render_items(pre), "post": render_items(post),
            "miles": miles, "info_icon": False,
        }

    # quality
    desc = label or plain or qty or "Workout"
    pre = [(REF_WARMUP, "WU"), (REF_WARMUP, "Dynamics"), (None, "stride progression")]
    if re.search(r"@r\b", (label or "").lower()) or "200m" in (label or "").lower():
        post = [(REF_WARMUP, "Strides"), (REF_MOBILITY, "Mobility/Strength A")]
    else:
        post = [(REF_MOBILITY, "Mobility/Strength B")]
    return {
        "type": "quality", "desc": desc, "pre": render_items(pre), "post": render_items(post),
        "miles": miles, "info_icon": False,
    }


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

def render_workout_item(group_name, wo):
    cls = GROUP_CLASS.get(group_name, group_name.lower())
    if wo["type"] == "rest":
        return f'''                    <div class="workout-item {cls}" data-group="{group_name}">
                        <div class="group-badge {cls}">{group_name}</div>
                        <div class="workout-details">
                            <div class="workout-desc"><span>REST</span></div>
                        </div>
                        <div class="workout-miles">&mdash;</div>
                    </div>'''

    miles_txt = f'{wo["miles"]:.1f} mi' if wo["miles"] is not None else "&mdash;"
    info_icon_html = (
        '<span class="info-icon" onclick="openModal(\'easy-run\')" '
        'title="Click for workout details">i</span>'
        if wo["info_icon"] else ""
    )
    pre_html = f'<div class="workout-pre">{wo["pre"]}</div>' if wo["pre"] else ""
    post_html = f'<div class="workout-post">{wo["post"]}</div>' if wo["post"] else ""

    return f'''                    <div class="workout-item {cls}" data-group="{group_name}">
                        <div class="group-badge {cls}">{group_name}</div>
                        <div class="workout-details">
                            {pre_html}
                            <div class="workout-desc">
                                <span>{wo["desc"]}</span>
                                {info_icon_html}
                            </div>
                            {post_html}
                        </div>
                        <div class="workout-miles">{miles_txt}</div>
                    </div>'''


def render_day(day_abbr, day_cells):
    workouts = {}
    has_quality = False
    for group_name, cell_raw in day_cells.items():
        wo = build_workout(day_abbr, group_name, cell_raw)
        workouts[group_name] = wo
        if wo["type"] == "quality":
            has_quality = True

    groups_btn = (
        ' <a href="athlete_groups.html" target="_blank" class="groups-btn" '
        'title="View training groups">👥 Groups</a>' if has_quality else ""
    )

    ordered_groups = [g for g in GROUP_DISPLAY_ORDER if g in workouts]
    items_html = "\n".join(
        render_workout_item(g, workouts[g]) for g in ordered_groups
    )

    return f'''    <div class="day">
        <div class="day-header">
            <span>{DAY_FULL[day_abbr]}</span>{groups_btn}
        </div>
        <div class="day-content">
                <div class="section">
                    <div class="section-label">WORKOUT</div>
{items_html}
                </div>
        </div>
    </div>'''


def render_week_html(week):
    groups = [g["name"] for g in week["groups"]]
    ordered_groups = [g for g in GROUP_DISPLAY_ORDER if g in groups]
    totals_map = {g["name"]: g["total"] for g in week["groups"]}

    totals_html = "\n".join(
        f'''        <div class="total {GROUP_CLASS.get(g, g.lower())}" onclick="filterGroup('{g}')" id="total-{g}">
            <div class="total-label">{g}</div>
            <div class="total-miles">{totals_map[g]:g}</div>
        </div>''' for g in ordered_groups
    )

    filters_html = '        <button class="filter-btn active" onclick="showAll()">Show All</button>\n' + "\n".join(
        f'        <button class="filter-btn" onclick="filterGroup(\'{g}\')">{g}</button>' for g in ordered_groups
    )

    days_html = "\n".join(
        render_day(d, week["days"][d]) for d in DAY_ORDER if d in week["days"]
    )

    title = f'🏃 STX Training - Week {week["num"]} — {week["date_range"].title()}'

    return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>STX Training Week {week["num"]}</title>
{STYLE_BLOCK}
</head>
<body>
    <a class="back-btn" href="index.html">← Schedule</a>
    <h1>{title}</h1>
    {f'<div class="subtitle"><strong>{week["title"]}</strong></div>' if week["title"] else ''}

    <div class="totals">
{totals_html}
    </div>

    <div class="filters">
{filters_html}
    </div>

{days_html}
{MODAL_BLOCK}

{SCRIPT_BLOCK}
</body>
</html>
'''


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_week_selection(text, available_nums):
    """Parse input like '5', '5-7', or '5,9,14-16' into a set of week numbers."""
    wanted = set()
    for token in text.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            start_s, end_s = token.split("-", 1)
            wanted.update(range(int(start_s.strip()), int(end_s.strip()) + 1))
        else:
            wanted.add(int(token))
    return wanted


def prompt_for_weeks(available_nums):
    lo, hi = min(available_nums), max(available_nums)
    coverage = format_week_ranges(available_nums)
    if coverage == f"{lo}-{hi}":
        print(f"\nWeeks available in the markdown file: {coverage}")
    else:
        print(f"\nWeeks available in the markdown file: {coverage} "
              f"(not a full {lo}-{hi} range - some week numbers are missing)")
    while True:
        raw = input(
            f"Which week(s) do you want to generate? "
            f"(e.g. 5, 5-7, 5,9,14-16, or 'all') [{lo}-{hi}]: "
        ).strip()
        if not raw:
            print("Please enter at least one week number.")
            continue
        if raw.lower() == "all":
            return set(available_nums)
        try:
            wanted = parse_week_selection(raw, available_nums)
        except ValueError:
            print(f"Couldn't parse '{raw}' - use a number, a range like 5-7, or a comma list.")
            continue
        if not wanted:
            print("Please enter at least one week number.")
            continue
        missing = sorted(wanted - available_nums)
        if missing:
            print(f"Week(s) {missing} aren't in this markdown file "
                  f"(it only has: {coverage}). Try again, or double-check you "
                  f"picked the right schedule file.")
            continue
        return wanted


def find_by_glob(patterns, cwd):
    """Try each glob pattern in order and return the results of the first
    pattern that matches anything (so a broad fallback pattern doesn't pull
    in unrelated .md files once a more specific pattern already matched)."""
    import glob as globmod
    for pat in patterns:
        found = globmod.glob(os.path.join(cwd, pat))
        if found:
            # de-dupe while preserving order
            seen = set()
            ordered = []
            for f in found:
                if f not in seen:
                    seen.add(f)
                    ordered.append(f)
            return ordered
    return []


def describe_md_weeks(path):
    """Peek at a candidate schedule file and summarize which week numbers
    it actually contains, so ambiguous multi-file folders can be told apart."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
    except OSError:
        return "unreadable"
    nums = sorted(int(n) for n in re.findall(r"## \*\*WEEK (\d+):", text))
    if not nums:
        return "no 'WEEK n' sections found - probably not the schedule file"
    return f"{len(nums)} week(s) found: {format_week_ranges(nums)}"


def format_week_ranges(nums):
    """[1,2,3,5,6,9] -> '1-3, 5-6, 9'"""
    nums = sorted(set(nums))
    ranges = []
    start = prev = nums[0]
    for n in nums[1:]:
        if n == prev + 1:
            prev = n
            continue
        ranges.append(f"{start}-{prev}" if start != prev else f"{start}")
        start = prev = n
    ranges.append(f"{start}-{prev}" if start != prev else f"{start}")
    return ", ".join(ranges)


def resolve_path(argval, label, patterns, cwd, describe_fn=None):
    """Return a filesystem path for a required input, auto-detecting it in
    `cwd` via glob `patterns` when not passed on the command line, and
    falling back to an interactive prompt. If `describe_fn` is given, its
    output is shown next to each candidate to help disambiguate."""
    if argval:
        return argval

    candidates = find_by_glob(patterns, cwd)

    if len(candidates) == 1 and not describe_fn:
        print(f"Using {label}: {candidates[0]}")
        return candidates[0]

    if len(candidates) >= 1:
        if len(candidates) == 1:
            print(f"\nFound one possible {label} file:")
        else:
            print(f"\nFound multiple possible {label} files:")
        for i, c in enumerate(candidates, 1):
            extra = f"  -> {describe_fn(c)}" if describe_fn else ""
            print(f"  {i}) {os.path.basename(c)}{extra}")
        if len(candidates) == 1:
            raw = input(f"Use this file as the {label}? [Y/n] (or type a different path): ").strip()
            if raw == "" or raw.lower() in ("y", "yes"):
                return candidates[0]
            if os.path.isfile(raw):
                return raw
        while True:
            raw = input(f"Which one is the {label}? [1-{len(candidates)}] "
                        f"(or type a path): ").strip()
            if raw.isdigit() and 1 <= int(raw) <= len(candidates):
                return candidates[int(raw) - 1]
            if os.path.isfile(raw):
                return raw
            print("Please enter a valid number or file path.")

    while True:
        raw = input(f"Couldn't find a {label} automatically - enter its path: ").strip()
        if os.path.isfile(raw):
            return raw
        print(f"'{raw}' isn't a file - try again.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", default=None,
                     help="Path to the season schedule markdown file "
                          "(auto-detected in the current folder if omitted)")
    ap.add_argument("--outdir", default=None,
                     help="Directory to write weekN.html files into (defaults to the "
                          "current folder, so links to the other reference pages keep working)")
    ap.add_argument("--weeks", default=None,
                     help="Comma list of specific week numbers to generate, e.g. 1,2,3 "
                          "(overrides --start/--end)")
    ap.add_argument("--start", type=int, default=None, help="First week number to generate")
    ap.add_argument("--end", type=int, default=None,
                     help="Last week number to generate (defaults to the last week in the file "
                          "if --start is given without --end)")
    ap.add_argument("--force", action="store_true",
                     help="Overwrite existing weekN.html files without asking")
    ap.add_argument("--yes", "-y", action="store_true",
                     help="Skip the interactive range prompt and generate every week in the file "
                          "(same as the old default behavior)")
    args = ap.parse_args()

    cwd = os.getcwd()
    md_path = resolve_path(
        args.md, "schedule markdown",
        ["*Complete_Schedule*.md", "*Schedule*Weeks*.md", "*Schedule*.md", "*schedule*.md", "*.md"],
        cwd, describe_fn=describe_md_weeks,
    )
    outdir = args.outdir or cwd
    if not args.outdir:
        print(f"Using output folder: {outdir}")

    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    all_weeks = parse_markdown(md_text)
    available_nums = {w["num"] for w in all_weeks}

    # Figure out which week numbers to generate, in priority order:
    # --weeks > --start/--end > interactive prompt > --yes (all weeks)
    if args.weeks:
        wanted = {int(w) for w in args.weeks.split(",")}
    elif args.start is not None:
        end = args.end if args.end is not None else max(available_nums)
        wanted = set(range(args.start, end + 1))
    elif args.yes:
        wanted = available_nums
    else:
        wanted = prompt_for_weeks(available_nums)

    weeks = [w for w in all_weeks if w["num"] in wanted]
    missing = sorted(wanted - available_nums)
    if missing:
        print(f"WARNING: these requested weeks aren't in the markdown file and will be skipped: {missing}",
              file=sys.stderr)

    os.makedirs(outdir, exist_ok=True)

    written, skipped = 0, 0
    for week in sorted(weeks, key=lambda w: w["num"]):
        out_path = os.path.join(outdir, f"week{week['num']}.html")

        if os.path.exists(out_path) and not args.force:
            answer = input(f"{out_path} already exists - overwrite? [y/N]: ").strip().lower()
            if answer not in ("y", "yes"):
                print(f"Skipped {out_path}")
                skipped += 1
                continue

        html = render_week_html(week)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Wrote {out_path}")
        written += 1

    print(f"\nDone: {written} week page(s) written, {skipped} skipped, in {outdir}")


if __name__ == "__main__":
    main()
