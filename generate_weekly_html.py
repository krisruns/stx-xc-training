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
    5,9,14-16, or 'all' - and if any of the target weekN.html files already
    exist, it lists them and asks once whether to overwrite all of them
    (rather than asking file-by-file).

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
                          palatine, state, champions, nationals, hoka)
      Quality/Workout -> bold label with rep/pace patterns
                          (fartlek, progression, hill repeats, NxM, @T/@I/@R,
                          distances like 800m/1000m/1200m/1600m/200m/300m/400m)
      Easy            -> everything else (default)
      TBD             -> label is/contains "TBD" (e.g. **Workout TBD**). Shown as a
                          placeholder row with no routines. Add *Nmi* if you know the
                          mileage; if not, the week total that includes it gets a "+".
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
  - Varsity vs JV workouts (optional, per week). The main table in a week is
    the Varsity / default schedule. When JV does something different on a
    day, add a second table directly under the main one, introduced by a
    line that starts with "#### JV Overrides" (or "**JV Overrides**"):

        #### JV Overrides

        | Day | Blue (27 mi) | White (33 mi) | Green (39 mi) | Gold (43.5 mi) |
        |:----|:---|:---|:---|:---|
        | **Tue** | Easy *3.5mi* | Easy *4.5mi* | Easy *6mi* | Easy *6.5mi* |
        | **Wed** | **Champions 2** *5mi* | **Champions 2** *6mi* | | |

    Same columns as the main table. Only list the days that differ, and
    leave a cell blank (or "-" / "same") when that group's JV athletes do
    what the main table says. Header totals on the override table are
    optional; if present they are checked against the JV weekly total
    (main cells, with overrides swapped in). On the page, any group/day with
    an override shows a VARSITY row and a JV row, a Varsity/JV filter
    appears, and each mileage total gets a "JV nn" line underneath.
    Weeks with no override table render exactly as before.
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

# Minutes-per-mile easy pace used to *estimate* mileage for cells that only
# give a duration (e.g. "Easy *35min + 6x100m strides*") with no explicit
# "Xmi". Edit these if the group paces change.
PACE_MIN_PER_MILE = {"Gold": 7.5, "Green": 8.0, "White": 8.5, "Blue": 9.0}

# Which modal (defined in MODAL_BLOCK below) each workout type's info icon
# opens. "rest" has no icon/modal. Edit MODAL_BLOCK's content directly to
# change what a modal says; edit this dict if you rename/add a modal.
MODAL_KEY_BY_TYPE = {
    "easy": "easy-run",
    "long_run": "long-run",
    "race": "race-day",
    # "quality" isn't listed here - it's split further into subtypes
    # (threshold/interval/repetition/fartlek/progression/hill repeats)
    # by classify_quality_subtype() / MODAL_KEY_BY_QUALITY_SUBTYPE below.
}

# Which modal a "quality" workout's info icon opens depends on which kind
# of quality session it is - see classify_quality_subtype(). Anything that
# doesn't match a specific subtype falls back to the generic
# "quality-workout" modal.
MODAL_KEY_BY_QUALITY_SUBTYPE = {
    "threshold": "threshold",
    "interval": "interval",
    "repetition": "repetition",
    "fartlek": "fartlek",
    "progression": "progression",
    "hill_repeats": "hill-repeats",
    "quality": "quality-workout",
}

RACE_KEYWORDS = [
    "race", "trial", "invitational", "classic", "showcase", "regional",
    "championships", "meet", "tiger run", "alumni run", "run for the gold",
    "haunted woods", "palatine", "state", "champions", "nationals", "hoka",
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
        
        /* Varsity / JV split */
        .squad-filters { margin: -8px 0 20px 0; }
        .squad-btn { padding: 6px 14px; margin: 0 5px 5px 0; border: 2px solid #1E3A8A; background: white; color: #1E3A8A; border-radius: 16px; cursor: pointer; font-size: 0.85rem; transition: all 0.2s; }
        .squad-btn:hover, .squad-btn.active { background: #1E3A8A; color: white; }
        .total-jv { font-size: 0.85rem; font-weight: 600; margin-top: 4px; opacity: 0.85; }
        .jv-note { background: #E6F0FF; border: 1px solid #4169E1; border-radius: 6px; padding: 10px 15px; margin: 15px 0; font-size: 0.9rem; color: #1E3A8A; }
        .squad-tag { display: block; width: fit-content; margin-top: 3px; padding: 1px 7px; border-radius: 8px; font-size: 0.62rem; letter-spacing: 0.5px; color: white; }
        .squad-tag.varsity { background: #2c5530; }
        .squad-tag.jv { background: #1E3A8A; }
        .workout-item.jv-row { border-left-style: dashed; }

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
        let currentFilter = null;   // selected group, or null for all groups
        let currentSquad = 'all';   // 'all' | 'varsity' | 'jv'

        function applyFilters() {
            document.querySelectorAll('.workout-item').forEach(item => {
                const groupOk = currentFilter === null || item.dataset.group === currentFilter;
                const squad = item.dataset.squad || 'all';
                const squadOk = currentSquad === 'all' || squad === 'all' || squad === currentSquad;
                item.classList.toggle('hidden', !(groupOk && squadOk));
            });
            document.querySelectorAll('.filter-btn').forEach(btn => {
                btn.classList.toggle('active', (btn.dataset.group || null) === currentFilter);
            });
            document.querySelectorAll('.squad-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.squad === currentSquad);
            });
            document.querySelectorAll('.total').forEach(t => {
                t.classList.toggle('active', currentFilter !== null && t.id === 'total-' + currentFilter);
            });
        }

        function filterGroup(group) {
            currentFilter = group;
            applyFilters();
        }

        function filterSquad(squad) {
            currentSquad = squad;
            applyFilters();
        }

        function showAll() {
            currentFilter = null;
            currentSquad = 'all';
            applyFilters();
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
    </div>
    <div id="modal-long-run" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal('long-run')">&times;</span>
            <h2>Long Run</h2>

            <div class="modal-section">
                <h3>Overview</h3>
                <p>Extended aerobic run to build endurance and mileage base - the longest run of the week.</p>
            </div>
            <div class="modal-section">
                <h3>Key Points</h3>
                <ul class="key-points">
                    <li>• Steady, controlled effort throughout</li>
<li>• Fuel/hydrate as needed for runs over ~60 minutes</li>
                </ul>
            </div>
            <div class="modal-section"><h3>Pace</h3><p>Easy to Marathon pace from chart</p></div>
            <div class="modal-section"><h3>Duration</h3><p>varies</p></div>
        </div>
    </div>
    <div id="modal-threshold" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal('threshold')">&times;</span>
            <h2>Threshold</h2>

            <div class="modal-section">
                <h3>Overview</h3>
                <p>Steady, prolonged/tempo runs (sometimes called cruise intervals), comfortably hard - roughly 15K to half-marathon race effort.</p>
            </div>
            <div class="modal-section">
                <h3>Key Points</h3>
                <ul class="key-points">
                    <li>• Intensity: ~83-88% max VO2, ~88-92% max heart rate</li>
<li>• Purpose: builds speed endurance</li>
                </ul>
            </div>
            <div class="modal-section"><h3>Pace</h3><p>@T - Threshold pace from chart</p></div>
            <div class="modal-section"><h3>Duration</h3><p>varies</p></div>
        </div>
    </div>
    <div id="modal-interval" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal('interval')">&times;</span>
            <h2>Interval</h2>

            <div class="modal-section">
                <h3>Overview</h3>
                <p>maxVO2 intervals - "high intensity" but not all-out, sustainable for 10-12 minutes in a serious race. Roughly 3K-5K race effort.</p>
            </div>
            <div class="modal-section">
                <h3>Key Points</h3>
                <ul class="key-points">
                    <li>• Usually 3-5 min per rep (800m-1k), with equal recovery</li>
<li>• Purpose: stress aerobic power (maxVO2) - takes ~2 min to hit maxVO2; after ~5 min the body shifts anaerobic</li>
                </ul>
            </div>
            <div class="modal-section"><h3>Pace</h3><p>@I - Interval pace from chart (~95-100% max HR), or @RP - current race pace</p></div>
            <div class="modal-section"><h3>Duration</h3><p>varies</p></div>
        </div>
    </div>
    <div id="modal-repetition" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal('repetition')">&times;</span>
            <h2>Repetition</h2>

            <div class="modal-section">
                <h3>Overview</h3>
                <p>Race (and faster) pace reps and strides - mile pace or faster, for neuromuscular power.</p>
            </div>
            <div class="modal-section">
                <h3>Key Points</h3>
                <ul class="key-points">
                    <li>• FAST but not HARD - rest should allow full recovery between reps</li>
<li>• Purpose: improve speed, economy, and efficiency (running relaxed)</li>
                </ul>
            </div>
            <div class="modal-section"><h3>Pace</h3><p>@R - Repetition pace from chart</p></div>
            <div class="modal-section"><h3>Duration</h3><p>varies</p></div>
        </div>
    </div>
    <div id="modal-fartlek" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal('fartlek')">&times;</span>
            <h2>Fartlek</h2>

            <div class="modal-section">
                <h3>Overview</h3>
                <p>"Speed play" - controlled surges mixed into a continuous run, alternating "on" and "steady" segments.</p>
            </div>
            <div class="modal-section">
                <h3>Key Points</h3>
                <ul class="key-points">
                    <li>• "on" = controlled surge at roughly 5K-10K effort</li>
<li>• "steady" = comfortable recovery pace (not walking)</li>
                </ul>
            </div>
            <div class="modal-section"><h3>Pace</h3><p>Effort-based, per the on/steady cues above</p></div>
            <div class="modal-section"><h3>Duration</h3><p>varies</p></div>
        </div>
    </div>
    <div id="modal-progression" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal('progression')">&times;</span>
            <h2>Progression</h2>

            <div class="modal-section">
                <h3>Overview</h3>
                <p>A continuous run that gradually shifts from easy to faster effort over set time blocks.</p>
            </div>
            <div class="modal-section">
                <h3>Key Points</h3>
                <ul class="key-points">
                    <li>• All groups run the same time structure, at their own appropriate effort level</li>
<li>• Pace by feel, not by watch</li>
                </ul>
            </div>
            <div class="modal-section"><h3>Pace</h3><p>Effort-based - progresses from easy to faster</p></div>
            <div class="modal-section"><h3>Duration</h3><p>varies</p></div>
        </div>
    </div>
    <div id="modal-hill-repeats" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal('hill-repeats')">&times;</span>
            <h2>Hill Repeats</h2>

            <div class="modal-section">
                <h3>Overview</h3>
                <p>Repeated hard efforts up a hill, with a walk/jog recovery back down between reps.</p>
            </div>
            <div class="modal-section">
                <h3>Key Points</h3>
                <ul class="key-points">
                    <li>• Strong arm drive and knee lift - don't overstride</li>
<li>• Recovery is the walk/jog back down the hill</li>
                </ul>
            </div>
            <div class="modal-section"><h3>Pace</h3><p>Hard, controlled effort - not a sprint</p></div>
            <div class="modal-section"><h3>Duration</h3><p>varies</p></div>
        </div>
    </div>
    <div id="modal-quality-workout" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal('quality-workout')">&times;</span>
            <h2>Quality Workout</h2>

            <div class="modal-section">
                <h3>Overview</h3>
                <p>Structured effort work to build speed, threshold, or race-specific fitness.</p>
            </div>
            <div class="modal-section">
                <h3>Key Points</h3>
                <ul class="key-points">
                    <li>• Warm up thoroughly before starting</li>
<li>• Hit the prescribed effort/pace for each rep, with full or prescribed recovery between</li>
                </ul>
            </div>
            <div class="modal-section"><h3>Pace</h3><p>Interval / Threshold / Repetition pace from chart, per the workout</p></div>
            <div class="modal-section"><h3>Duration</h3><p>varies</p></div>
        </div>
    </div>
    <div id="modal-race-day" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal('race-day')">&times;</span>
            <h2>Race Day</h2>

            <div class="modal-section">
                <h3>Overview</h3>
                <p>Competition effort - execute the race plan and compete.</p>
            </div>
            <div class="modal-section">
                <h3>Key Points</h3>
                <ul class="key-points">
                    <li>• Follow the race-day warmup routine</li>
<li>• Start controlled, finish strong</li>
                </ul>
            </div>
            <div class="modal-section"><h3>Pace</h3><p>Race effort, per current fitness</p></div>
            <div class="modal-section"><h3>Duration</h3><p>Race distance</p></div>
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


def extract_miles_minutes(qty_text):
    """Parse a cell's italic quantity text into (miles, minutes_text, leftover).
    Handles plain '4mi', and combined mile/time entries like '3mi/20min'
    or '4mi/25-30min' (minutes_text keeps the original '25-30' form).
    'leftover' is whatever trailing text follows the quantity, e.g. for
    '4mi + strides' that's 'strides'.
    Uses \\b after 'mi' so a time-only value like '30min shakeout' isn't
    misread as 30 miles (since 'min' starts with 'mi')."""
    if not qty_text:
        return None, None, ""
    m = re.match(r"([\d.]+)\s*mi\b(?:\s*/\s*([\d]+(?:\s*-\s*[\d]+)?)\s*min)?", qty_text)
    if not m:
        return None, None, ""
    miles = float(m.group(1))
    minutes = m.group(2).replace(" ", "") if m.group(2) else None
    leftover = qty_text[m.end():].strip()
    return miles, minutes, leftover


def format_dist(miles, minutes):
    """(6.0, None) -> '6mi'   (3.0, '20-25') -> '3mi / 20-25min'"""
    if miles is None:
        return None
    s = f"{miles:g}mi"
    if minutes:
        s += f" / {minutes}min"
    return s


def extract_minutes_only(qty_text):
    """For cells with a duration but no explicit mileage, e.g.
    '35min + 6x100m strides' or '20-25min', return
    (pace_minutes, duration_text, leftover):
      pace_minutes  - the (midpoint) minutes value, used for the mileage estimate
      duration_text - the original duration text as written, e.g. '35min' or '20-25min'
      leftover      - whatever trailing text follows, e.g. '+ 6x100m strides'
    Returns (None, None, "") if there's no leading 'Nmin'/'N-Mmin' to find."""
    if not qty_text:
        return None, None, ""
    m = re.match(r"([\d.]+)(?:\s*-\s*([\d.]+))?\s*min\b", qty_text.strip())
    if not m:
        return None, None, ""
    lo = float(m.group(1))
    hi = float(m.group(2)) if m.group(2) else lo
    pace_minutes = (lo + hi) / 2
    duration_text = qty_text.strip()[:m.end()]
    leftover = qty_text.strip()[m.end():].strip()
    return pace_minutes, duration_text, leftover


def estimate_miles_from_minutes(minutes, group_name):
    pace = PACE_MIN_PER_MILE.get(group_name)
    if pace is None or minutes is None:
        return None
    return round(minutes / pace, 1)


def is_rest_cell(cell_raw):
    """True for a cell that's just REST in any markdown decoration:
    '**REST**', '*Rest*', 'REST', etc."""
    cleaned = re.sub(r"\*+", "", cell_raw).strip()
    return cleaned.lower() == "rest"


def classify(label, cell_raw):
    if is_rest_cell(cell_raw) or (label and label.strip().upper() == "REST"):
        return "rest"
    if re.sub(r"\*+", "", cell_raw).strip().lower() == "tbd" or (
            label and re.search(r"\btbd\b", label, re.I)):
        return "tbd"
    if not label:
        return "easy"
    ll = label.lower()
    if "long run" in ll:
        return "long_run"
    if "rest" in ll:
        return "rest"
    if any(k in ll for k in RACE_KEYWORDS):
        return "race"
    # Check quality markers before the plain "easy" substring check below -
    # a Progression label like "5min easy / 15min steady / 5min easy"
    # contains the word "easy" but is a quality workout, not an easy run.
    if any(k in ll for k in QUALITY_KEYWORDS) or any(p.search(ll) for p in QUALITY_PATTERNS):
        return "quality"
    if "easy" in ll:
        return "easy"
    return "easy"


def classify_quality_subtype(label):
    """For a workout already classified as "quality", figure out which
    kind it is (threshold/interval/repetition/fartlek/progression/hill
    repeats) so it can get its own info-icon modal. Checked in this order
    since a single label can contain more than one marker - e.g.
    "2mi@T + 4x200m@R" is a Threshold run with strides tacked on the end,
    so @T (the main workout) wins over the trailing @R strides."""
    if not label:
        return "quality"
    ll = label.lower()
    # "Nx(1:00 on/4:00 steady)" style reps, with or without a "Fartlek"
    # prefix - some weeks just number the reps without repeating the word.
    if "fartlek" in ll or re.search(r"\bon\s*/\s*\d+:\d+\s*(off|steady)\b", ll):
        return "fartlek"
    if "progression" in ll:
        return "progression"
    if "hill" in ll:
        return "hill_repeats"
    if re.search(r"@t\b", ll):
        return "threshold"
    if re.search(r"@i\b", ll) or re.search(r"@rp\b", ll):
        return "interval"
    if re.search(r"@r\b", ll):
        return "repetition"
    return "quality"


# A line like "#### JV Overrides" or "**JV Overrides**" directly above a
# table marks it as the JV override table for that week.
JV_HEADING_RE = re.compile(r"^(?:#{2,6}\s*|\*\*)\s*(?:JV|Junior\s+Varsity)\b", re.I)
# Cells that mean "JV does the same thing as the main table".
JV_BLANK_CELL_RE = re.compile(r"^\s*(?:|[-\u2013\u2014]+|=|same)\s*$", re.I)


def _norm_cell(text):
    return re.sub(r"\s+", " ", text.strip().lower())


def parse_group_header(header_line):
    """'| Day | Blue (25 mi) | Gold (39 mi) |' -> [{name, total}, ...].
    The '(NN mi)' total is optional (used for JV override tables)."""
    header_cells = [c.strip() for c in header_line.strip("|").split("|")]
    groups = []
    for gc in header_cells[1:]:
        gm = re.match(r"(\w+)\s*\(([\d.]+)\s*mi\)", gc.strip())
        if gm:
            groups.append({"name": gm.group(1), "total": float(gm.group(2))})
        else:
            groups.append({"name": gc.strip(), "total": None})
    return groups


def find_tables(lines):
    """Every markdown table whose header row starts with '| Day', as a list of
    (preceding_line, table_lines). preceding_line is the nearest non-blank
    line above the table ('' if none) - used to spot the '#### JV Overrides'
    marker."""
    tables = []
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("| Day"):
            prev = ""
            for j in range(i - 1, -1, -1):
                if lines[j].strip():
                    prev = lines[j].strip()
                    break
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i].strip())
                i += 1
            tables.append((prev, block))
        else:
            i += 1
    return tables


def parse_table_rows(data_lines, groups, week_num, pad_missing):
    """Data rows -> {day_abbr: {group_name: raw_cell}}.
    pad_missing=True (main table): a short row reuses its last cell and warns.
    pad_missing=False (JV table): a short row just gets blank cells."""
    days = {}
    for dl in data_lines:
        cells = [c.strip() for c in dl.strip("|").split("|")]
        day_abbr = re.sub(r"\*\*", "", cells[0]).strip()
        if day_abbr not in DAY_ORDER:
            continue
        group_vals = cells[1:]
        if len(group_vals) < len(groups):
            if pad_missing:
                print(
                    f"WARNING: Week {week_num} {day_abbr} row has {len(group_vals)} "
                    f"cells but {len(groups)} groups expected - padding with last cell",
                    file=sys.stderr,
                )
                while len(group_vals) < len(groups):
                    group_vals.append(group_vals[-1] if group_vals else "**REST**")
            else:
                group_vals = group_vals + [""] * (len(groups) - len(group_vals))
        days[day_abbr] = {groups[i]["name"]: group_vals[i] for i in range(len(groups))}
    return days


def parse_jv_overrides(table_lines, groups, days, week_num):
    """Parse a '#### JV Overrides' table. Returns (jv_groups, overrides) where
    overrides is {day_abbr: {group_name: raw_cell}} containing ONLY the cells
    that actually differ from the main table (blank / 'same' / identical
    cells are dropped)."""
    jv_groups = parse_group_header(table_lines[0])
    main_names = {g["name"] for g in groups}
    for g in jv_groups:
        if g["name"] not in main_names:
            print(
                f"WARNING: Week {week_num} JV table has a '{g['name']}' column that isn't "
                f"in the main table - ignoring that column",
                file=sys.stderr,
            )
    raw = parse_table_rows(table_lines[2:], jv_groups, week_num, pad_missing=False)
    overrides = {}
    for day_abbr, cells in raw.items():
        if day_abbr not in days:
            print(
                f"WARNING: Week {week_num} JV table has a {day_abbr} row but the main "
                f"table doesn't - ignoring it",
                file=sys.stderr,
            )
            continue
        for gname, cell in cells.items():
            if gname not in main_names:
                continue
            if JV_BLANK_CELL_RE.match(cell):
                continue
            if _norm_cell(cell) == _norm_cell(days[day_abbr].get(gname, "")):
                continue
            overrides.setdefault(day_abbr, {})[gname] = cell
    return jv_groups, overrides


def parse_markdown(md_text):
    """Return a list of week dicts:
    {num, date_range, title, groups:[...], days: {abbr: {group: cell}},
     jv_groups:[...], jv_days: {abbr: {group: cell}}}
    jv_days only holds cells where JV differs from the main (Varsity) table."""
    # The "- Title" suffix after the header is optional: some weeks (e.g. a
    # source file's Week 14) only have "## **WEEK N: DATE**" with no title,
    # so that part of the header must not be required or the whole week
    # silently fails to match and gets skipped.
    week_re = re.compile(
        r"## \*\*WEEK (\d+): ([^*]+)\*\*[ \t]*(?:\u2014[ \t]*([^\n]+))?\n(.*?)"
        r"(?=\n## \*\*WEEK \d+:|\n## \*\*MILEAGE SUMMARY|\Z)",
        re.S,
    )
    weeks = []
    for m in week_re.finditer(md_text):
        num = int(m.group(1))
        date_range = m.group(2).strip()
        title = (m.group(3) or "").strip()
        body = m.group(4)

        tables = find_tables(body.splitlines())
        if not tables:
            print(f"WARNING: no table found for Week {num}", file=sys.stderr)
            continue

        main_lines = tables[0][1]
        groups = parse_group_header(main_lines[0])
        # main_lines[1] is the separator row (":---|:---")
        days = parse_table_rows(main_lines[2:], groups, num, pad_missing=True)

        jv_groups, jv_days = [], {}
        for prev_line, tbl in tables[1:]:
            if not JV_HEADING_RE.match(prev_line):
                print(
                    f"WARNING: Week {num} has an extra table that isn't introduced by a "
                    f"'#### JV Overrides' line - ignoring it",
                    file=sys.stderr,
                )
                continue
            if jv_groups:
                print(f"WARNING: Week {num} has more than one JV table - ignoring the extra one",
                      file=sys.stderr)
                continue
            jv_groups, jv_days = parse_jv_overrides(tbl, groups, days, num)

        weeks.append({
            "num": num,
            "date_range": date_range,
            "title": title,
            "groups": groups,
            "days": days,
            "jv_groups": jv_groups,
            "jv_days": jv_days,
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


def build_workout(day_abbr, group_name, cell_raw, week_num=None):
    label, qty, plain = parse_cell(cell_raw)
    # Some quality workouts aren't bolded in the source markdown (e.g. a
    # plain "6x200m@RP/200 steady *4mi*" with no ** around it) - fall back
    # to the plain leftover text so those still get classified correctly
    # instead of defaulting to "easy".
    effective_label = label or (plain if plain else None)
    wtype = classify(effective_label, cell_raw)
    miles, minutes, leftover = extract_miles_minutes(qty)
    dist_txt = format_dist(miles, minutes)
    is_estimated = False
    duration_txt = None  # raw duration text when there's no explicit mileage, e.g. "50min"

    if miles is None and wtype in ("easy", "long_run"):
        # No explicit mileage in the cell (e.g. "Easy *35min + 6x100m
        # strides*") - estimate it from the duration and the group's easy
        # pace instead of leaving it blank.
        est_minutes, duration_txt, leftover = extract_minutes_only(qty)
        estimated_miles = estimate_miles_from_minutes(est_minutes, group_name)
        if estimated_miles is not None:
            miles = estimated_miles
            is_estimated = True
            where = f"Week {week_num} " if week_num is not None else ""
            print(
                f"INFO: {where}{DAY_FULL.get(day_abbr, day_abbr)} {group_name} - "
                f"estimated {miles:g} mi from {est_minutes:g} min @ "
                f"{PACE_MIN_PER_MILE[group_name]:g} min/mi pace "
                f"(no explicit mileage in source)",
                file=sys.stderr,
            )
        else:
            duration_txt = None

    if wtype == "rest":
        return {
            "type": "rest", "desc": "REST", "pre": None, "post": None,
            "miles": None, "modal": None, "estimated": False,
        }

    if wtype == "tbd":
        return {
            "type": "tbd", "desc": label or "Workout TBD", "pre": None, "post": None,
            "miles": miles, "modal": None, "estimated": False,
        }

    if wtype == "easy":
        # "easy" always sits right after the quantity (miles and/or
        # duration), with any extra detail (e.g. "+ 6x100m strides")
        # trailing after that: "50min easy + 6x100m strides".
        quantity = dist_txt or duration_txt
        if quantity:
            desc = f"{quantity} easy" + (f" {leftover}" if leftover else "")
        elif qty:
            desc = f"{qty} easy"
        else:
            desc = plain or "Easy"
        if day_abbr == "Mon":
            pre = [(REF_FOOT, "Foot Drills"), (REF_WARMUP, "Dynamics"), (None, "Buildups")]
        else:
            pre = [(REF_WARMUP, "WU"), (REF_WARMUP, "Dynamics"), (None, "stride progression")]
        post = [(REF_WARMUP, "Strides"), (REF_MOBILITY, "Mobility/Strength A")]
        return {
            "type": "easy", "desc": desc, "pre": render_items(pre), "post": render_items(post),
            "miles": miles, "modal": MODAL_KEY_BY_TYPE.get(wtype), "estimated": is_estimated,
        }

    if wtype == "long_run":
        quantity = dist_txt or duration_txt
        if quantity:
            desc = f"Long Run {quantity}" + (f" {leftover}" if leftover else "")
        elif qty:
            desc = f"Long Run {qty}"
        else:
            desc = label or "Long Run"
        pre = [(REF_WARMUP, "Awesomizer"), (REF_WARMUP, "Lunge Matrix")]
        post = [(REF_WARMUP, "Strides"), (REF_MOBILITY, "Mobility A"), (None, "24s")]
        return {
            "type": "long_run", "desc": desc, "pre": render_items(pre), "post": render_items(post),
            "miles": miles, "modal": MODAL_KEY_BY_TYPE.get(wtype), "estimated": is_estimated,
        }

    if wtype == "race":
        desc = label or "Race"
        pre = [(REF_WARMUP, "Race Day WU")]
        post = [(REF_WARMUP, "Post Race")]
        return {
            "type": "race", "desc": desc, "pre": render_items(pre), "post": render_items(post),
            "miles": miles, "modal": MODAL_KEY_BY_TYPE.get(wtype), "estimated": False,
        }

    # quality
    desc = label or plain or qty or "Workout"
    subtype = classify_quality_subtype(effective_label)
    pre = [(REF_WARMUP, "WU"), (REF_WARMUP, "Dynamics"), (None, "stride progression")]
    if re.search(r"@r\b", (effective_label or "").lower()) or "200m" in (effective_label or "").lower():
        post = [(REF_WARMUP, "Strides"), (REF_MOBILITY, "Mobility/Strength A")]
    else:
        post = [(REF_MOBILITY, "Mobility/Strength B")]
    return {
        "type": "quality", "subtype": subtype, "desc": desc,
        "pre": render_items(pre), "post": render_items(post),
        "miles": miles, "modal": MODAL_KEY_BY_QUALITY_SUBTYPE.get(subtype, "quality-workout"),
        "estimated": False,
    }


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

SQUAD_LABEL = {"varsity": "VARSITY", "jv": "JV"}


def render_workout_item(group_name, wo, squad="all"):
    """squad: 'all' (everyone in the group does this), or 'varsity' / 'jv'
    when the group has separate Varsity and JV workouts that day."""
    cls = GROUP_CLASS.get(group_name, group_name.lower())
    squad_tag = (
        f'<span class="squad-tag {squad}">{SQUAD_LABEL[squad]}</span>'
        if squad in SQUAD_LABEL else ""
    )
    item_cls = f"{cls} jv-row" if squad == "jv" else cls

    if wo["type"] == "rest":
        return f'''                    <div class="workout-item {item_cls}" data-group="{group_name}" data-squad="{squad}">
                        <div class="group-badge {cls}">{group_name}{squad_tag}</div>
                        <div class="workout-details">
                            <div class="workout-desc"><span>REST</span></div>
                        </div>
                        <div class="workout-miles">&mdash;</div>
                    </div>'''

    miles_txt = "&mdash;"
    miles_title = ""
    if wo["miles"] is not None:
        if wo.get("estimated"):
            miles_txt = f'~{wo["miles"]:.1f} mi'
            miles_title = ' title="Estimated from the workout duration and easy pace - no explicit mileage in the source schedule"'
        else:
            miles_txt = f'{wo["miles"]:.1f} mi'
    info_icon_html = ""
    if wo.get("modal"):
        info_icon_html = (
            f'<span class="info-icon" onclick="openModal(\'{wo["modal"]}\')" '
            f'title="Click for workout details">i</span>'
        )
    pre_html = f'<div class="workout-pre">{wo["pre"]}</div>' if wo["pre"] else ""
    post_html = f'<div class="workout-post">{wo["post"]}</div>' if wo["post"] else ""

    return f'''                    <div class="workout-item {item_cls}" data-group="{group_name}" data-squad="{squad}">
                        <div class="group-badge {cls}">{group_name}{squad_tag}</div>
                        <div class="workout-details">
                            {pre_html}
                            <div class="workout-desc">
                                <span>{wo["desc"]}</span>
                                {info_icon_html}
                            </div>
                            {post_html}
                        </div>
                        <div class="workout-miles"{miles_title}>{miles_txt}</div>
                    </div>'''


def compute_week_workouts(week):
    """Build every cell's workout dict once per week:
        {day: {"main": {group: workout}, "jv": {group: workout}}}
    "main" is the Varsity / default schedule; "jv" only has entries for the
    group/days where the JV override table differs. Reused for rendering and
    for the weekly mileage totals so the totals always match the daily rows."""
    computed = {}
    jv_days = week.get("jv_days", {})
    for day_abbr, day_cells in week["days"].items():
        computed[day_abbr] = {
            "main": {
                group_name: build_workout(day_abbr, group_name, cell_raw, week_num=week["num"])
                for group_name, cell_raw in day_cells.items()
            },
            "jv": {
                group_name: build_workout(day_abbr, group_name, cell_raw, week_num=week["num"])
                for group_name, cell_raw in jv_days.get(day_abbr, {}).items()
            },
        }
    return computed


def render_day(day_abbr, day_workouts):
    main, jv = day_workouts["main"], day_workouts["jv"]
    has_quality = any(wo["type"] == "quality" for wo in list(main.values()) + list(jv.values()))

    groups_btn = (
        ' <a href="athlete_groups.html" target="_blank" class="groups-btn" '
        'title="View training groups">👥 Groups</a>' if has_quality else ""
    )

    items = []
    for g in GROUP_DISPLAY_ORDER:
        if g not in main:
            continue
        if g in jv:
            items.append(render_workout_item(g, main[g], squad="varsity"))
            items.append(render_workout_item(g, jv[g], squad="jv"))
        else:
            items.append(render_workout_item(g, main[g]))
    items_html = "\n".join(items)

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
    header_totals = {g["name"]: g["total"] for g in week["groups"]}
    jv_header_totals = {g["name"]: g["total"] for g in week.get("jv_groups", [])}

    workouts_by_day = compute_week_workouts(week)

    # Varsity total = the main table. JV total = the main table with any JV
    # override swapped in for that day.
    varsity_totals = {g: 0.0 for g in ordered_groups}
    jv_totals = {g: 0.0 for g in ordered_groups}
    jv_group_names = set()   # groups that have at least one JV override this week
    prov_varsity, prov_jv = set(), set()   # totals that omit a TBD workout with no mileage
    jv_day_abbrs = []        # days (in week order) where any group's JV differs
    for day_abbr in DAY_ORDER:
        day = workouts_by_day.get(day_abbr)
        if not day:
            continue
        if day["jv"]:
            jv_day_abbrs.append(day_abbr)
        for g in ordered_groups:
            main_wo = day["main"].get(g)
            jv_wo = day["jv"].get(g)
            if main_wo is not None and main_wo["miles"] is not None:
                varsity_totals[g] += main_wo["miles"]
            if main_wo is not None and main_wo["type"] == "tbd" and main_wo["miles"] is None:
                prov_varsity.add(g)
            effective = jv_wo if jv_wo is not None else main_wo
            if effective is not None and effective["miles"] is not None:
                jv_totals[g] += effective["miles"]
            if effective is not None and effective["type"] == "tbd" and effective["miles"] is None:
                prov_jv.add(g)
            if jv_wo is not None:
                jv_group_names.add(g)

    for g in ordered_groups:
        header_val = header_totals.get(g)
        if header_val is not None and g not in prov_varsity and abs(header_val - varsity_totals[g]) > 0.05:
            print(
                f"WARNING: Week {week['num']} {g} - markdown header says "
                f"{header_val:g} mi but the daily cells add up to "
                f"{varsity_totals[g]:g} mi; using the computed total",
                file=sys.stderr,
            )
        jv_header_val = jv_header_totals.get(g)
        if jv_header_val is not None and g not in prov_jv and abs(jv_header_val - jv_totals[g]) > 0.05:
            print(
                f"WARNING: Week {week['num']} {g} - JV table header says "
                f"{jv_header_val:g} mi but the main cells + JV overrides add up to "
                f"{jv_totals[g]:g} mi; using the computed total",
                file=sys.stderr,
            )

    tbd_title = ' title="Doesn\'t include a TBD workout that has no mileage yet"'

    def total_card(g):
        jv_line = (
            f'\n            <div class="total-jv"{tbd_title if g in prov_jv else ""}>'
            f'JV {jv_totals[g]:g}{"+" if g in prov_jv else ""}</div>'
            if g in jv_group_names else ""
        )
        return f'''        <div class="total {GROUP_CLASS.get(g, g.lower())}" onclick="filterGroup('{g}')" id="total-{g}">
            <div class="total-label">{g}</div>
            <div class="total-miles"{tbd_title if g in prov_varsity else ""}>{varsity_totals[g]:g}{"+" if g in prov_varsity else ""}</div>{jv_line}
        </div>'''

    totals_html = "\n".join(total_card(g) for g in ordered_groups)

    filters_html = '        <button class="filter-btn active" data-group="" onclick="showAll()">Show All</button>\n' + "\n".join(
        f'        <button class="filter-btn" data-group="{g}" onclick="filterGroup(\'{g}\')">{g}</button>' for g in ordered_groups
    )

    # Only weeks that actually have JV overrides get the note + squad filter.
    note_html = ""
    squad_html = ""
    if jv_day_abbrs:
        days_txt = ", ".join(DAY_FULL[d].title() for d in jv_day_abbrs)
        note_html = (
            '    <div class="jv-note">🔀 <strong>Separate Varsity &amp; JV workouts this week</strong> '
            f'(JV differs on: {days_txt}). Where they differ, each group shows a Varsity row and a JV row. '
            'Big mileage numbers are Varsity; JV mileage is shown underneath.</div>\n'
        )
        squad_html = (
            '    <div class="filters squad-filters">\n'
            '        <button class="squad-btn active" data-squad="all" onclick="filterSquad(\'all\')">Everyone</button>\n'
            '        <button class="squad-btn" data-squad="varsity" onclick="filterSquad(\'varsity\')">Varsity</button>\n'
            '        <button class="squad-btn" data-squad="jv" onclick="filterSquad(\'jv\')">JV</button>\n'
            '    </div>\n'
        )

    days_html = "\n".join(
        render_day(d, workouts_by_day[d]) for d in DAY_ORDER if d in workouts_by_day
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
{note_html}
    <div class="totals">
{totals_html}
    </div>

    <div class="filters">
{filters_html}
    </div>
{squad_html}
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

    existing = [
        os.path.join(outdir, f"week{week['num']}.html")
        for week in sorted(weeks, key=lambda w: w["num"])
        if os.path.exists(os.path.join(outdir, f"week{week['num']}.html"))
    ]
    overwrite_all = args.force
    if existing and not args.force:
        print(f"\n{len(existing)} file(s) already exist and would be overwritten:")
        for p in existing:
            print(f"  - {os.path.basename(p)}")
        answer = input("Overwrite all of these? [y/N]: ").strip().lower()
        overwrite_all = answer in ("y", "yes")
        if not overwrite_all:
            print("Skipping all existing files (new weeks will still be written).")

    written, skipped = 0, 0
    for week in sorted(weeks, key=lambda w: w["num"]):
        out_path = os.path.join(outdir, f"week{week['num']}.html")

        if os.path.exists(out_path) and not overwrite_all:
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
