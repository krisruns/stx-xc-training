#!/usr/bin/env python3
"""
STX Archive to Training Overview CSV
Reads week HTML files and produces a Training_Overview CSV ready for the pipeline.

Usage:
    python archive_to_overview.py --start 1 --end 23 --input ./weeks --output Training_Overview_XC2025.csv

Notes:
    - Uses Gold group's RUN as the canonical V workout description
    - Simplifies verbose descriptions to pipeline-compatible keywords
    - Rows marked ⚠️ in the Review column need manual cleanup before running the pipeline
    - V/JV split days produce two rows per week (V + JV)
"""

import argparse
import re
import csv
import sys
from pathlib import Path
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# ─── WORKOUT SIMPLIFICATION ────────────────────────────────────────────────────

def simplify_workout(raw, debug=False):
    """
    Convert verbose HTML workout description to pipeline-compatible canonical form.
    Returns (simplified, needs_review).
    needs_review=True means the user should manually check this entry.
    """
    if not raw or not raw.strip():
        return '', False

    text = raw.strip()
    lo   = text.lower()

    # REST / OFF
    if lo in ('rest', 'off', 'rest day') or lo.startswith('rest'):
        return 'Rest', False

    # RACE
    if lo.startswith('race') or lo == 'race':
        return 'Race', False
    if re.match(r'^race\b', lo):
        return 'Race', False

    # LONG RUN PROGRESSION
    if ('long run' in lo or re.search(r'\blr\b', lo)) and 'progression' in lo:
        return 'LR - Progression', False

    # LONG RUN
    if 'long run' in lo or re.search(r'\blr\b', lo):
        return 'Long Run', False

    # HILLS
    if 'hill' in lo:
        # Try to preserve duration hint if present e.g. "Hills 35min"
        m = re.search(r'(\d+)\s*min', lo)
        if m:
            return f"Hills {m.group(1)}min", False
        return 'Hills', False

    # FARTLEK — extract rep structure
    if 'fartlek' in lo:
        # Pattern: "N x [Xmin on/Ymin off]" or "5-4-3-2-1" or "Nx[Xmin/Ymin]"
        # Try bracket style: "6 x [3min on/2min steady]"
        m = re.search(r'(\d+)\s*[x×]\s*\[([^\]]+)\]', text, re.I)
        if m:
            return f"Fartlek {m.group(1)}x[{m.group(2).strip()}]", False
        # Plain N x (time on / time off)
        m = re.search(r'(\d+)\s*[x×]\s*[\[(]([^)\]]+)[\])]', text, re.I)
        if m:
            return f"Fartlek {m.group(1)}x({m.group(2).strip()})", False
        # Descending ladder like 5-4-3-2-1
        m = re.search(r'(\d+-\d+-\d+(?:-\d+)*)', text)
        if m:
            return f"Fartlek {m.group(1)}", False
        # Fallback: keep "Fartlek" keyword so pipeline catches it
        return 'Fartlek', True   # flag for manual refinement

    # PRE TEMPO workouts (pre 30, pre 40, etc.)
    if re.search(r'\bpre\s*(30|40|tempo)\b', lo):
        m = re.search(r'pre\s*(\d+)', lo)
        if m:
            return f"Pre {m.group(1)}", False
        return 'Pre Tempo', False

    # TEMPO
    if 'tempo' in lo:
        return 'Tempo', True

    # EASY — also catches "Xmi easy", "easy miles", surges embedded in easy run
    if 'easy' in lo:
        return 'easy', False

    # SPECIFIC INTERVALS — e.g. "12x200@800 (30s)", "4x[3x300@mile]"
    # These pass through as-is but are flagged for review since the pipeline
    # can't expand group-specific reps automatically
    if re.search(r'\d+x[\d\[\(]', lo) or re.search(r'\d+\s*@\s*\d', lo):
        # Try to clean up a bit — strip leading/trailing filler
        clean = re.sub(r'^(gold|green|white|freshman)[:\s]+', '', text, flags=re.I)
        clean = re.sub(r'\s*(total[:\s].+)$', '', clean, flags=re.I)
        return clean.strip(), True

    # TIME TRIAL
    if 'time trial' in lo or re.search(r'\btt\b', lo):
        return 'Time Trial', False

    # PROGRESSION (standalone, not long run)
    if 'progression' in lo:
        return 'Progression', False

    # WORKOUT (catch-all for structured workouts)
    if 'workout' in lo or 'interval' in lo:
        return text.strip(), True

    # Anything else — pass through flagged
    return text.strip(), True


STRUCTURED_KEYWORDS = ('fartlek', 'hill', 'interval', 'tempo', 'pre', '@', 'x[', 'x(', 'x[', 'stride')

def needs_groups_page(gold_desc, freshman_desc):
    """
    Return True only for structured workouts that genuinely need per-group pace pages.
    Easy runs with different mileage do NOT need a groups page.
    """
    if not gold_desc:
        return False
    lo_g = gold_desc.lower()

    # Structured workout keywords — these always get a groups page
    for kw in STRUCTURED_KEYWORDS:
        if kw in lo_g:
            return True

    # Interval notation: Nx400, 3x[...], etc.
    if re.search(r'\d+\s*[x×]\s*[\[\d(]', lo_g):
        return True

    # Explicitly different workout types between groups (V/JV split)
    if freshman_desc:
        lo_f = freshman_desc.lower()
        # Both easy → no groups page (different mileage is handled by pipeline)
        if 'easy' in lo_g and 'easy' in lo_f:
            return False
        # Both race/rest → no groups page
        if lo_g in ('race', 'rest') and lo_f in ('race', 'rest'):
            return False
        # Different workout types → groups page
        if lo_g.split()[0] != lo_f.split()[0]:
            return True

    return False


# ─── DATE UTILITIES ────────────────────────────────────────────────────────────

MONTHS = {
    'january':1,'february':2,'march':3,'april':4,'may':5,'june':6,
    'july':7,'august':8,'september':9,'october':10,'november':11,'december':12
}

def parse_month_day(text, ref_year=2025):
    """Extract a datetime from text like 'MONDAY, JUNE 30' or 'June 30, 2025'."""
    m = re.search(
        r'(january|february|march|april|may|june|july|august|september|october|november|december)'
        r'\s+(\d{1,2})(?:,?\s*(\d{4}))?',
        text, re.I
    )
    if m:
        mon  = MONTHS[m.group(1).lower()]
        day  = int(m.group(2))
        year = int(m.group(3)) if m.group(3) else ref_year
        try:
            return datetime(year, mon, day)
        except ValueError:
            return None
    return None


def find_monday(data, ref_year=2025):
    """
    Find the Monday date for a parsed week.
    Tries day titles first, then the H1/title text.
    """
    for day in data['days']:
        d = parse_month_day(day.get('raw_title', ''), ref_year)
        if d:
            return d - timedelta(days=d.weekday())

    # Fallback: try title/h1 which often has "May 18 - 24, 2026"
    for key in ('title_text', 'date_range_text'):
        txt = data.get(key, '')
        d = parse_month_day(txt, ref_year)
        if d:
            return d - timedelta(days=d.weekday())
    return None


def format_beginning_date(monday):
    """Format as M/D (no leading zeros), e.g. '6/30'."""
    if not monday:
        return ''
    return f"{monday.month}/{monday.day}"


# ─── PARSERS ──────────────────────────────────────────────────────────────────

def clean(el):
    if el is None:
        return ''
    for a in el.find_all('a'):
        a.decompose()
    return re.sub(r'\s+', ' ', el.get_text(separator=' ', strip=True)).strip()


def detect_format(soup):
    if soup.find('div', class_='day-section'):
        return 'old'
    if soup.find('div', class_='workout-item'):
        return 'new'
    return 'old'


def extract_miles_float(text):
    """Parse '46 miles' or '46.0' → 46.0, or None."""
    m = re.search(r'(\d+\.?\d*)', str(text))
    return float(m.group(1)) if m else None


def parse_old_format(soup, week_num):
    """Parse week06-style HTML. Returns structured week dict."""
    data = {
        'week': week_num, 'title_text': '', 'date_range_text': '',
        'days': [], 'totals': {}, 'notes': [], 'highlight': ''
    }

    h1 = soup.find('h1')
    if h1:
        data['title_text'] = clean(h1)
    hdr = soup.find('div', class_='header')
    if hdr:
        p = hdr.find('p')
        if p:
            data['date_range_text'] = clean(p)
    hl = soup.find('div', class_='week-highlight')
    if hl:
        data['highlight'] = clean(hl)

    # Totals
    tots = soup.find('div', class_='totals-section')
    if tots:
        for item in tots.find_all('div', class_='total-item'):
            g = item.find('div', class_='total-group')
            m = item.find('div', class_='total-miles')
            if g and m:
                data['totals'][clean(g).title()] = clean(m)

    # Notes
    notes_sec = soup.find('div', class_='notes-section')
    if notes_sec:
        for li in notes_sec.find_all('li'):
            data['notes'].append(clean(li))

    # Days
    DAY_NAMES = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']
    for day_div in soup.find_all('div', class_='day-section'):
        day = {'name': '', 'raw_title': '', 'groups': {}, 'has_vjv': False}
        title_el = day_div.find('div', class_='day-title')
        if title_el:
            raw = re.sub(r'[\U00010000-\U0010ffff📱🎯]+', '', clean(title_el)).strip()
            day['raw_title'] = raw
            # Extract day name
            for dn in DAY_NAMES:
                if dn in raw.lower():
                    day['name'] = dn.capitalize()
                    break

        gc = day_div.find('div', class_='groups-container') or day_div
        for grp_div in gc.find_all('div', class_='group'):
            name_el = grp_div.find('div', class_='group-name')
            grp_name = clean(name_el).title() if name_el else 'Unknown'

            grp = {'pre': '', 'run': '', 'post': '', 'status': ''}
            for ws in grp_div.find_all('div', class_='workout-section'):
                lbl_el = ws.find('div', class_='workout-label')
                lbl = clean(lbl_el).upper().rstrip(':') if lbl_el else ''
                cnt = ws.find('div', class_='workout-content')
                if cnt:
                    for a in cnt.find_all('a'): a.decompose()
                    main_el   = cnt.find('div', class_='workout-main')
                    detail_el = cnt.find('div', class_='workout-details')
                    parts = []
                    if main_el:
                        t = clean(main_el)
                        if t: parts.append(t)
                    if detail_el:
                        t = clean(detail_el)
                        if t: parts.append(t)
                    text = ' '.join(parts)
                else:
                    text = ''
                if 'PRE' in lbl:
                    grp['pre'] = text
                elif 'RUN' in lbl:
                    grp['run'] = text
                elif 'POST' in lbl:
                    grp['post'] = text

            day['groups'][grp_name] = grp

        data['days'].append(day)
    return data


def parse_new_format(soup, week_num):
    """Parse week52-style HTML. Returns same structured dict."""
    data = {
        'week': week_num, 'title_text': '', 'date_range_text': '',
        'days': [], 'totals': {}, 'notes': [], 'highlight': ''
    }

    h1 = soup.find('h1')
    if h1:
        data['title_text'] = clean(h1)

    # Totals
    tots = soup.find('div', class_='totals')
    if tots:
        for item in tots.find_all('div', class_='total'):
            lbl = item.find('div', class_='total-label')
            mi  = item.find('div', class_='total-miles')
            if lbl and mi:
                data['totals'][clean(lbl).title()] = clean(mi)

    # Notes
    notes_div = soup.find('div', class_='week-notes')
    if notes_div:
        for li in notes_div.find_all('li'):
            data['notes'].append(clean(li))

    DAY_NAMES = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday']
    for day_div in soup.find_all('div', class_='day'):
        day = {'name': '', 'raw_title': '', 'groups': {}, 'has_vjv': False}
        hdr = day_div.find('div', class_='day-header')
        if hdr:
            raw = re.sub(r'[\U00010000-\U0010ffff📱🎯←]+', '', hdr.get_text(separator=' ',strip=True))
            raw = re.sub(r'(Groups|Workout Paces|Schedule)', '', raw).strip()
            day['raw_title'] = raw
            for dn in DAY_NAMES:
                if dn in raw.lower():
                    day['name'] = dn.capitalize()
                    break

        # Collect per-group workouts; detect V/JV split
        group_map = {}   # group_name -> {'V': ..., 'JV': ...}
        for section in day_div.find_all('div', class_='section'):
            sec_lbl_el = section.find('div', class_='section-label')
            sec_lbl = clean(sec_lbl_el).upper() if sec_lbl_el else 'WORKOUT'

            for item in section.find_all('div', class_='workout-item'):
                grp_name = item.get('data-group', '').strip()
                if not grp_name:
                    continue
                for a in item.find_all('a'): a.decompose()
                desc_el  = item.find('div', class_='workout-desc')
                miles_el = item.find('div', class_='workout-miles')
                desc  = clean(desc_el)
                miles = clean(miles_el)

                # Detect status from class list (varsity / jv)
                classes = item.get('class', [])
                status = ''
                if any('varsity' in c.lower() for c in classes):
                    status = 'Varsity'
                elif any(c.lower() == 'jv' for c in classes):
                    status = 'JV'

                if grp_name not in group_map:
                    group_map[grp_name] = {}

                if status == 'JV':
                    group_map[grp_name]['JV'] = {'run': desc, 'pre': '', 'post': ''}
                    day['has_vjv'] = True
                else:
                    if 'PRE' in sec_lbl:
                        group_map[grp_name].setdefault('V', {})['pre'] = desc
                    elif 'POST' in sec_lbl:
                        group_map[grp_name].setdefault('V', {})['post'] = desc
                    else:
                        existing = group_map[grp_name].get('V', {}).get('run', '')
                        is_off   = desc.strip().lower() in ('off', 'rest', 'off day', '')
                        if not existing:
                            group_map[grp_name].setdefault('V', {})['run'] = desc
                        elif is_off:
                            # Second section "Off" = non-racer row, not an overwrite
                            if 'JV' not in group_map[grp_name]:
                                group_map[grp_name]['JV'] = {'run': desc, 'pre': '', 'post': ''}
                                day['has_vjv'] = True

        for grp_name, statuses in group_map.items():
            v_data = statuses.get('V', {})
            entry = {
                'run': v_data.get('run', ''),
                'pre': v_data.get('pre', ''),
                'post': v_data.get('post', ''),
                'status': '',
                'jv_run': statuses.get('JV', {}).get('run', '') if day['has_vjv'] else ''
            }
            day['groups'][grp_name] = entry

        data['days'].append(day)
    return data


def parse_week(filepath, week_num):
    with open(filepath, encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    fmt = detect_format(soup)
    return (parse_old_format if fmt == 'old' else parse_new_format)(soup, week_num), fmt


# ─── OVERVIEW ROW BUILDER ─────────────────────────────────────────────────────

DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
GROUPS_FLAG = 'athlete_groups.html'


MEET_KEYWORDS = re.compile(
    r'\b(invitational|relays?|championship|classic|festival|dual\s+meet|'
    r'state\s+meet|region(?:al)?|district|sectional|qualifier|time\s+trial|'
    r'meet\s+of|(?:cross\s+country|track)\s+meet)\b',
    re.I
)

def detect_meet(data):
    """
    Scan notes and race-day content for an actual meet name.
    Returns a string or ''.
    Ignores training/coaching notes — only returns text that looks like a meet.
    """
    candidates = []

    # Check notes for meet references
    for note in data.get('notes', []):
        if MEET_KEYWORDS.search(note):
            # Clean up: strip leading bold labels like "Week 6 Meet:"
            clean_note = re.sub(r'^[^:]+:\s*', '', note).strip()
            if clean_note:
                candidates.append(clean_note[:80])

    # Check highlight — but only if it looks like a meet, not a training note
    hl = data.get('highlight', '')
    if hl and MEET_KEYWORDS.search(hl):
        clean_hl = re.sub(r'^[📱🎯⚡🏆!\s]+', '', hl).strip()
        candidates.append(clean_hl[:80])

    return candidates[0] if candidates else ''


def build_overview_rows(data, ref_year=2025, debug=False):
    """
    Build V (and optionally JV) row dicts for the Overview CSV.
    Returns list of row dicts (1 or 2 rows).
    """
    week_num = data['week']
    monday   = find_monday(data, ref_year)
    beg_date = format_beginning_date(monday)
    meet     = detect_meet(data)

    # Mileage totals
    def parse_vol(grp):
        raw = data['totals'].get(grp, '')
        return extract_miles_float(raw)

    vol_gold  = parse_vol('Gold')
    vol_green = parse_vol('Green')
    vol_white = parse_vol('White')
    vol_fr    = parse_vol('Freshman')

    # Index days by name
    day_index = {}
    for day in data['days']:
        if day['name']:
            day_index[day['name']] = day

    # Build V row
    v_row   = {'Unnamed: 0': 'V',  'Week': week_num, 'Beginning Date': beg_date,
               'Meet': meet, 'Vol_Gold': vol_gold, 'Vol_Green': vol_green,
               'Vol_White': vol_white, 'Vol_FR': vol_fr, '_review': []}
    jv_row  = {'Unnamed: 0': 'JV', 'Week': week_num, 'Beginning Date': beg_date,
               'Meet': '', 'Vol_Gold': None, 'Vol_Green': None,
               'Vol_White': None, 'Vol_FR': None, '_review': []}
    has_jv  = False

    for day_name in DAYS:
        v_col  = day_name
        g_col  = f"{day_name}_Groups"
        day    = day_index.get(day_name)

        if not day or not day['groups']:
            v_row[v_col]  = None
            v_row[g_col]  = None
            jv_row[v_col] = None
            jv_row[g_col] = None
            continue

        grps = day['groups']
        gold_data = grps.get('Gold') or grps.get(next(iter(grps), ''))
        fr_data   = grps.get('Freshman', gold_data)

        gold_run  = gold_data.get('run', '') if gold_data else ''
        fr_run    = fr_data.get('run', '')   if fr_data  else ''

        # V canonical
        v_simple, v_review = simplify_workout(gold_run)
        if v_review:
            v_row['_review'].append(f"{day_name}: {v_simple!r}")

        # Groups page flag
        use_groups = needs_groups_page(gold_run, fr_run) if gold_run else False

        v_row[v_col] = v_simple
        v_row[g_col] = GROUPS_FLAG if use_groups else None

        # JV / Non-racer (from V/JV split in new format, or absent in XC)
        jv_run = gold_data.get('jv_run', '') if gold_data else ''
        if jv_run and jv_run.strip().lower() not in ('', 'off'):
            jv_simple, jv_review = simplify_workout(jv_run)
            if jv_review:
                jv_row['_review'].append(f"{day_name}: {jv_simple!r}")
            jv_row[v_col] = jv_simple
            jv_row[g_col] = GROUPS_FLAG if use_groups else None
            has_jv = True
        else:
            jv_row[v_col] = None
            jv_row[g_col] = None

        if debug:
            print(f"    {day_name}: gold_run={gold_run[:60]!r} → {v_simple!r} review={v_review}")

    rows = [v_row]
    if has_jv:
        rows.append(jv_row)

    return rows


# ─── MAIN ─────────────────────────────────────────────────────────────────────

OVERVIEW_COLS = [
    'Unnamed: 0', 'Week', 'Beginning Date',
    'Monday', 'Monday_Groups',
    'Tuesday', 'Tuesday_Groups',
    'Wednesday', 'Wednesday_Groups',
    'Thursday', 'Thursday_Groups',
    'Friday', 'Friday_Groups',
    'Saturday', 'Saturday_Groups',
    'Sunday', 'Sunday_Groups',
    'Meet', 'Vol_Gold', 'Vol_Green', 'Vol_White', 'Vol_FR'
]


def main():
    ap = argparse.ArgumentParser(description='Build Training Overview CSV from week HTML files.')
    ap.add_argument('--start',    type=int, required=True,  help='First week number')
    ap.add_argument('--end',      type=int, required=True,  help='Last week number')
    ap.add_argument('--input',    type=str, default='.',    help='Directory containing weekNN.html files')
    ap.add_argument('--output',   type=str, default='Training_Overview_extracted.csv', help='Output CSV path')
    ap.add_argument('--ref-year', type=int, default=2025,   help='Reference year for date parsing (default 2025)')
    ap.add_argument('--debug',    action='store_true')
    args = ap.parse_args()

    input_dir = Path(args.input)
    all_rows  = []
    review_log = []
    processed = skipped = 0

    print(f"\n{'='*60}")
    print(f"  Archive → Training Overview Extractor")
    print(f"  Weeks {args.start}–{args.end}  |  input: {input_dir}")
    print(f"{'='*60}\n")

    for n in range(args.start, args.end + 1):
        fp = input_dir / f"week{n:02d}.html"
        if not fp.exists():
            fp = input_dir / f"week{n}.html"
        if not fp.exists():
            print(f"  ⚠  week{n:02d}.html not found — skipping")
            skipped += 1
            continue

        print(f"  ✓  Week {n}  ({fp.name})")
        data, fmt = parse_week(fp, n)

        if args.debug:
            print(f"      format={fmt}  totals={data['totals']}  days={[d['name'] for d in data['days']]}")

        rows = build_overview_rows(data, ref_year=args.ref_year, debug=args.debug)

        for row in rows:
            review = row.pop('_review', [])
            if review:
                review_log.append(f"Week {n} ({row['Unnamed: 0']}):")
                for item in review:
                    review_log.append(f"  ⚠  {item}")

        all_rows.extend(rows)
        processed += 1

    # Write CSV
    out_path = Path(args.output)
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=OVERVIEW_COLS,
                                quoting=csv.QUOTE_MINIMAL,
                                lineterminator='\r\n',
                                extrasaction='ignore')
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n{'='*60}")
    print(f"  ✅  {processed} weeks extracted → {out_path}")
    if skipped:
        print(f"  ⚠   {skipped} weeks skipped (file not found)")

    if review_log:
        print(f"\n  📋  {len(review_log)} items need manual review:")
        for line in review_log:
            print(f"     {line}")
        print(f"\n  These are interval/workout descriptions the pipeline")
        print(f"  can't auto-expand per-group. Edit them in the CSV")
        print(f"  before running overview_to_week_schedule_mk2.py.")
    else:
        print(f"  ✅  No items flagged for review — ready for pipeline.")

    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
