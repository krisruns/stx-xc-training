#!/usr/bin/env python3
"""
Training Overview to Week Schedule CSV Converter
Generates weekly schedules in the STX training format

Usage:
    python overview_to_week_schedule.py Training_Master - Training_Overview.csv
"""

import pandas as pd
import csv
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Anchor: Week 8 starts Monday July 14, 2025
WEEK_8_START = datetime(2026, 7, 13)


def week_start_date(week_num):
    """Return the Monday start date for a given week number as ISO string (YYYY-MM-DD)."""
    return (WEEK_8_START + timedelta(weeks=(int(week_num) - 8))).strftime('%Y-%m-%d')

# Pre/Post schedule CSV path (can be overridden via command-line arg)
PRE_POST_CSV = 'Training_Master_-_pre_post.csv'

# Workout type classification keywords
WORKOUT_TYPES = {
    'Race':               ['race'],
    'Rest':               ['rest'],
    'LongRunProgression': ['progression'],
    'LongRun':            ['long run', 'lr'],
    'Workout':            ['hill', 'fartlek', 'pre', 'interval', 'tempo'],
    'Easy':               ['easy'],
    'Time Trial':         ['time trial', 'tt'],
    'Split 400s':         ['split 400s'],
}


def load_pre_post_schedule(csv_path=None):
    """Load pre/post routines from CSV.
    Searches: (1) current working directory, (2) same folder as this script.
    Falls back to glob match on *pre_post*.csv if exact name fails.
    Expected columns: Day, Workout_Type, Pre, Post
    """
    import glob as _glob
    filename = csv_path or PRE_POST_CSV
    script_dir = Path(__file__).resolve().parent

    # Exact name candidates
    candidates = [
        Path(filename),
        script_dir / Path(filename).name,
    ]
    found_path = next((p for p in candidates if p.exists()), None)

    # Glob fallback - find any *pre_post*.csv in the same folder as script
    if found_path is None:
        matches = list(script_dir.glob('*pre_post*.csv'))
        if matches:
            found_path = matches[0]
            print(f"  (found via glob: {found_path.name})")

    if found_path is None:
        print(f"ERROR: Could not find pre/post CSV. Searched in: {script_dir}")
        print(f"  CSV files in that folder: {[p.name for p in script_dir.glob('*.csv')]}")
        return []

    rows = []
    with open(found_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k.strip(): v.strip() for k, v in row.items()})
    print(f"✓ Loaded {len(rows)} pre/post rules from: {found_path.resolve()}")
    return rows


# Module-level cache so the CSV is only read once per run
_PRE_POST_RULES = None


def get_pre_post_rules():
    global _PRE_POST_RULES
    if not _PRE_POST_RULES:
        _PRE_POST_RULES = load_pre_post_schedule()
    return _PRE_POST_RULES

# Group name mapping
GROUP_NAMES = {
    'GOLD': 'Gold',
    'GREEN': 'Green', 
    'WHITE': 'White',
    'BLUE': 'Blue'
}

# Day abbreviations
DAY_ABBREV = {
    'Monday': 'Mon',
    'Tuesday': 'Tue',
    'Wednesday': 'Wed',
    'Thursday': 'Thu',
    'Friday': 'Fri',
    'Saturday': 'Sat',
    'Sunday': 'Sun'
}

# ─── MILEAGE CALCULATION SYSTEM ─────────────────────────────────────────────
import re as _re

METERS_PER_MILE = 1609.34
WU_CD_MILES     = 2.5

_GROUP_IDX    = {'Gold': 0, 'Green': 1, 'White': 2, 'Blue': 3}
_MAX_REGULAR  = [9.0, 7.5, 6.0, 5.0]
_MAX_LONG_RUN = [13.0, 11.0, 9.0, 7.0]

# ─── GROUP SCALING ────────────────────────────────────────────────────────────
# Rules:
#   Intervals ≥ 800m : each group does 1 fewer rep  (Gold → Green → White → Blue)
#   Intervals <  800m : each group does 2 fewer reps
#   Tempo mileage     : each group does 1 fewer mile
# Minimums: 2 reps for intervals, 1.0 mi for tempo segments

_MIN_INTERVAL_REPS = 2
_MIN_TEMPO_MILES   = 1.0


def _scale_reps(gold_reps, dist_m, group):
    """Return scaled rep count for a group."""
    step = 1 if dist_m >= 800 else 2
    return max(_MIN_INTERVAL_REPS, gold_reps - _GROUP_IDX.get(group, 0) * step)


def _scale_miles(gold_miles, group):
    """Return scaled tempo miles for a group."""
    return max(_MIN_TEMPO_MILES, gold_miles - _GROUP_IDX.get(group, 0))


def _scale_segment(seg, group):
    """
    Scale a single workout segment string for a group.
    Returns the scaled segment string.
    Handles:
      NxDm@type (rest)   — interval/rep segment
      N-Mx D m@type(rest)— range: upper bound = Gold count
      Nmi @type          — tempo mileage segment
    Timed rests, plain text, etc. pass through unchanged.
    """
    seg = seg.strip()
    if not seg:
        return seg

    # Timed rest alone: (2:30), (90s), (3:00), "1:00 rest"
    if _re.fullmatch(r'\([\d:]+\s*(?:min|sec|s|m)?\)', seg, _re.I):
        return seg
    if _re.fullmatch(r'[\d]+:[\d]+\s*(?:rest)?', seg, _re.I):
        return seg

    # Interval/rep: [N-M|N]xD[m|mi] [@type] [(rest)]
    m = _re.match(
        r'^(\d+(?:-\d+)?)\s*([x×])\s*([\d.]+)\s*(m(?:i(?:le)?)?|km)?'
        r'(\s*@\w+)?(\s*\([^)]+\))?(.*)$',
        seg, _re.I
    )
    if m:
        rep_str  = m.group(1)
        x_char   = m.group(2)
        dist_val = float(m.group(3))
        unit_raw = (m.group(4) or 'm')
        at_type  = m.group(5) or ''
        rest_par = m.group(6) or ''
        suffix   = m.group(7) or ''

        unit_lo  = unit_raw.lower().rstrip('le')          # 'mi' or 'm' or 'km'
        dist_m   = dist_val * 1609.34 if 'mi' in unit_lo else dist_val

        # Gold rep count: upper bound if range, else the number itself
        # For ranges: Gold/Green → upper bound, White/Blue → lower bound
        # For plain counts: apply the standard step rule (-1 or -2 per group)
        if '-' in rep_str:
            parts_r     = rep_str.split('-')
            upper_bound = int(parts_r[-1])
            lower_bound = int(parts_r[0])
            # Gold=0, Green=1 → upper; White=2, Blue=3 → lower
            scaled = upper_bound if _GROUP_IDX.get(group, 0) <= 1 else lower_bound
        else:
            gold_reps = int(rep_str)
            scaled    = int(_scale_reps(gold_reps, dist_m, group))

        # Reconstruct — keep original distance/unit/type/rest formatting
        unit_out = unit_raw if unit_raw else 'm'
        dist_out = f"{int(dist_val)}" if dist_val == int(dist_val) else str(dist_val)
        return f"{scaled}{x_char}{dist_out}{unit_out}{at_type}{rest_par}{suffix}"

    # Tempo mileage: Nmi @type [(rest)]
    m = _re.match(
        r'^(\d+(?:\.\d+)?)\s*(mi(?:le)?)\s*(@\w+)?(\s*\([^)]+\))?(.*)$',
        seg, _re.I
    )
    if m:
        miles    = float(m.group(1))
        unit_raw = m.group(2)
        at_type  = m.group(3) or ''
        rest_par = m.group(4) or ''
        suffix   = m.group(5) or ''

        scaled = _scale_miles(miles, group)
        scaled = round(scaled * 2) / 2   # round to 0.5
        out    = f"{int(scaled)}" if scaled == int(scaled) else str(scaled)
        return f"{out}{unit_raw}{at_type}{rest_par}{suffix}"

    return seg   # nothing to scale


def scale_workout_for_group(desc, group):
    """
    Return the workout description scaled for a given group.
    Gold is canonical (no change). Other groups get fewer reps / miles
    according to the scaling rules above.

    Compound workouts ('+' separated) are scaled segment by segment.
    Timed rests, fartleks, hills, easy runs, etc. pass through unchanged.
    """
    if not desc or not desc.strip():
        return desc or ''

    dl = desc.lower().strip()

    # These workout types are never rep-scaled
    for kw in ('easy', 'rest', 'off', 'fartlek', 'hill', 'long run', 'lr ',
               'progression', 'shakeout', 'race', 'time trial', 'tempo\n',
               'shakeout'):
        if kw in dl:
            return desc
    if dl.strip() == 'tempo':
        return desc

    # Split on '+' (major separator), then on ' - ' (minor separator within segments)
    # Preserve the separators for reconstruction.
    major_raw = _re.split(r'(\s*\+\s*)', desc)
    result    = []

    for part in major_raw:
        if _re.fullmatch(r'\s*\+\s*', part):
            result.append(part)
            continue

        # Split on ' - ' style separators, keeping them for reconstruction
        minor_raw = _re.split(r'(\s+-\s+)', part)
        scaled_minor = []

        for sub in minor_raw:
            if _re.fullmatch(r'\s+-\s+', sub):
                scaled_minor.append(sub)
            else:
                scaled_minor.append(_scale_segment(sub, group))

        result.append(''.join(scaled_minor))

    return ''.join(result)
_MIN_EASY     = 2.0
_RACE_WUCD    = [2.5, 2.5, 2.0, 2.0]
_HILLS_MINS   = [35, 30, 25, 20]
_LR_PCT       = 0.25


def _parse_rep_range(s):
    if '-' in s:
        parts = s.split('-')
        return (float(parts[0]) + float(parts[-1])) / 2
    return float(s)


def _parse_segment_meters(seg):
    seg = seg.strip()
    if not seg:
        return 0.0
    if _re.fullmatch(r'\([\d:]+\s*(?:min|sec|s|m)?\)', seg, _re.I):
        return 0.0
    if _re.fullmatch(r'[\d]+:[\d]+', seg):
        return 0.0
    if _re.fullmatch(r'[\d]+:[\d]+\s*rest', seg, _re.I):
        return 0.0
    # Nmin@type — timed jog between segments
    m = _re.match(r'^(\d+(?:\.\d+)?)\s*min\b', seg, _re.I)
    if m:
        return (float(m.group(1)) / 8.0) * METERS_PER_MILE
    # Nmi@type
    m = _re.match(r'^(\d+(?:\.\d+)?)\s*mi\b', seg, _re.I)
    if m:
        return float(m.group(1)) * METERS_PER_MILE
    # NxDm@type [(RESTj)]
    m = _re.match(
        r'^(\d+(?:-\d+)?)\s*[x×]\s*([\d.]+)\s*(m(?:i(?:le)?)?|km)?\s*'
        r'(?:@\w+)?\s*(?:\(([^)]+)\))?',
        seg, _re.I
    )
    if m:
        reps = _parse_rep_range(m.group(1))
        dist = float(m.group(2))
        unit = (m.group(3) or 'm').lower().rstrip('le')
        rest_str = (m.group(4) or '').strip()
        dist_m = dist * METERS_PER_MILE if 'mi' in unit else dist
        interval_m = reps * dist_m
        jog_m = 0.0
        jog = _re.match(r'^(\d+)\s*j', rest_str, _re.I)
        if jog:
            jog_m = reps * float(jog.group(1))
        return interval_m + jog_m
    return 0.0


def parse_workout_meters(desc):
    """Return (total_meters, parsed_ok) for a structured workout description."""
    if not desc:
        return 0.0, False
    dl = desc.lower().strip()
    for kw in ('easy', 'rest', 'off', 'fartlek', 'hill', 'long run',
                'lr ', 'progression', 'shakeout', 'tempo', 'time trial'):
        if kw in dl:
            return 0.0, False
    major = _re.split(r'\s*\+\s*', desc)
    segs = []
    for part in major:
        segs.extend(_re.split(r'\s+-\s+', part))
    total_m, got = 0.0, False
    for seg in segs:
        m = _parse_segment_meters(seg)
        if m > 0:
            got = True
        total_m += m
    return total_m, got


def _parse_fartlek_minutes(desc):
    m = _re.search(
        r'(\d+(?:\.\d+)?)\s*[x×\[]\s*'
        r'(\d+(?::\d+)?)\s*(?:min\s*)?(?:on|fast|harder)\s*[/,]\s*'
        r'(\d+(?::\d+)?)\s*(?:min\s*)?(?:steady|off|easy|recover)',
        desc.lower()
    )
    if m:
        def to_min(t):
            if ':' in t:
                p = t.split(':')
                return int(p[0]) + int(p[1]) / 60
            return float(t)
        return float(m.group(1)) * (to_min(m.group(2)) + to_min(m.group(3)))
    return None


def _parse_race_miles(desc):
    dl = desc.lower()
    m = _re.search(r'(\d+(?:\.\d+)?)\s*mi(?:le)?\s*(?:race|run|tt)', dl)
    if m:
        return float(m.group(1))
    if '5k' in dl or '5km' in dl:
        return 3.1
    m2 = _re.search(r'(\d)\s*mile', dl)
    if m2:
        return float(m2.group(1))
    return 3.1


def _fixed_day_miles(desc, group):
    """Return (miles, day_type) for a single day's workout description."""
    if not desc or str(desc).strip() == '':
        return 0.0, 'rest'
    dl  = str(desc).lower().strip()
    idx = _GROUP_IDX.get(group, 3)

    if 'rest' in dl or dl == 'off':
        return 0.0, 'rest'

    if dl.startswith('race'):
        wucd = _RACE_WUCD[idx]
        dist = _parse_race_miles(desc)
        return round((wucd + dist) * 2) / 2, 'race'

    if 'time trial' in dl:
        dist = _re.search(r'(\d+(?:\.\d+)?)\s*mi', dl)
        tt_dist = float(dist.group(1)) if dist else 2.0
        return round((WU_CD_MILES + tt_dist) * 2) / 2, 'tt'

    if 'shakeout' in dl:
        return 3.0, 'shakeout'

    if 'long run' in dl or (dl.startswith('lr')):
        return 0.0, 'lr'

    if dl.startswith('progression'):
        prog_mins = {'progression 1': 35, 'progression 2': 40, 'progression 3': 45}
        mins = next((v for k, v in prog_mins.items() if k in dl), 40)
        miles = round((mins / 8.0) * 2) / 2
        return min(miles, _MAX_REGULAR[idx]), 'progression'

    if 'hill' in dl:
        hill_miles = _HILLS_MINS[idx] / 7.0
        total = round((WU_CD_MILES + hill_miles) * 2) / 2
        return min(total, _MAX_REGULAR[idx]), 'hills'

    if 'fartlek' in dl or 'pre 30' in dl or 'pre 40' in dl:
        if 'pre 40' in dl:
            mins = 40
        elif 'pre 30' in dl:
            mins = 30
        else:
            mins = _parse_fartlek_minutes(desc) or [35, 30, 25, 20][idx]
        miles = round((WU_CD_MILES + mins / 8.0) * 2) / 2
        return min(miles, _MAX_REGULAR[idx]), 'fartlek'

    if dl.strip() == 'tempo':
        tempo_miles = [30, 25, 20, 15][idx] / 6.5
        total = round((WU_CD_MILES + tempo_miles) * 2) / 2
        return min(total, _MAX_REGULAR[idx]), 'workout'

    workout_m, parsed = parse_workout_meters(desc)
    if parsed and workout_m > 0:
        total = round((WU_CD_MILES + workout_m / METERS_PER_MILE) * 2) / 2
        return min(total, _MAX_REGULAR[idx]), 'workout'

    if 'easy' in dl or dl == 'e':
        return 0.0, 'easy'

    return 0.0, 'easy'


def distribute_week_mileage(week_schedule, group, weekly_vol):
    """
    Two-pass: fix workout/race/LR/rest mileage, distribute remainder as easy.

    Args:
        week_schedule: dict of day → {'v': desc, 'jv': desc}
        group:         training group name
        weekly_vol:    target weekly mileage for this group

    Returns:
        dict of day → {'v': miles, 'jv': miles}
    """
    idx = _GROUP_IDX.get(group, 3)
    if not weekly_vol:
        return {d: {'v': 0.0, 'jv': 0.0} for d in week_schedule}

    fixed = {}
    easy_days_v, easy_days_jv = [], []

    for day, descs in week_schedule.items():
        # Scale canonical (Gold) description for this group before calculating mileage
        v_desc  = scale_workout_for_group(descs.get('v',  '') or '', group)
        jv_desc = scale_workout_for_group(descs.get('jv', '') or '', group) if descs.get('jv') else ''
        v_miles,  v_type  = _fixed_day_miles(v_desc,  group)
        jv_miles, jv_type = _fixed_day_miles(jv_desc, group) if jv_desc else (v_miles, v_type)
        fixed[day] = {'v': v_miles, 'jv': jv_miles, 'tv': v_type, 'tj': jv_type}
        if v_type == 'easy':
            easy_days_v.append(day)
        if jv_desc and jv_type == 'easy':
            easy_days_jv.append(day)

    # Size long run
    for day, info in fixed.items():
        if info['tv'] == 'lr':
            lr = min(round(weekly_vol * _LR_PCT * 2) / 2, _MAX_LONG_RUN[idx])
            fixed[day]['v'] = lr
            fixed[day]['jv'] = lr

    # Distribute easy — V side
    fixed_v = sum(i['v'] for i in fixed.values())
    rem_v = max(0.0, weekly_vol - fixed_v)
    if easy_days_v and rem_v > 0:
        per = max(_MIN_EASY, min(round(rem_v / len(easy_days_v) * 2) / 2, _MAX_REGULAR[idx]))
        for day in easy_days_v:
            fixed[day]['v'] = per

    # Distribute easy — JV side
    fixed_jv = sum(i['jv'] for i in fixed.values())
    rem_jv = max(0.0, weekly_vol - fixed_jv)
    if easy_days_jv and rem_jv > 0:
        per_jv = max(_MIN_EASY, min(round(rem_jv / len(easy_days_jv) * 2) / 2, _MAX_REGULAR[idx]))
        for day in easy_days_jv:
            fixed[day]['jv'] = per_jv

    return {day: {'v': info['v'], 'jv': info['jv']} for day, info in fixed.items()}


def get_mileage_for_group(group, workout_desc, weekly_vol):
    """Compatibility shim — used for single-day lookups."""
    miles, _ = _fixed_day_miles(workout_desc, group)
    if miles > 0:
        return miles
    idx = _GROUP_IDX.get(group, 3)
    return min(round(weekly_vol * 0.13 * 2) / 2, _MAX_REGULAR[idx])



def expand_workout_description(desc, group, calculated_miles):
    """Expand general workout description into detailed Main_Workout
    
    Args:
        desc: Workout description from overview
        group: Training group (Gold, Green, White, Blue)
        calculated_miles: The actual calculated mileage for this workout
    """
    if not desc or pd.isna(desc):
        return ""
    
    desc_str = str(desc).strip()
    desc_lower = desc_str.lower()
    
    # Group-specific scaling for rep counts
    group_idx = {'Gold': 0, 'Green': 1, 'White': 2, 'Blue': 3}
    idx = group_idx.get(group, 3)
    
    # Fartlek workouts
    if 'fartlek' in desc_lower:
        if '5-4-3-2-1' in desc_str:
            rep_counts = [6, 6, 4, 2][idx]
            return f"10min WU; Fartlek: 5-4-3-2-1 w/ half recovery; 10min CD + {rep_counts}x200 cut down"
        return f"10min WU; {desc_str}; 10min CD"
    
    # Hills
    elif 'hill' in desc_lower:
        durations = [35, 30, 25, 20][idx]
        return f"10min WU; Hills - {durations}min; 10min CD"
    
    # Pre 30/40 workouts
    elif 'pre 30' in desc_lower or 'pre 40' in desc_lower:
        return f"WU; {desc_str}; CD"
    
    # Long runs - calculate time based on mileage at 7:30 pace
    elif 'long run' in desc_lower or 'lr' in desc_lower:
        if 'progression' in desc_lower:
            # Calculate time: mileage * 7.5 minutes per mile, round to nearest 5 min
            minutes = calculated_miles * 7.5
            rounded_minutes = round(minutes / 5) * 5  # Round to nearest 5 minutes
            # Format mileage: remove .0 if whole number
            miles_str = f"{calculated_miles:.0f}" if calculated_miles % 1 == 0 else f"{calculated_miles:.1f}"
            return f"Long Run {miles_str}mi/{int(rounded_minutes)}min - Progression"
        else:
            miles_str = f"{calculated_miles:.0f}" if calculated_miles % 1 == 0 else f"{calculated_miles:.1f}"
            return f"Long Run {miles_str}mi"
    
    # Easy runs - use calculated mileage
    elif 'easy' in desc_lower or desc_lower == 'e':
        # Format mileage: remove .0 if whole number
        miles_str = f"{calculated_miles:.0f}" if calculated_miles % 1 == 0 else f"{calculated_miles:.1f}"
        return f"{miles_str}mi easy"
    
    # Race
    elif 'race' in desc_lower:
        return "Race"
    
    # Rest
    elif 'rest' in desc_lower:
        return "REST"
    
    # Default - use as provided
    return desc_str

def classify_workout(workout_desc):
    """Classify a workout description into a Workout_Type string."""
    desc_lower = str(workout_desc).lower() if workout_desc else ''
    for wtype, keywords in WORKOUT_TYPES.items():
        if any(kw in desc_lower for kw in keywords):
            return wtype
    return 'Easy'  # default


def determine_pre_post(workout_desc, day):
    """Determine Pre and Post workout routines by looking up pre_post_schedule.csv.

    Matching priority:
      1. Day-specific row  (e.g. Day=Friday,  Workout_Type=Easy)
      2. Any-day row       (e.g. Day=Any,     Workout_Type=Easy)
      3. Fallback to empty strings if nothing matches
    """
    rules = get_pre_post_rules()
    wtype = classify_workout(workout_desc)

    # 1. Day-specific match
    for rule in rules:
        if rule.get('Day', '').lower() == day.lower() and rule.get('Workout_Type') == wtype:
            return rule.get('Pre', ''), rule.get('Post', '')

    # 2. Any-day match
    for rule in rules:
        if rule.get('Day', '').lower() == 'any' and rule.get('Workout_Type') == wtype:
            return rule.get('Pre', ''), rule.get('Post', '')

    # 3. Fallback
    return '', ''

def update_descriptions_after_adjustment(df):
    """
    Update Main_Workout descriptions to match adjusted mileages
    
    Args:
        df: DataFrame with adjusted mileages
    
    Returns:
        DataFrame with updated descriptions
    """
    for idx, row in df.iterrows():
        desc = row['Main_Workout']
        miles = row['Miles']
        
        # Update easy run descriptions
        if 'mi easy' in desc:
            # Extract and replace mileage
            miles_str = f"{miles:.0f}" if miles % 1 == 0 else f"{miles:.1f}"
            # Replace the old mileage with new
            import re
            new_desc = re.sub(r'[\d.]+mi easy', f'{miles_str}mi easy', desc)
            df.at[idx, 'Main_Workout'] = new_desc
        
        # Update long run descriptions
        elif 'Long Run' in desc and 'mi/' in desc:
            # Extract and replace mileage, recalculate time
            miles_str = f"{miles:.0f}" if miles % 1 == 0 else f"{miles:.1f}"
            # Calculate new time at 7:30 pace
            minutes = miles * 7.5
            rounded_minutes = round(minutes / 5) * 5
            # Replace in description
            import re
            # Match pattern like "Long Run 11mi/80min - Progression"
            new_desc = re.sub(r'Long Run [\d.]+mi/\d+min', 
                            f'Long Run {miles_str}mi/{int(rounded_minutes)}min', 
                            desc)
            df.at[idx, 'Main_Workout'] = new_desc
    
    return df

def adjust_mileages_to_target(df, target_volumes):
    """
    Adjust daily mileages to match target weekly volumes
    
    Uses a two-phase approach:
    1. Adjust shared days to hit racer target
    2. Fine-tune split days to balance both groups
    
    Args:
        df: DataFrame with rows for the week
        target_volumes: dict of group -> target weekly mileage
    
    Returns:
        DataFrame with adjusted mileages
    """
    adjusted_rows = []
    
    for group in ['Gold', 'Green', 'White', 'Blue']:
        target_vol = target_volumes.get(group, 0)
        if target_vol == 0:
            # No target, keep as is
            group_df = df[df['Group'] == group]
            adjusted_rows.extend(group_df.to_dict('records'))
            continue
        
        group_df = df[df['Group'] == group].copy()
        
        # Separate into shared, racer-only, and non-racer-only days
        shared_days = group_df[group_df['Status'] == ''].copy()
        racer_days = group_df[group_df['Status'] == 'Racer'].copy()
        nonracer_days = group_df[group_df['Status'] == 'Non-Racer'].copy()
        
        # Calculate current totals
        shared_total = shared_days['Miles'].sum()
        racer_only_total = racer_days['Miles'].sum()
        nonracer_only_total = nonracer_days['Miles'].sum()
        
        # Identify race days (don't adjust these)
        shared_race_miles = shared_days[
            shared_days['Main_Workout'].str.contains('Race', case=False, na=False)
        ]['Miles'].sum()
        racer_race_miles = racer_days[
            racer_days['Main_Workout'].str.contains('Race', case=False, na=False)
        ]['Miles'].sum()
        nonracer_race_miles = nonracer_days[
            nonracer_days['Main_Workout'].str.contains('Race', case=False, na=False)
        ]['Miles'].sum()
        
        # Calculate adjustable mileage
        shared_adjustable = shared_total - shared_race_miles
        racer_adjustable = racer_only_total - racer_race_miles
        nonracer_adjustable = nonracer_only_total - nonracer_race_miles
        
        # Calculate shortfalls
        racer_current = shared_total + racer_only_total
        nonracer_current = shared_total + nonracer_only_total
        racer_shortfall = target_vol - racer_current
        nonracer_shortfall = target_vol - nonracer_current
        
        # Only adjust if shortfall is significant
        if abs(racer_shortfall) > 0.5 or abs(nonracer_shortfall) > 0.5:
            # Phase 1: Adjust shared days to get racers close to target
            total_racer_adjustable = shared_adjustable + racer_adjustable
            if total_racer_adjustable > 0:
                racer_factor = racer_shortfall / total_racer_adjustable
            else:
                racer_factor = 0
            
            # Adjust shared days
            for idx, row in shared_days.iterrows():
                is_race = 'race' in str(row['Main_Workout']).lower()
                if not is_race:
                    new_miles = row['Miles'] * (1 + racer_factor)
                    new_miles = round(new_miles * 2) / 2  # Round to 0.5
                    shared_days.at[idx, 'Miles'] = new_miles
            
            # Adjust racer-only days
            for idx, row in racer_days.iterrows():
                is_race = 'race' in str(row['Main_Workout']).lower()
                if not is_race:
                    new_miles = row['Miles'] * (1 + racer_factor)
                    new_miles = round(new_miles * 2) / 2
                    racer_days.at[idx, 'Miles'] = new_miles
            
            # Phase 2: Adjust non-racer-only days independently
            # Recalculate after phase 1
            new_shared_total = shared_days['Miles'].sum()
            new_nonracer_current = new_shared_total + nonracer_only_total
            new_nonracer_shortfall = target_vol - new_nonracer_current
            
            if abs(new_nonracer_shortfall) > 0.5 and nonracer_adjustable > 0:
                nonracer_factor = new_nonracer_shortfall / nonracer_adjustable
                
                # Adjust non-racer-only days
                for idx, row in nonracer_days.iterrows():
                    is_race = 'race' in str(row['Main_Workout']).lower()
                    if not is_race:
                        new_miles = row['Miles'] * (1 + nonracer_factor)
                        new_miles = round(new_miles * 2) / 2
                        nonracer_days.at[idx, 'Miles'] = new_miles
        
        # Combine all adjusted days
        adjusted_rows.extend(shared_days.to_dict('records'))
        adjusted_rows.extend(racer_days.to_dict('records'))
        adjusted_rows.extend(nonracer_days.to_dict('records'))
    
    return pd.DataFrame(adjusted_rows)

def generate_week_schedule(week_data, output_dir='weekly_schedules'):
    """Generate week schedule CSV from overview data"""
    
    week_num = int(week_data.iloc[0]['Week'])
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"week{week_num:02d}.csv"
    
    days_full = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    groups = ['Gold', 'Green', 'White', 'Blue']
    
    # Get volume targets
    volumes = {
        'Gold': week_data.iloc[0]['Vol_Gold'],
        'Green': week_data.iloc[0]['Vol_Green'],
        'White': week_data.iloc[0]['Vol_White'],
        'Blue': week_data.iloc[0]['Vol_Blue']
    }
    
    # Build schedule from V and JV rows
    schedule = {'V': {}, 'JV': {}}
    groups_links = {}

    # Extract week-level notes (from V row)
    week_notes = ''
    for _, row in week_data.iterrows():
        squad = row.iloc[0]
        if squad == 'V' and 'Notes' in row and not pd.isna(row['Notes']):
            week_notes = str(row['Notes']).strip()
        for day in days_full:
            if day in row and not pd.isna(row[day]) and str(row[day]).strip():
                schedule[squad][day] = str(row[day]).strip()
            groups_col = f'{day}_Groups'
            if groups_col in row and not pd.isna(row[groups_col]) and str(row[groups_col]).strip():
                groups_links[day] = str(row[groups_col]).strip()

    # Determine split days
    split_days  = set(schedule['V'].keys()) & set(schedule['JV'].keys())
    v_only_days = set(schedule['V'].keys()) - split_days

    rows = []

    # ── New two-pass mileage distribution ────────────────────────────────────
    # For each group, build the full-week schedule dict and call
    # distribute_week_mileage once, so easy miles are calculated as the
    # residual after fixing workout / race / LR / rest mileages.
    group_mileages = {}   # group → {day → {'v': miles, 'jv': miles}}

    for group in groups:
        weekly_vol = volumes.get(group, 0)
        if pd.isna(weekly_vol):
            weekly_vol = 0

        # Build week_schedule dict for this group
        week_sched = {}
        for day_full in days_full:
            v_d  = schedule['V'].get(day_full,  '') or ''
            jv_d = schedule['JV'].get(day_full, '') if day_full in split_days else ''
            if v_d or jv_d:
                week_sched[day_full] = {'v': v_d, 'jv': jv_d}

        group_mileages[group] = distribute_week_mileage(week_sched, group, weekly_vol)
    # ─────────────────────────────────────────────────────────────────────────

    # Generate schedule rows
    for day_full in days_full:
        day_abbrev = DAY_ABBREV[day_full]
        if day_full not in schedule['V'] and day_full not in schedule['JV']:
            continue

        for group in groups:
            weekly_vol = volumes.get(group, 0)
            if pd.isna(weekly_vol):
                weekly_vol = 0

            day_miles = group_mileages.get(group, {}).get(day_full, {'v': 0.0, 'jv': 0.0})

            if day_full in split_days:
                # Racer workout (V) — scale canonical description for this group
                v_desc        = scale_workout_for_group(schedule['V'][day_full], group)
                miles         = day_miles['v']
                main_workout  = expand_workout_description(v_desc, group, miles)
                pre, post     = determine_pre_post(v_desc, day_full)
                rows.append({
                    'Week': week_num, 'Week_Start': week_start_date(week_num),
                    'Day': day_abbrev, 'Group': group, 'Status': 'Varsity',
                    'Pre': pre, 'Main_Workout': main_workout, 'Post': post,
                    'Miles': miles, 'Groups': groups_links.get(day_full, ''),
                    'Notes': week_notes if not rows else ''
                })

                # Non-Racer workout (JV)
                jv_desc       = scale_workout_for_group(schedule['JV'][day_full], group)
                jv_miles      = day_miles['jv']
                main_workout  = expand_workout_description(jv_desc, group, jv_miles)
                pre, post     = determine_pre_post(jv_desc, day_full)
                rows.append({
                    'Week': week_num, 'Week_Start': week_start_date(week_num),
                    'Day': day_abbrev, 'Group': group, 'Status': 'JV',
                    'Pre': pre, 'Main_Workout': main_workout, 'Post': post,
                    'Miles': jv_miles, 'Groups': groups_links.get(day_full, ''),
                    'Notes': ''
                })

            elif day_full in v_only_days:
                v_desc        = scale_workout_for_group(schedule['V'][day_full], group)
                miles         = day_miles['v']
                main_workout  = expand_workout_description(v_desc, group, miles)
                pre, post     = determine_pre_post(v_desc, day_full)
                rows.append({
                    'Week': week_num, 'Week_Start': week_start_date(week_num),
                    'Day': day_abbrev, 'Group': group, 'Status': '',
                    'Pre': pre, 'Main_Workout': main_workout, 'Post': post,
                    'Miles': miles, 'Groups': groups_links.get(day_full, ''),
                    'Notes': week_notes if not rows else ''
                })

    # Sort: day → group → status
    day_order    = {day: i for i, day in enumerate(DAY_ABBREV.values())}
    group_order  = {g: i for i, g in enumerate(groups)}
    status_order = {'': 0, 'JV': 1, 'Varsity': 2}

    df = pd.DataFrame(rows)
    if df.empty:
        print(f"  ⚠ Week {week_num} has no workouts - skipping")
        return None

    df['_day_ord']    = df['Day'].map(day_order)
    df['_group_ord']  = df['Group'].map(group_order)
    df['_status_ord'] = df['Status'].map(status_order)
    df = df.sort_values(['_day_ord', '_group_ord', '_status_ord'])
    df = df.drop(['_day_ord', '_group_ord', '_status_ord'], axis=1)

    df['Status'] = df['Status'].fillna('')
    df['Groups'] = df['Groups'].fillna('')
    df['Notes']  = df['Notes'].fillna('')

    df.to_csv(output_file, index=False, quoting=csv.QUOTE_MINIMAL, lineterminator='\r\n')
    print(f"✓ Created {output_file}")

    # Print mileage summary
    print(f"  Week {week_num} — mileage by group:")
    for group in groups:
        total = sum(v for d in group_mileages.get(group, {}).values() for v in [d['v']])
        target = volumes.get(group, 0)
        print(f"    {group}: {total:.1f} mi (target {target})")

    return output_file

def process_overview(overview_file, output_dir='weekly_schedules'):
    """Process training overview and generate week schedules"""
    
    print(f"\n{'='*70}")
    print(f"Training Overview to Week Schedule Converter")
    print(f"{'='*70}\n")
    
    # Load overview
    try:
        df = pd.read_csv(overview_file)
        print(f"✓ Loaded: {overview_file}")
    except Exception as e:
        print(f"✗ Error reading file: {e}")
        return
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    print(f"✓ Output directory: {output_path}\n")
    
    # Group by week
    weeks = sorted([w for w in df['Week'].unique() if not pd.isna(w)])
    print(f"Processing {len(weeks)} weeks...\n")
    
    for week_num in weeks:
        week_data = df[df['Week'] == week_num]
        generate_week_schedule(week_data, output_dir)
        print()
    
    print(f"{'='*70}")
    print(f"✓ Generated {len(weeks)} week schedule files")
    print(f"{'='*70}\n")

def main():
    # Auto-find the training overview CSV if no file specified
    if len(sys.argv) < 2:
        # Look for files matching pattern: *training*overview*.csv (case-insensitive)
        import glob
        pattern = '*[Tt]raining*[Oo]verview*.csv'
        matching_files = glob.glob(pattern)
        
        if len(matching_files) == 0:
            print("✗ Error: No training overview CSV file found.")
            print("  Looking for files matching: *training*overview*.csv")
            print("\nUsage: python overview_to_week_schedule.py [csv_file] [output_dir]")
            print("\nExample:")
            print("  python overview_to_week_schedule.py Training_Master_-_Training_Overview.csv")
            sys.exit(1)
        elif len(matching_files) == 1:
            overview_file = matching_files[0]
            print(f"📄 Auto-detected: {overview_file}")
        else:
            print(f"📄 Found {len(matching_files)} matching files:")
            for i, f in enumerate(matching_files, 1):
                print(f"   {i}. {f}")
            print(f"\n✓ Using: {matching_files[0]}")
            print("  (To use a different file, specify it as an argument)")
            overview_file = matching_files[0]
    else:
        overview_file = sys.argv[1]
    
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'weekly_schedules'
    
    if not Path(overview_file).exists():
        print(f"✗ Error: File not found: {overview_file}")
        sys.exit(1)
    
    process_overview(overview_file, output_dir)

if __name__ == '__main__':
    main()
