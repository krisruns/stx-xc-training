#!/usr/bin/env python3
"""
STX Training Groups Generator - mk8
Based on Jack Daniels 3rd Edition (Coach's custom chart)

WHAT'S NEW IN mk8:
- Updated CSV reader for new Athlete_Groups - Data.csv format (multi-header structure)
- Reads ALL current-season performance columns C-G:
    C: 800M (individual)
    D: 4x800 Split (relay — also treated as 800m, best of C/D used)
    E: 1600/Mile
    F: 3200/2 Mile
    G: 5000M (stored for reference; no VDOT lookup in current table)
- vdot_800 = best (highest) VDOT from individual 800m OR relay split
- vdot_max = highest VDOT across all three events (800/1600/3200)
- Verification CSV now shows all 5 source columns with per-column VDOTs
- Best_Event label distinguishes "800m (individual)" vs "800m (relay split)"

PRIOR HISTORY:
- mk7.1: Name normalization (apostrophe variants, whitespace)
- mk7:   Dual-constraint grouping (size + VDOT gap), gap-aware merging,
         smart unassigned placement (tier-based or interactive),
         back button + print-to-PDF in generated HTML

REQUIRED FILES (all in same directory as script):
- training_paces.csv          : VDOT lookup table
- Athlete_Groups - Data.csv   : Performance data for athletes with times
- Roster.csv                  : Full team roster (optional but recommended)
                                Add optional "Tier" column (Gold/Green/White/FR)
                                to enable tier-based unassigned placement

OUTPUTS:
- athlete_groups.html         : Training groups with VDOT toggle
- vdot_verification.csv       : VDOT calculations for verification
"""

import csv
import os
import unicodedata
import pandas as pd
from collections import defaultdict
from pathlib import Path


# ============================================================================
# Name Normalization
# ============================================================================

def normalize_name(name):
    """
    Normalize athlete names for consistent matching across CSV sources.
    Handles:
      - Curly/smart apostrophes vs straight apostrophes (e.g. O'Bryan vs O\u2019Bryan)
      - Extra or inconsistent whitespace
      - Unicode normalization (accented characters, etc.)
    """
    # Collapse all apostrophe/quote variants to straight apostrophe
    name = name.replace('\u2019', "'")  # right single quotation mark
    name = name.replace('\u2018', "'")  # left single quotation mark
    name = name.replace('\u02bc', "'")  # modifier letter apostrophe
    name = name.replace('\u0060', "'")  # grave accent (rare)
    # Unicode normalize
    name = unicodedata.normalize('NFC', name)
    # Collapse extra whitespace
    return ' '.join(name.split())


# ============================================================================
# VDOT Lookup Table Functions
# ============================================================================

def parse_time_to_seconds(time_str):
    """Convert time string to seconds. Handles M:SS, MM:SS, H:MM:SS formats."""
    if not time_str or time_str.strip() == '' or time_str == '-----':
        return None
    time_str = time_str.strip()
    parts = time_str.split(':')
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        else:
            return float(parts[0])
    except:
        return None


def load_vdot_table(csv_path, debug=False):
    """
    Load VDOT lookup table from CSV.

    Dynamically finds the VDOT column and the race-time columns (800m, Mile, 2mile)
    by scanning the header rows. Works regardless of how many preamble rows exist.
    """
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        lines = f.readlines()

    # Split every line into parts once
    rows = [line.strip().split(',') for line in lines]

    # ---- Find the VDOT header row ----
    vdot_col = None
    header_row_idx = None
    for i, parts in enumerate(rows):
        for j, cell in enumerate(parts):
            if cell.strip().upper() == 'VDOT':
                vdot_col = j
                header_row_idx = i
                break
        if header_row_idx is not None:
            break

    if header_row_idx is None:
        raise ValueError(f"Could not find 'VDOT' header in {csv_path}")

    header_parts = [p.strip().lower() for p in rows[header_row_idx]]
    if debug:
        print(f"\n   [DEBUG] VDOT header at row {header_row_idx}, col {vdot_col}")
        print(f"   [DEBUG] Header cells: {list(enumerate(header_parts))}")

    # ---- Auto-detect race-time columns ----
    # Search header row for 800m, mile, 2-mile by keyword
    col_800m = col_mile = col_2mile = None
    for j, cell in enumerate(header_parts):
        if col_800m  is None and '800' in cell:  col_800m  = j
        if col_mile  is None and cell == 'mile':  col_mile  = j
        if col_2mile is None and '2 mile' in cell or '2mile' in cell: col_2mile = j

    # Fallback: search a few rows below the header for sub-row labels
    # (e.g. a "Time / Pace" row that clarifies which column is which)
    if not all([col_800m, col_mile, col_2mile]):
        for i in range(header_row_idx + 1, min(header_row_idx + 4, len(rows))):
            sub = [p.strip().lower() for p in rows[i]]
            for j, cell in enumerate(sub):
                if col_800m  is None and '800' in cell:  col_800m  = j
                if col_mile  is None and cell == 'mile':  col_mile  = j
                if col_2mile is None and ('2 mile' in cell or '2mile' in cell): col_2mile = j

    # Hard fallback to known indices for this CSV layout
    if col_800m  is None: col_800m  = 6
    if col_mile  is None: col_mile  = 5
    if col_2mile is None: col_2mile = 3

    if debug:
        print(f"   [DEBUG] Column indices — 800m: {col_800m}, Mile: {col_mile}, 2mile: {col_2mile}")

    # ---- Read data rows ----
    # Skip any rows between header and first numeric VDOT row
    vdot_table = {}
    for parts in rows[header_row_idx + 1:]:
        if len(parts) <= vdot_col:
            continue
        try:
            vdot = int(parts[vdot_col].strip())
        except ValueError:
            continue  # sub-header or blank row
        try:
            vdot_table[vdot] = {
                '800m':  parse_time_to_seconds(parts[col_800m].strip()  if col_800m  < len(parts) else ''),
                '1600m': parse_time_to_seconds(parts[col_mile].strip()  if col_mile  < len(parts) else ''),
                '3200m': parse_time_to_seconds(parts[col_2mile].strip() if col_2mile < len(parts) else ''),
            }
        except Exception:
            continue

    if debug:
        sample = sorted(vdot_table.keys(), reverse=True)[:3]
        for v in sample:
            print(f"   [DEBUG] VDOT {v}: {vdot_table[v]}")

    if not vdot_table:
        raise ValueError(
            f"VDOT table loaded 0 entries from {csv_path}.\n"
            "Check that the file has a 'VDOT' column and race time columns (800m, Mile, 2 mile)."
        )

    print(f"   ✓ Loaded {len(vdot_table)} VDOT values "
          f"(range: {min(vdot_table)} – {max(vdot_table)})")
    if debug:
        print(f"   [DEBUG] 800m col {col_800m}, Mile col {col_mile}, 2mile col {col_2mile}")

    return {
        'vdot_to_times': vdot_table,
        'vdot_values': sorted(vdot_table.keys(), reverse=True)
    }


def find_closest_vdot(time_seconds, distance, vdot_table):
    """Find the VDOT that corresponds to the closest race time in the table."""
    if time_seconds is None:
        return None
    closest_vdot = None
    smallest_diff = float('inf')
    for vdot in vdot_table['vdot_values']:
        table_time = vdot_table['vdot_to_times'][vdot].get(distance)
        if table_time is None:
            continue
        diff = abs(table_time - time_seconds)
        if diff < smallest_diff:
            smallest_diff = diff
            closest_vdot = vdot
    return closest_vdot


# ============================================================================
# Roster / Data Loading
# ============================================================================

def read_roster(roster_path):
    """
    Read Roster.csv. Returns dict of {name: tier_or_None}.
    Handles "Athlete" column or "First"+"Last" columns.
    Optional "Tier" column (Gold/Green/White/FR) used for unassigned placement.
    """
    roster = {}
    with open(roster_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tier = row.get('Tier', '').strip() or None
            if 'First' in row and 'Last' in row:
                first = row['First'].strip()
                last  = row['Last'].strip()
                if first and last:
                    roster[normalize_name(f"{first} {last}")] = tier
            elif 'Athlete' in row and row['Athlete'].strip():
                roster[normalize_name(row['Athlete'].strip())] = tier
    return roster


def find_similar_names(name, name_list):
    """Return names from name_list that share the same last name."""
    similar = []
    parts = name.split()
    for candidate in name_list:
        cparts = candidate.split()
        if (len(parts) >= 2 and len(cparts) >= 2
                and parts[-1].lower() == cparts[-1].lower()
                and name.lower() != candidate.lower()):
            similar.append(candidate)
    return similar


def read_athlete_data(csv_path, vdot_table):
    """
    Read athlete performance data from the CSV and calculate VDOTs.

    Column discovery is fully dynamic — the function scans every row looking
    for a row that contains recognizable event labels ('800', '1600', 'mile',
    '3200', '2 mile', '5000'). Once found, it maps those labels to column
    positions and reads athlete data using those positions. This makes it
    immune to changes in the number of header rows, the presence or absence
    of a Grad Year column, or column ordering.

    800m VDOT: calculated for both the individual 800m column AND the relay
    split column; vdot_800 = the higher of the two.
    vdot_max:  highest VDOT across 800m, 1600m, and 3200m.
    """
    import pandas as pd

    # ---- Step 1: Read raw to discover column positions ----
    df_raw = pd.read_csv(csv_path, header=None, dtype=str)

    # Labels we search for in each event column (lowercase, partial match)
    # Each entry: (our_key, [substrings to match], is_relay_800)
    EVENT_SEARCH = [
        ('800m_current', ['800m', '800 m'],              False),
        ('800m_relay',   ['4x800', '4 x 800', 'split'],  False),
        ('1600m',        ['1600', 'mile'],                False),
        ('3200m',        ['3200', '2 mile', '2mile'],     False),
        ('5000m',        ['5000', '5k', '5 k'],           False),
    ]

    col_map = {}          # {our_key: column_index}
    athlete_start_row = 1 # row index (0-based) where athlete data begins

    for row_idx, row in df_raw.iterrows():
        row_vals = [str(v).strip().lower() for v in row]
        found_count = 0
        candidate_map = {}

        for our_key, keywords, _ in EVENT_SEARCH:
            for col_idx, cell in enumerate(row_vals):
                if any(kw in cell for kw in keywords):
                    if our_key not in candidate_map:  # first match wins
                        candidate_map[our_key] = col_idx
                        found_count += 1
                    break

        # Require at least 2 event labels to confirm this is the label row
        if found_count >= 2:
            col_map = candidate_map
            athlete_start_row = row_idx + 1
            break

    if not col_map:
        raise ValueError(
            f"Could not find event label row in {csv_path}.\n"
            "Expected a row containing labels like '800M', '1600/Mile', '3200/2 Mile'."
        )

    # Find the Athlete name column (first col containing 'athlete' or non-empty label in row 0)
    name_col = 0  # default
    header_row = [str(v).strip().lower() for v in df_raw.iloc[0]]
    for ci, val in enumerate(header_row):
        if 'athlete' in val or 'name' in val:
            name_col = ci
            break

    print(f"   ✓ Event columns found: { {k: v for k, v in col_map.items()} }")
    print(f"   ✓ Athlete name at col {name_col}, data starts at row {athlete_start_row}")

    # ---- Step 2: Read athlete rows ----
    def safe_cell(row, col_idx):
        """Return cleaned time string or '' for missing/invalid."""
        try:
            val = str(row.iloc[col_idx]).strip()
            return '' if val in ('nan', 'NaN', '-----', '', 'None') else val
        except IndexError:
            return ''

    athletes = []
    for _, row in df_raw.iloc[athlete_start_row:].iterrows():
        name_raw = safe_cell(row, name_col)
        if not name_raw:
            continue

        athlete = {
            'name':         normalize_name(name_raw),
            '800m_current': safe_cell(row, col_map.get('800m_current', -1)),
            '800m_relay':   safe_cell(row, col_map.get('800m_relay',   -1)),
            '1600m':        safe_cell(row, col_map.get('1600m',        -1)),
            '3200m':        safe_cell(row, col_map.get('3200m',        -1)),
            '5000m':        safe_cell(row, col_map.get('5000m',        -1)),
        }

        # ---- Step 3: VDOT lookups ----
        t800_ind   = parse_time_to_seconds(athlete['800m_current'])
        t800_relay = parse_time_to_seconds(athlete['800m_relay'])
        t1600      = parse_time_to_seconds(athlete['1600m'])
        t3200      = parse_time_to_seconds(athlete['3200m'])

        athlete['vdot_800_ind']   = find_closest_vdot(t800_ind,   '800m',  vdot_table)
        athlete['vdot_800_relay'] = find_closest_vdot(t800_relay, '800m',  vdot_table)
        athlete['vdot_1600']      = find_closest_vdot(t1600,      '1600m', vdot_table)
        athlete['vdot_3200']      = find_closest_vdot(t3200,      '3200m', vdot_table)

        vdots_800 = [v for v in [athlete['vdot_800_ind'], athlete['vdot_800_relay']] if v]
        athlete['vdot_800'] = max(vdots_800) if vdots_800 else None

        if (athlete['vdot_800_relay']
                and athlete['vdot_800_relay'] == athlete['vdot_800']
                and athlete['vdot_800_relay'] != athlete['vdot_800_ind']):
            athlete['vdot_800_source'] = 'relay'
        else:
            athlete['vdot_800_source'] = 'individual'

        all_vdots = [v for v in [athlete['vdot_800'], athlete['vdot_1600'], athlete['vdot_3200']] if v]
        athlete['vdot_max'] = max(all_vdots) if all_vdots else None

        athletes.append(athlete)

    return athletes


def export_vdot_verification(athletes, output_path):
    """Export VDOT calculations to CSV for verification."""
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = [
            'Athlete',
            '800M (Ind)', 'VDOT_800_Ind',
            '800M (Relay)', 'VDOT_800_Relay',
            'Best_800_VDOT',
            '1600/Mile', 'VDOT_1600',
            '3200/2Mile', 'VDOT_3200',
            '5000M',
            'VDOT_Max', 'Best_Event',
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for athlete in sorted(athletes, key=lambda a: a.get('vdot_max') or 0, reverse=True):
            vdot_max = athlete['vdot_max']
            best = ''
            if vdot_max:
                if athlete['vdot_800'] == vdot_max:
                    src = athlete.get('vdot_800_source', 'individual')
                    best = f"800m ({'relay split' if src == 'relay' else 'individual'})"
                elif athlete['vdot_1600'] == vdot_max:
                    best = '1600m'
                elif athlete['vdot_3200'] == vdot_max:
                    best = '3200m'

            writer.writerow({
                'Athlete':        athlete['name'],
                '800M (Ind)':     athlete['800m_current'] or '',
                'VDOT_800_Ind':   athlete['vdot_800_ind'] or '',
                '800M (Relay)':   athlete['800m_relay'] or '',
                'VDOT_800_Relay': athlete['vdot_800_relay'] or '',
                'Best_800_VDOT':  athlete['vdot_800'] or '',
                '1600/Mile':      athlete['1600m'] or '',
                'VDOT_1600':      athlete['vdot_1600'] or '',
                '3200/2Mile':     athlete['3200m'] or '',
                'VDOT_3200':      athlete['vdot_3200'] or '',
                '5000M':          athlete['5000m'] or '',
                'VDOT_Max':       athlete['vdot_max'] or '',
                'Best_Event':     best,
            })
    print(f"   ✓ VDOT verification CSV: {output_path}")


# ============================================================================
# Group Assignment — dual-constraint (size + VDOT gap)
# ============================================================================

def assign_groups(athletes, vdot_field='vdot_max',
                  group_size_min=4, group_size_max=8, max_vdot_gap=4):
    """
    Assign athletes to groups using two constraints:
      1. Size: close group when it reaches group_size_max
      2. Gap:  close group when next athlete's VDOT is more than max_vdot_gap
               below the group leader's VDOT

    Returns:
        groups       : {group_num: [athlete, ...]}
        close_reason : {group_num: 'size' | 'gap' | 'end'}
    """
    valid = [a for a in athletes if a.get(vdot_field) is not None]
    valid.sort(key=lambda a: a[vdot_field], reverse=True)

    groups = defaultdict(list)
    close_reason = {}
    current_group = 1

    for i, athlete in enumerate(valid):
        vdot = athlete[vdot_field]
        group = groups[current_group]

        if group:
            leader_vdot = group[0][vdot_field]
            gap = leader_vdot - vdot
            at_max_size = len(group) >= group_size_max

            if at_max_size or gap > max_vdot_gap:
                # Record why we closed the previous group
                close_reason[current_group] = 'size' if at_max_size else 'gap'
                current_group += 1
                group = groups[current_group]

        groups[current_group].append(athlete)

    close_reason[current_group] = 'end'

    # ---- Post-process: handle undersized trailing groups ----
    # Walk backwards and try to merge into the group above if:
    #   a) combined size still <= group_size_max, AND
    #   b) combined VDOT gap still <= max_vdot_gap
    # If both constraints can't be met, leave as-is and flag for review.
    group_keys = sorted(groups.keys())

    for gk in reversed(group_keys):
        grp = groups[gk]
        if len(grp) >= group_size_min:
            continue  # fine as-is

        if gk == 1:
            # Only one group exists or it's the first — can't merge upward
            if len(grp) < group_size_min:
                close_reason[gk] = 'small-solo'
            continue

        prev_gk = gk - 1
        prev_grp = groups[prev_gk]
        combined = prev_grp + grp
        combined_size_ok = len(combined) <= group_size_max
        combined_gap = prev_grp[0][vdot_field] - grp[-1][vdot_field]
        combined_gap_ok = combined_gap <= max_vdot_gap

        if combined_size_ok and combined_gap_ok:
            groups[prev_gk] = combined
            del groups[gk]
            close_reason[prev_gk] = close_reason.get(gk, 'end')
            if gk in close_reason:
                del close_reason[gk]
        else:
            # Can't merge cleanly — flag it
            close_reason[gk] = 'small-review'

    return dict(groups), close_reason


# ============================================================================
# Unassigned Athlete Placement
# ============================================================================

# Tier ordering for auto-placement (lower number = faster tier)
TIER_ORDER = {'gold': 1, 'green': 2, 'white': 3, 'fr': 4, 'freshman': 4}

def get_group_tier_profile(group_athletes, vdot_field):
    """Return the median VDOT and rough tier of a group."""
    vdots = [a[vdot_field] for a in group_athletes if a.get(vdot_field)]
    if not vdots:
        return None
    return sum(vdots) / len(vdots)


def place_unassigned_athletes(unassigned_roster, groups, close_reason, vdot_field,
                               group_size_max, max_vdot_gap, interactive=True):
    """
    Place athletes who have no performance data.

    Strategy (when interactive=False or tier is known):
      - If athlete has a Tier, find the group whose average VDOT best represents
        that tier, and append them there (flagged for review).
      - If no tier, fall back to interactive prompt or last group.

    Strategy (when interactive=True):
      - Show group summary and ask coach to assign each athlete.
    """
    group_keys = sorted(groups.keys())

    # Build a quick summary for prompts
    def group_summary(gk):
        grp = groups[gk]
        vdots = [a[vdot_field] for a in grp if a.get(vdot_field)]
        if vdots:
            return f"Group {gk} (VDOT {max(vdots)}-{min(vdots)}, {len(grp)} athletes)"
        return f"Group {gk} ({len(grp)} athletes, no VDOT data)"

    # Tier → typical VDOT midpoint heuristics (adjust to your team)
    TIER_VDOT_TARGET = {'gold': 67, 'green': 60, 'white': 53, 'fr': 50, 'freshman': 50}

    # Pre-compute group avg VDOTs
    group_avg_vdot = {}
    for gk in group_keys:
        avg = get_group_tier_profile(groups[gk], vdot_field)
        if avg:
            group_avg_vdot[gk] = avg

    placed = []  # (name, target_group_key)

    for name, tier in sorted(unassigned_roster.items()):
        tier_key = tier.lower() if tier else None
        target_gk = None

        # Try tier-based auto-assignment
        if tier_key and tier_key in TIER_VDOT_TARGET and group_avg_vdot:
            target_vdot = TIER_VDOT_TARGET[tier_key]
            target_gk = min(group_avg_vdot.keys(),
                            key=lambda gk: abs(group_avg_vdot[gk] - target_vdot))

        if interactive:
            # Always show a prompt — pre-select tier suggestion if available
            print(f"\n   👤 {name}" + (f"  [Tier: {tier}]" if tier else "  [No tier]"))
            print(f"      Available groups:")
            for gk in group_keys:
                marker = " ◀ suggested" if gk == target_gk else ""
                print(f"        {gk}. {group_summary(gk)}{marker}")
            print(f"        U. Leave unassigned (review later)")

            default = str(target_gk) if target_gk else 'U'
            raw = input(f"      Assign to group [{default}]: ").strip()
            if not raw:
                raw = default

            if raw.upper() == 'U':
                target_gk = None
            else:
                try:
                    target_gk = int(raw)
                    if target_gk not in groups:
                        print(f"      ⚠️  Invalid group, leaving unassigned.")
                        target_gk = None
                except ValueError:
                    print(f"      ⚠️  Invalid input, leaving unassigned.")
                    target_gk = None

        placed.append((name, tier, target_gk))

    # Apply placements
    unassigned_group_key = (max(groups.keys()) + 1) if groups else 1
    groups[unassigned_group_key] = []

    for name, tier, target_gk in placed:
        entry = {
            'name': name,
            'unassigned': True,
            'tier': tier,
            'vdot_800': None, 'vdot_800_ind': None, 'vdot_800_relay': None,
            'vdot_800_source': None,
            'vdot_1600': None, 'vdot_3200': None, 'vdot_max': None,
            '800m_current': '', '800m_relay': '', '1600m': '', '3200m': '', '5000m': '',
        }
        if target_gk is not None:
            groups[target_gk].append(entry)
            print(f"   ✓ {name} → Group {target_gk}" + (f" (via tier: {tier})" if tier else ""))
        else:
            groups[unassigned_group_key].append(entry)

    # Clean up empty unassigned bucket
    if not groups[unassigned_group_key]:
        del groups[unassigned_group_key]
    else:
        close_reason[unassigned_group_key] = 'unassigned'

    return groups, close_reason


# ============================================================================
# HTML Generation
# ============================================================================

CLOSE_REASON_LABELS = {
    'size':         '⚡ closed: size limit',
    'gap':          '📏 closed: VDOT gap',
    'end':          '',
    'small-review': '⚠️  small group — review',
    'small-solo':   '⚠️  small group — review',
    'unassigned':   '📋 needs performance data',
}

def generate_html(groups, close_reason, output_path, vdot_field='vdot_max'):
    """Generate HTML file with athlete groups."""
    sorted_groups = sorted(groups.items())

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>STX Training Groups</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        h1 {
            text-align: center;
            color: #003366;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 3px solid #003366;
        }
        .controls {
            text-align: center;
            margin: 20px 0 30px 0;
            padding: 15px;
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 8px;
        }
        .vdot-toggle-btn {
            padding: 10px 20px;
            background: #003366;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .vdot-toggle-btn:hover { background: #004488; transform: translateY(-2px); }
        .vdot-info { margin-top: 8px; font-size: 0.85rem; color: #666; }
        .groups-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .group-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .group-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .group-card.review-needed { border-left: 4px solid #e67e22; }
        .group-card.unassigned-card { border-left: 4px solid #e74c3c; background: #fff9f9; }
        .group-header {
            font-size: 1.4em;
            font-weight: bold;
            color: #003366;
            margin-bottom: 4px;
        }
        .group-meta {
            font-size: 0.8em;
            color: #888;
            margin-bottom: 12px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 4px;
        }
        .vdot-range {
            background: #e3f2fd;
            color: #1565c0;
            padding: 2px 8px;
            border-radius: 10px;
            font-weight: 600;
            font-size: 0.85em;
        }
        .close-reason {
            font-size: 0.78em;
            color: #999;
            font-style: italic;
        }
        .close-reason.gap-close    { color: #e67e22; font-weight: 600; }
        .close-reason.review-close { color: #e74c3c; font-weight: 600; }
        .athlete-list { list-style: none; padding: 0; margin: 0; }
        .athlete-list li {
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
            color: #555;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .athlete-list li:last-child { border-bottom: none; }
        .athlete-list li:hover { color: #003366; background-color: #f8f8f8; padding-left: 5px; transition: all 0.2s; }
        .athlete-name { font-weight: 500; }
        .vdot-value {
            display: none;
            padding: 2px 8px;
            background: #e3f2fd;
            color: #1976d2;
            border-radius: 12px;
            font-size: 0.82em;
            font-weight: 600;
        }
        .vdot-value.show { display: inline-block; }
        .no-data-badge {
            font-size: 0.75em;
            background: #fce4ec;
            color: #c62828;
            padding: 2px 7px;
            border-radius: 10px;
            font-style: italic;
        }
        .tier-badge {
            font-size: 0.73em;
            background: #f3e5f5;
            color: #6a1b9a;
            padding: 2px 7px;
            border-radius: 10px;
        }
        @media (max-width: 768px) {
            body { padding: 10px; }
            .groups-container { grid-template-columns: 1fr; }
            h1 { font-size: 1.5em; }
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #777;
            font-size: 0.9em;
        }
        .btn-row {
            display: flex;
            justify-content: center;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 12px;
        }
        .back-btn {
            padding: 10px 20px;
            background: #555;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            transition: all 0.2s;
        }
        .back-btn:hover { background: #333; transform: translateY(-2px); }
        .print-btn {
            padding: 10px 20px;
            background: #2e7d32;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .print-btn:hover { background: #1b5e20; transform: translateY(-2px); }

        /* ---- Print styles ---- */
        @media print {
            body { background: white; padding: 0; max-width: 100%; }
            .controls { display: none !important; }
            .footer { display: none; }
            h1 { font-size: 1.4em; border-bottom: 2px solid #003366; margin-bottom: 12px; }
            .groups-container {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 12px;
                margin-top: 12px;
            }
            .group-card {
                box-shadow: none;
                border: 1px solid #ccc;
                padding: 12px;
                break-inside: avoid;
            }
            .group-card:hover { transform: none; box-shadow: none; }
            .vdot-value { display: inline-block !important; }
            .athlete-list li { padding: 4px 0; }
            .group-header { font-size: 1.1em; }
        }
    </style>
</head>
<body>
    <h1>St. Xavier Training Groups</h1>

    <div class="controls">
        <div class="btn-row">
            <a href="index.html" class="back-btn">← Week View</a>
            <button class="vdot-toggle-btn" onclick="toggleVDOT()">Show VDOT Values</button>
            <button class="print-btn" onclick="printGroups()">🖨 Print to PDF</button>
        </div>
        <div class="vdot-info">
            <span style="color:#e67e22;font-weight:600;">Orange border</span> = small group, review recommended &nbsp;|&nbsp;
            <span style="color:#e74c3c;font-weight:600;">Red border</span> = needs performance data
        </div>
    </div>

    <div class="groups-container">
"""

    for group_num, athletes in sorted_groups:
        is_unassigned_bucket = all(a.get('unassigned') for a in athletes)
        needs_review = close_reason.get(group_num) in ('small-review', 'small-solo')
        reason_label = CLOSE_REASON_LABELS.get(close_reason.get(group_num, 'end'), '')

        # VDOT range for this group
        vdots = [a[vdot_field] for a in athletes if a.get(vdot_field)]
        vdot_range_html = ''
        if vdots:
            if max(vdots) == min(vdots):
                vdot_range_html = f'<span class="vdot-range">VDOT {max(vdots)}</span>'
            else:
                vdot_range_html = f'<span class="vdot-range">VDOT {max(vdots)}–{min(vdots)}</span>'

        # Reason CSS class
        if close_reason.get(group_num) == 'gap':
            reason_css = 'gap-close'
        elif close_reason.get(group_num) in ('small-review', 'small-solo', 'unassigned'):
            reason_css = 'review-close'
        else:
            reason_css = ''

        card_class = 'group-card'
        if is_unassigned_bucket:
            card_class += ' unassigned-card'
        elif needs_review:
            card_class += ' review-needed'

        group_label = f"Group {group_num}"
        if is_unassigned_bucket:
            group_label += " — Unassigned"

        html += f"""        <div class="{card_class}">
            <div class="group-header">{group_label}</div>
            <div class="group-meta">
                <span>{len(athletes)} athletes &nbsp; {vdot_range_html}</span>
                <span class="close-reason {reason_css}">{reason_label}</span>
            </div>
            <ul class="athlete-list">
"""
        # Sort: athletes with data by VDOT desc, unassigned alphabetically at bottom
        has_data = sorted([a for a in athletes if a.get(vdot_field)],
                          key=lambda a: a[vdot_field], reverse=True)
        no_data  = sorted([a for a in athletes if not a.get(vdot_field)],
                          key=lambda a: a['name'])

        for athlete in has_data + no_data:
            name  = athlete['name']
            vdot  = athlete.get(vdot_field)
            is_ua = athlete.get('unassigned', False)
            tier  = athlete.get('tier', '')

            tier_html = f'<span class="tier-badge">{tier}</span>' if tier else ''

            if is_ua:
                html += f"""                <li>
                    <span class="athlete-name">{name} {tier_html}</span>
                    <span class="no-data-badge">needs data</span>
                </li>
"""
            else:
                vdot_display = f'VDOT {vdot}' if vdot else 'No VDOT'
                html += f"""                <li>
                    <span class="athlete-name">{name}</span>
                    <span class="vdot-value">{vdot_display}</span>
                </li>
"""

        html += """            </ul>
        </div>
"""

    html += """    </div>

    <div class="footer">St. Xavier High School Cross Country &amp; Track</div>

    <script>
        function toggleVDOT() {
            const els = document.querySelectorAll('.vdot-value');
            const btn = document.querySelector('.vdot-toggle-btn');
            const showing = els[0] && els[0].classList.contains('show');
            els.forEach(el => el.classList.toggle('show'));
            btn.textContent = showing ? 'Show VDOT Values' : 'Hide VDOT Values';
        }

        function printGroups() {
            // Show all VDOT values before printing so they appear on the PDF
            document.querySelectorAll('.vdot-value').forEach(el => el.classList.add('show'));
            window.print();
            // Restore hidden state after print dialog closes
            document.querySelectorAll('.vdot-value').forEach(el => el.classList.remove('show'));
        }
    </script>
</body>
</html>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


# ============================================================================
# Interactive Main
# ============================================================================

def prompt_int(prompt_text, default):
    raw = input(prompt_text).strip()
    try:
        return int(raw) if raw else default
    except ValueError:
        print(f"   Invalid input — using default ({default})")
        return default


def main():
    script_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()

    VDOT_TABLE_PATH = script_dir / 'training_paces.csv'
    CSV_PATH        = script_dir / 'Athlete_Groups - Data.csv'
    ROSTER_PATH     = script_dir / 'Roster.csv'
    OUTPUT_PATH     = script_dir / 'athlete_groups.html'
    VDOT_CSV_PATH   = script_dir / 'vdot_verification.csv'

    print("\n" + "=" * 70)
    print("STX TRAINING GROUPS GENERATOR  —  mk8")
    print("Using Jack Daniels 3rd Edition VDOT Table")
    print("=" * 70)
    print(f"\n📂 Script directory: {script_dir.absolute()}")

    # Load VDOT table
    print("\n📊 Loading VDOT lookup table...")
    vdot_table = load_vdot_table(str(VDOT_TABLE_PATH), debug=True)
    print(f"   ✓ Loaded {len(vdot_table['vdot_values'])} VDOT values")

    # Load roster
    print("\n📋 Checking for Roster.csv...")
    roster = {}  # {name: tier_or_None}
    if ROSTER_PATH.exists():
        roster = read_roster(str(ROSTER_PATH))
        has_tiers = any(v for v in roster.values())
        print(f"   ✓ Loaded {len(roster)} athletes from roster"
              + (" (includes Tier data)" if has_tiers else " (no Tier column found)"))
        if not has_tiers:
            print("   💡 Add a 'Tier' column (Gold/Green/White/FR) to Roster.csv")
            print("      for smarter auto-placement of unassigned athletes.")
    else:
        print("   ⚠️  Roster.csv not found — unassigned athlete check will be skipped.")

    # Group size / gap config
    print("\n👥 Group Configuration")
    group_size_min = prompt_int("   Minimum athletes per group [default: 4]: ", 4)
    group_size_max = prompt_int("   Maximum athletes per group [default: 8]: ", 8)
    max_vdot_gap   = prompt_int("   Maximum VDOT gap within a group [default: 4]: ", 4)
    print(f"   ✓ Groups: {group_size_min}–{group_size_max} athletes, max gap: {max_vdot_gap} VDOT points")

    # VDOT source for grouping
    print("\n🎯 Which race performance should determine VDOT for grouping?")
    print("  1. ALL    - Use highest VDOT across all events (default)")
    print("  2. 800    - Use best 800m (individual or relay split, whichever is higher)")
    print("  3. 1600   - Use 1600m/mile performance only")
    print("  4. 3200   - Use 3200m/2-mile performance only")
    choice = input("\nEnter choice (1-4) [default: 1]: ").strip() or '1'
    vdot_choice_map = {
        '1': ('ALL',   'vdot_max'),
        '2': ('800m',  'vdot_800'),
        '3': ('1600m', 'vdot_1600'),
        '4': ('3200m', 'vdot_3200'),
    }
    if choice not in vdot_choice_map:
        print("   Invalid choice — using ALL.")
        choice = '1'
    choice_name, vdot_field = vdot_choice_map[choice]
    print(f"   ✓ Using {choice_name} performance for grouping")

    # Unassigned placement mode
    interactive_placement = True
    if roster:
        has_tiers = any(v for v in roster.values())
        if has_tiers:
            print("\n🔀 Unassigned athlete placement")
            print("  1. Interactive — prompt for each athlete (default)")
            print("  2. Auto        — use Tier column to suggest placement (no prompts)")
            ua_choice = input("\nEnter choice (1-2) [default: 1]: ").strip()
            interactive_placement = (ua_choice != '2')
            if not interactive_placement:
                print("   ✓ Auto-placement enabled (tier-based suggestions)")

    print("\n" + "=" * 70)

    # Process athlete data
    print(f"\n📊 Reading athlete performance data...")
    athletes = read_athlete_data(str(CSV_PATH), vdot_table)
    print(f"   ✓ {len(athletes)} athletes with performance data")

    # VDOT verification export
    print(f"\n📋 Exporting VDOT verification CSV...")
    export_vdot_verification(athletes, str(VDOT_CSV_PATH))

    # Top 10 preview
    print(f"\n📈 Top 10 by {choice_name} VDOT:")
    for i, a in enumerate(sorted(athletes, key=lambda a: a.get(vdot_field) or 0, reverse=True)[:10], 1):
        v = a.get(vdot_field)
        if v:
            t = ''
            if vdot_field in ('vdot_max', 'vdot_800') and a['vdot_800'] == v:
                src = a.get('vdot_800_source', 'individual')
                time_val = a['800m_relay'] if src == 'relay' else a['800m_current']
                label = 'relay split' if src == 'relay' else '800m ind'
                if time_val:
                    t = f"({time_val} {label})"
            elif vdot_field in ('vdot_max', 'vdot_1600') and a.get('vdot_1600') == v and a['1600m']:
                t = f"({a['1600m']} 1600m)"
            elif vdot_field in ('vdot_max', 'vdot_3200') and a.get('vdot_3200') == v and a['3200m']:
                t = f"({a['3200m']} 3200m)"
            elif vdot_field == 'vdot_1600' and a['1600m']:
                t = f"({a['1600m']})"
            elif vdot_field == 'vdot_3200' and a['3200m']:
                t = f"({a['3200m']})"
            print(f"   {i:2}. {a['name']:25} VDOT: {v:2}  {t}")

    # Assign groups
    print(f"\n👥 Creating groups (size {group_size_min}–{group_size_max}, max gap {max_vdot_gap})...")
    groups, close_reason = assign_groups(
        athletes, vdot_field, group_size_min, group_size_max, max_vdot_gap
    )

    # Roster check — find unassigned athletes
    if roster:
        print(f"\n🔍 Checking roster for unassigned athletes...")
        assigned_names = {a['name'] for grp in groups.values() for a in grp}

        # Name mismatch warnings
        data_not_in_roster = assigned_names - set(roster.keys())
        if data_not_in_roster:
            print(f"\n   ⚠️  {len(data_not_in_roster)} athletes in data file don't exactly match roster:")
            for name in sorted(data_not_in_roster):
                similar = find_similar_names(name, list(roster.keys()))
                if similar:
                    print(f"      • '{name}' — did you mean '{similar[0]}'?")
                else:
                    print(f"      • '{name}' (not found in roster)")

        # Unassigned athletes
        unassigned_roster = {n: t for n, t in roster.items() if n not in assigned_names}

        if unassigned_roster:
            print(f"\n   📋 {len(unassigned_roster)} roster athletes have no performance data.")
            if interactive_placement:
                print("   Prompting for group assignment (Enter to accept suggestion, U = leave unassigned):")
            else:
                print("   Auto-assigning based on Tier...")
            groups, close_reason = place_unassigned_athletes(
                unassigned_roster, groups, close_reason, vdot_field,
                group_size_max, max_vdot_gap, interactive=interactive_placement
            )
        else:
            print("   ✓ All roster athletes have performance data")
    else:
        print("\n   ℹ️  Roster check skipped (Roster.csv not found)")

    # Generate HTML
    print(f"\n📝 Generating HTML...")
    generate_html(groups, close_reason, str(OUTPUT_PATH), vdot_field)

    # Terminal summary
    print(f"\n{'=' * 70}")
    print("GROUP SUMMARY")
    print(f"{'=' * 70}")
    for gk in sorted(groups.keys()):
        grp = groups[gk]
        vdots = [a[vdot_field] for a in grp if a.get(vdot_field)]
        reason = close_reason.get(gk, 'end')
        reason_str = {
            'size':         '(closed: size limit)',
            'gap':          '(closed: VDOT gap ⚠️)',
            'end':          '',
            'small-review': '(⚠️  SMALL — review recommended)',
            'small-solo':   '(⚠️  SMALL — review recommended)',
            'unassigned':   '(needs performance data)',
        }.get(reason, '')

        is_ua = all(a.get('unassigned') for a in grp)
        label = f"Group {gk}" + (" [Unassigned]" if is_ua else "")

        if vdots:
            vdot_range = f"VDOT {max(vdots)}–{min(vdots)}, spread: {max(vdots)-min(vdots)}"
        else:
            vdot_range = "no VDOT data"

        print(f"  {label}: {len(grp)} athletes  |  {vdot_range}  {reason_str}")

    print(f"\n✅ Complete!")
    print(f"   HTML:  {OUTPUT_PATH}")
    print(f"   CSV:   {VDOT_CSV_PATH}")
    print(f"\n💡 TIP: Open HTML and click 'Show VDOT Values' to verify assignments.")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
