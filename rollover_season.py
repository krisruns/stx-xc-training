#!/usr/bin/env python3
"""
STX Season Rollover Script
Converts existing week HTML files to the current format with updated dates.

Usage:
    python rollover_season.py --start 1 --end 23 --shift-weeks 52 --input ./old --output ./new
    python rollover_season.py --start 1 --end 23 --new-start 2026-06-01 --input ./old --output ./new

Arguments:
    --start N           First week number to process
    --end N             Last week number to process
    --shift-weeks N     Shift all dates forward by N weeks (e.g. 52 for one year)
    --new-start DATE    Explicit Monday date for week 1 of new season (YYYY-MM-DD).
                        Calculates shift automatically from the old week 1 file.
    --input DIR         Directory containing old weekNN.html files (default: .)
    --output DIR        Output directory for converted files (default: ./rollover_out)
    --title PREFIX      Season title prefix, e.g. "STX XC 2026 Training" (default: auto)
    --debug             Print parsing details for each file
"""

import argparse
import os
import re
from pathlib import Path
from datetime import datetime, timedelta
from bs4 import BeautifulSoup, NavigableString

# ─── DATE UTILITIES ───────────────────────────────────────────────────────────

MONTHS = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12
}
MONTH_ABBREV = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
}

def parse_date_from_text(text, ref_year=2025):
    """Try to parse a date from text like 'June 30' or 'July 1, 2025'."""
    text = text.strip()
    m = re.search(
        r'(january|february|march|april|may|june|july|august|september|october|november|december)'
        r'\s+(\d{1,2})(?:,?\s*(\d{4}))?',
        text, re.I
    )
    if m:
        month = MONTHS[m.group(1).lower()]
        day = int(m.group(2))
        year = int(m.group(3)) if m.group(3) else ref_year
        try:
            return datetime(year, month, day)
        except ValueError:
            return None
    return None


def shift_date_in_text(text, delta, ref_year=2025):
    """
    Find all date patterns in text and shift them by delta (timedelta).
    Handles: "June 30", "July 1, 2025", "MONDAY, JUNE 30"
    Returns updated text.
    """
    def replace_match(m):
        full = m.group(0)
        month_str = m.group(1)
        day_str = m.group(2)
        year_str = m.group(3)
        month = MONTHS[month_str.lower()]
        day = int(day_str)
        year = int(year_str) if year_str else ref_year
        try:
            old_date = datetime(year, month, day)
        except ValueError:
            return full
        new_date = old_date + delta
        # Preserve capitalisation style
        new_month = new_date.strftime('%B')
        if month_str.isupper():
            new_month = new_month.upper()
        elif month_str[0].isupper():
            new_month = new_month.capitalize()
        else:
            new_month = new_month.lower()
        # Preserve year if it was present
        if year_str:
            return f"{new_month} {new_date.day}, {new_date.year}"
        else:
            return f"{new_month} {new_date.day}"

    pattern = (
        r'(january|february|march|april|may|june|july|august|september|october|november|december)'
        r'\s+(\d{1,2})(?:,?\s*(\d{4}))?'
    )
    return re.sub(pattern, replace_match, text, flags=re.I)


def shift_year_in_text(text, old_year, new_year):
    """Replace standalone year references."""
    return re.sub(r'\b' + str(old_year) + r'\b', str(new_year), text)


def format_date_range(start_date, end_date):
    """Format a week date range like 'June 2 - 8, 2026' or 'June 30 - July 6, 2026'."""
    year = end_date.year
    if start_date.month == end_date.month:
        return f"{start_date.strftime('%B %-d')} - {end_date.day}, {year}"
    else:
        return f"{start_date.strftime('%B %-d')} - {end_date.strftime('%B %-d')}, {year}"


# ─── PARSERS ──────────────────────────────────────────────────────────────────

def clean_text(el):
    """Get text from element, stripping links but keeping content."""
    if el is None:
        return ''
    for a in el.find_all('a'):
        a.unwrap()
    text = el.get_text(separator=' ', strip=True)
    return re.sub(r'\s+', ' ', text).strip()


def extract_miles(text):
    """Extract a numeric mile value from text like '8 miles easy' or '7.5mi'."""
    m = re.search(r'(\d+\.?\d*)\s*mi', text, re.I)
    if m:
        val = float(m.group(1))
        return f"{int(val)} mi" if val == int(val) else f"{val} mi"
    return 'REST' if 'rest' in text.lower() else ''


def detect_format(soup):
    """Return 'old' (week06 style) or 'new' (week52 style)."""
    if soup.find('div', class_='day-section'):
        return 'old'
    if soup.find('div', class_='workout-item'):
        return 'new'
    return 'old'


def parse_old_format(soup, week_num, debug=False):
    """
    Parse week06-style HTML.
    Returns dict: {week, title_text, date_range_text, days, totals, notes}
    Each day: {title, date_text, groups: [{name, pre, run, post, miles}]}
    """
    data = {
        'week': week_num,
        'title_text': '',
        'date_range_text': '',
        'days': [],
        'totals': {},   # group -> miles string
        'notes': []
    }

    # Title / header
    h1 = soup.find('h1')
    if h1:
        data['title_text'] = clean_text(h1)
    header_p = soup.find('div', class_='header')
    if header_p:
        p = header_p.find('p')
        if p:
            data['date_range_text'] = clean_text(p)

    # Week highlight / special note
    highlight = soup.find('div', class_='week-highlight')
    if highlight:
        data['notes'].append(clean_text(highlight))

    # Totals
    totals_div = soup.find('div', class_='totals-section')
    if totals_div:
        for item in totals_div.find_all('div', class_='total-item'):
            grp_el = item.find('div', class_='total-group')
            mi_el  = item.find('div', class_='total-miles')
            if grp_el and mi_el:
                grp = clean_text(grp_el).title()
                data['totals'][grp] = clean_text(mi_el)

    # Notes section
    notes_sec = soup.find('div', class_='notes-section')
    if notes_sec:
        for li in notes_sec.find_all('li'):
            data['notes'].append(clean_text(li))

    # Days
    for day_div in soup.find_all('div', class_='day-section'):
        day = {'title': '', 'date_text': '', 'groups': []}

        title_el = day_div.find('div', class_='day-title')
        if title_el:
            raw = clean_text(title_el)
            # Strip emoji suffixes
            raw = re.sub(r'[\U00010000-\U0010ffff📱🎯]+', '', raw).strip()
            day['title'] = raw
            # Try to pull date from title like "MONDAY, JUNE 30"
            day['date_text'] = raw

        groups_container = day_div.find('div', class_='groups-container')
        if not groups_container:
            # Some days have groups directly in day-section
            groups_container = day_div

        for group_div in groups_container.find_all('div', class_='group'):
            grp = {'name': '', 'pre': '', 'run': '', 'post': '', 'miles': ''}
            name_el = group_div.find('div', class_='group-name')
            if name_el:
                grp['name'] = clean_text(name_el).title()

            for ws in group_div.find_all('div', class_='workout-section'):
                label_el = ws.find('div', class_='workout-label')
                label = clean_text(label_el).upper().rstrip(':') if label_el else ''

                # Grab main + details content
                content_el = ws.find('div', class_='workout-content')
                if content_el:
                    for a in content_el.find_all('a'):
                        a.decompose()
                    main_el   = content_el.find('div', class_='workout-main')
                    detail_el = content_el.find('div', class_='workout-details')
                    parts = []
                    if main_el:
                        t = clean_text(main_el)
                        if t: parts.append(t)
                    if detail_el:
                        t = clean_text(detail_el)
                        if t: parts.append(t)
                    text = ' '.join(parts)
                else:
                    text = ''

                if 'PRE' in label:
                    grp['pre'] = text
                elif 'RUN' in label:
                    grp['run'] = text
                    grp['miles'] = extract_miles(text)
                elif 'POST' in label:
                    grp['post'] = text

            if grp['name']:
                day['groups'].append(grp)

        if day['title'] or day['groups']:
            data['days'].append(day)

        if debug:
            print(f"    Day: {day['title']} | groups: {[g['name'] for g in day['groups']]}")

    return data


def parse_new_format(soup, week_num, debug=False):
    """
    Parse week52-style HTML.
    Returns same dict structure as parse_old_format.
    """
    data = {
        'week': week_num,
        'title_text': '',
        'date_range_text': '',
        'days': [],
        'totals': {},
        'notes': []
    }

    h1 = soup.find('h1')
    if h1:
        data['title_text'] = clean_text(h1)

    subtitle = soup.find('p', class_='subtitle') or soup.find('div', class_='subtitle')
    if subtitle:
        data['date_range_text'] = clean_text(subtitle)

    # Totals
    totals_div = soup.find('div', class_='totals')
    if totals_div:
        for item in totals_div.find_all('div', class_='total'):
            lbl = item.find('div', class_='total-label')
            mi  = item.find('div', class_='total-miles')
            if lbl and mi:
                raw_mi = clean_text(mi)
                # Handle "0-27.5" ranges (race week) — keep as-is
                data['totals'][clean_text(lbl).title()] = raw_mi

    # Notes
    notes_div = soup.find('div', class_='week-notes')
    if notes_div:
        for li in notes_div.find_all('li'):
            data['notes'].append(clean_text(li))

    # Days — group by day div, then by section label
    for day_div in soup.find_all('div', class_='day'):
        day = {'title': '', 'date_text': '', 'groups': []}

        hdr = day_div.find('div', class_='day-header')
        if hdr:
            raw = hdr.get_text(separator=' ', strip=True)
            raw = re.sub(r'[\U00010000-\U0010ffff📱🎯]+', '', raw).strip()
            # Remove the "Groups" button text if present
            raw = re.sub(r'←?\s*Groups\s*', '', raw).strip()
            day['title'] = raw.split('Workout Paces')[0].strip()
            day['date_text'] = day['title']

        # Collect items per group, preserving section labels (PRE / WORKOUT / POST)
        group_data = {}  # name -> {pre, run, post, miles, sections}

        for section in day_div.find_all('div', class_='section'):
            sec_label_el = section.find('div', class_='section-label')
            sec_label = clean_text(sec_label_el).upper() if sec_label_el else 'WORKOUT'

            for item in section.find_all('div', class_='workout-item'):
                grp_name = item.get('data-group', '').strip()
                if not grp_name:
                    continue
                desc_el  = item.find('div', class_='workout-desc')
                miles_el = item.find('div', class_='workout-miles')
                for a in (item.find_all('a') or []):
                    a.decompose()
                desc  = clean_text(desc_el)
                miles = clean_text(miles_el)

                if grp_name not in group_data:
                    group_data[grp_name] = {'name': grp_name, 'pre': '', 'run': '', 'post': '', 'miles': ''}

                if 'PRE' in sec_label:
                    group_data[grp_name]['pre'] = desc
                elif 'POST' in sec_label:
                    group_data[grp_name]['post'] = desc
                else:
                    # Main workout — handle Varsity/JV by appending
                    existing = group_data[grp_name]['run']
                    if existing and desc and existing != desc:
                        group_data[grp_name]['run'] = f"{existing} / {desc}"
                    elif desc:
                        group_data[grp_name]['run'] = desc
                    if miles and miles != 'REST':
                        group_data[grp_name]['miles'] = miles

        for grp in ['Gold', 'Green', 'White', 'Freshman']:
            if grp in group_data:
                day['groups'].append(group_data[grp])

        if day['title'] or day['groups']:
            data['days'].append(day)

        if debug:
            print(f"    Day: {day['title']} | groups: {[g['name'] for g in day['groups']]}")

    return data


def parse_week_file(filepath, week_num, debug=False):
    with open(filepath, encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    fmt = detect_format(soup)
    if debug:
        print(f"    Format detected: {fmt}")
    if fmt == 'new':
        return parse_new_format(soup, week_num, debug)
    else:
        return parse_old_format(soup, week_num, debug)


# ─── HTML GENERATION (NEW FORMAT) ─────────────────────────────────────────────

CSS = """
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; max-width: 1000px; margin: 20px auto; padding: 0 20px; background: #fafafa; }
        h1 { color: #2c5530; border-bottom: 3px solid #4a7c59; padding-bottom: 10px; }
        .subtitle { color: #666; margin-bottom: 20px; }
        .back-btn { display: inline-block; margin-bottom: 12px; padding: 7px 14px; background: white; color: #2c5530; border: 2px solid #4a7c59; border-radius: 4px; text-decoration: none; font-size: 0.9rem; font-weight: 600; transition: all 0.2s; }
        .back-btn:hover { background: #4a7c59; color: white; }
        .totals { display: flex; gap: 10px; margin: 20px 0; flex-wrap: wrap; }
        .total { padding: 15px 20px; background: white; border-radius: 6px; flex: 1; min-width: 140px; text-align: center; cursor: pointer; transition: all 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .total:hover { transform: translateY(-2px); box-shadow: 0 2px 6px rgba(0,0,0,0.15); }
        .total.gold { border-left: 4px solid #DAA520; }
        .total.gold.active { background: #DAA520; color: white; }
        .total.green { border-left: 4px solid #4a7c59; }
        .total.green.active { background: #4a7c59; color: white; }
        .total.white { border-left: 4px solid #888; }
        .total.white.active { background: #888; color: white; }
        .total.freshman { border-left: 4px solid #4169E1; }
        .total.freshman.active { background: #4169E1; color: white; }
        .total-label { font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px; }
        .total-miles { font-size: 1.8rem; font-weight: 700; }
        .filters { margin: 20px 0; text-align: center; }
        .filter-btn { padding: 8px 16px; margin: 0 5px 5px 0; border: 2px solid #4a7c59; background: white; color: #4a7c59; border-radius: 4px; cursor: pointer; font-size: 0.9rem; transition: all 0.2s; }
        .filter-btn:hover, .filter-btn.active { background: #4a7c59; color: white; }
        .week-notes { margin: 25px 0; border-radius: 8px; overflow: hidden; background: #FFF9E6; border: 3px solid #DAA520; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .notes-header { background: linear-gradient(135deg, #DAA520 0%, #B8860B 100%); padding: 15px 20px; color: white; font-size: 1.2rem; font-weight: 700; letter-spacing: 0.5px; }
        .notes-content { padding: 20px; color: #333; }
        .notes-content ul { margin: 10px 0 0 20px; }
        .notes-content li { margin-bottom: 5px; }
        .day { margin: 25px 0; border-radius: 8px; overflow: hidden; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .day-header { background: linear-gradient(135deg, #2c5530 0%, #4a7c59 100%); padding: 15px 20px; color: white; font-size: 1.2rem; font-weight: 700; letter-spacing: 0.5px; }
        .section { padding: 15px 20px; border-bottom: 1px solid #f0f0f0; }
        .section:last-child { border-bottom: none; }
        .section-label { font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #888; margin-bottom: 10px; }
        .workout-item { display: flex; align-items: flex-start; padding: 8px 0; border-bottom: 1px solid #f8f8f8; gap: 12px; }
        .workout-item:last-child { border-bottom: none; }
        .workout-item.hidden { display: none; }
        .group-badge { font-size: 0.7rem; font-weight: 700; text-transform: uppercase; padding: 2px 8px; border-radius: 3px; color: white; min-width: 70px; text-align: center; flex-shrink: 0; margin-top: 2px; }
        .group-badge.gold { background: #DAA520; }
        .group-badge.green { background: #4a7c59; }
        .group-badge.white { background: #888; }
        .group-badge.freshman { background: #4169E1; }
        .workout-desc { flex: 1; font-size: 0.95rem; color: #333; }
        .workout-miles { font-size: 0.85rem; font-weight: 600; color: #2c5530; min-width: 60px; text-align: right; flex-shrink: 0; }
"""

JS = """
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
"""

GROUP_ORDER = ['Gold', 'Green', 'White', 'Freshman']


def render_totals(totals):
    if not totals:
        return ''
    items = ''
    for grp in GROUP_ORDER:
        if grp in totals:
            cls = grp.lower()
            items += f'''
        <div class="total {cls}" onclick="filterGroup('{grp}')" id="total-{grp}">
            <div class="total-label">{grp}</div>
            <div class="total-miles">{totals[grp]}</div>
        </div>'''
    return f'    <div class="totals">{items}\n    </div>'


def render_notes(notes):
    if not notes:
        return ''
    items = ''.join(f'            <li>{n}</li>\n' for n in notes)
    return f'''    <div class="week-notes">
        <div class="notes-header">📋 Training Notes</div>
        <div class="notes-content"><ul>
{items}        </ul></div>
    </div>'''


def render_day(day, delta, ref_year):
    """Render a single day in new format."""
    title = day['title']
    if delta and title:
        title = shift_date_in_text(title, delta, ref_year)
    if not day['groups']:
        return ''

    # Determine which sections to render
    has_pre  = any(g['pre']  for g in day['groups'])
    has_post = any(g['post'] for g in day['groups'])

    sections_html = ''

    if has_pre:
        items = ''
        for g in day['groups']:
            if not g['pre']:
                continue
            cls = g['name'].lower()
            items += f'''            <div class="workout-item {cls}" data-group="{g['name']}">
                <div class="group-badge {cls}">{g['name']}</div>
                <div class="workout-desc">{g['pre']}</div>
                <div class="workout-miles"></div>
            </div>\n'''
        if items:
            sections_html += f'''        <div class="section">
            <div class="section-label">Pre</div>
{items}        </div>\n'''

    # Main workout
    items = ''
    for g in day['groups']:
        run = g['run'] or g.get('desc', '')
        if not run:
            continue
        cls = g['name'].lower()
        miles = g.get('miles', '')
        items += f'''            <div class="workout-item {cls}" data-group="{g['name']}">
                <div class="group-badge {cls}">{g['name']}</div>
                <div class="workout-desc">{run}</div>
                <div class="workout-miles">{miles}</div>
            </div>\n'''
    if items:
        sections_html += f'''        <div class="section">
            <div class="section-label">Workout</div>
{items}        </div>\n'''

    if has_post:
        items = ''
        for g in day['groups']:
            if not g['post']:
                continue
            cls = g['name'].lower()
            items += f'''            <div class="workout-item {cls}" data-group="{g['name']}">
                <div class="group-badge {cls}">{g['name']}</div>
                <div class="workout-desc">{g['post']}</div>
                <div class="workout-miles"></div>
            </div>\n'''
        if items:
            sections_html += f'''        <div class="section">
            <div class="section-label">Post</div>
{items}        </div>\n'''

    return f'''    <div class="day">
        <div class="day-header">{title}</div>
{sections_html}    </div>\n'''


def generate_html(data, delta, ref_year, title_prefix, date_range_str):
    week_num = data['week']
    h1 = f"🏃 {title_prefix} — Week {week_num} — {date_range_str}"

    totals_html  = render_totals(data['totals'])
    notes_html   = render_notes(data['notes'])
    days_html    = ''.join(render_day(d, delta, ref_year) for d in data['days'])

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title_prefix} Week {week_num}</title>
    <style>{CSS}
    </style>
</head>
<body>
    <a href="index.html" class="back-btn">← Schedule</a>
    <h1>{h1}</h1>
    <p class="subtitle">Training Week</p>

{totals_html}

    <div class="filters">
        <button class="filter-btn active" onclick="showAll()">Show All</button>
        <button class="filter-btn" onclick="filterGroup('Gold')">Gold</button>
        <button class="filter-btn" onclick="filterGroup('Green')">Green</button>
        <button class="filter-btn" onclick="filterGroup('White')">White</button>
        <button class="filter-btn" onclick="filterGroup('Freshman')">Freshman</button>
    </div>

{notes_html}

{days_html}
    <script>{JS}
    </script>
</body>
</html>"""


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def compute_date_range(data, delta, ref_year):
    """
    Find the Monday date for this week from the first day title,
    shift it, and return (start_date, end_date, date_range_str).
    """
    for day in data['days']:
        d = parse_date_from_text(day.get('date_text', ''), ref_year)
        if d:
            # Snap to Monday (in case day isn't Monday)
            monday = d - timedelta(days=d.weekday())
            new_monday = monday + delta
            new_sunday = new_monday + timedelta(days=6)
            return new_monday, new_sunday, format_date_range(new_monday, new_sunday)
    # Fallback: no date found
    return None, None, ''


def main():
    ap = argparse.ArgumentParser(description='STX Season Rollover — update dates and convert to current HTML format.')
    ap.add_argument('--start',       type=int, required=True,  help='First week number')
    ap.add_argument('--end',         type=int, required=True,  help='Last week number')
    ap.add_argument('--shift-weeks', type=int, default=None,   help='Shift all dates by N weeks')
    ap.add_argument('--new-start',   type=str, default=None,   help='New Monday date for week 1 (YYYY-MM-DD)')
    ap.add_argument('--input',       type=str, default='.',    help='Input directory (default: .)')
    ap.add_argument('--output',      type=str, default='rollover_out', help='Output directory')
    ap.add_argument('--title',       type=str, default=None,   help='Title prefix e.g. "STX XC 2026 Training"')
    ap.add_argument('--debug',       action='store_true')
    args = ap.parse_args()

    input_dir  = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Determine date shift ---
    delta    = None
    ref_year = 2025   # fallback for parsing dates without explicit year

    if args.shift_weeks is not None:
        delta = timedelta(weeks=args.shift_weeks)
        print(f"  Date shift: +{args.shift_weeks} weeks ({delta.days} days)")

    elif args.new_start:
        new_week1_monday = datetime.strptime(args.new_start, '%Y-%m-%d')
        # Find old week 1 Monday from the first available file
        for n in range(args.start, args.end + 1):
            fp = input_dir / f"week{n:02d}.html"
            if not fp.exists():
                fp = input_dir / f"week{n}.html"
            if fp.exists():
                with open(fp, encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')
                fmt = detect_format(soup)
                parsed = parse_old_format(soup, n) if fmt == 'old' else parse_new_format(soup, n)
                for day in parsed['days']:
                    d = parse_date_from_text(day.get('date_text', ''), ref_year)
                    if d:
                        old_monday = d - timedelta(days=d.weekday())
                        # Offset from week N to week 1
                        week_offset = timedelta(weeks=(n - args.start))
                        old_week1_monday = old_monday - week_offset
                        delta = new_week1_monday - old_week1_monday
                        print(f"  Detected old week {args.start} start: {old_week1_monday.strftime('%Y-%m-%d')}")
                        print(f"  New week {args.start} start:          {new_week1_monday.strftime('%Y-%m-%d')}")
                        print(f"  Date shift: {delta.days} days")
                        break
                if delta:
                    break

    if delta is None:
        print("⚠️  No date shift specified — dates will be copied as-is.")
        print("   Use --shift-weeks 52 or --new-start YYYY-MM-DD to update dates.")
        delta = timedelta(0)

    ref_year = 2025  # year to assume when none is explicit in the source HTML

    # --- Title prefix ---
    title_prefix = args.title or 'STX Training'

    # --- Process files ---
    print(f"\nProcessing weeks {args.start}–{args.end} from {input_dir}\n")
    processed, skipped = 0, 0

    for n in range(args.start, args.end + 1):
        fp = input_dir / f"week{n:02d}.html"
        if not fp.exists():
            fp = input_dir / f"week{n}.html"
        if not fp.exists():
            print(f"  ⚠️  week{n:02d}.html not found — skipping")
            skipped += 1
            continue

        print(f"  ✓  Week {n} ({fp.name})")
        data = parse_week_file(fp, n, debug=args.debug)

        # Compute new date range
        _, _, date_range_str = compute_date_range(data, delta, ref_year)
        if not date_range_str:
            # New-format: dates live in the h1 title string — shift them directly
            shifted_title = shift_date_in_text(data.get('title_text', ''), delta, ref_year)
            # Extract the date portion after "—" e.g. "🏃 STX Training — Week 52 — May 18 - 24, 2026"
            m = re.search(
                r'((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\S*\s+\d{1,2}.+\d{4})',
                shifted_title, re.I
            )
            date_range_str = m.group(1).strip() if m else shift_date_in_text(
                data.get('date_range_text', ''), delta, ref_year
            )

        if args.debug:
            print(f"    Date range: {date_range_str}")
            print(f"    Totals: {data['totals']}")

        html_out = generate_html(data, delta, ref_year, title_prefix, date_range_str)

        out_file = output_dir / f"week{n:02d}.html"
        out_file.write_text(html_out, encoding='utf-8')
        print(f"     → {out_file}  [{date_range_str}]")
        processed += 1

    print(f"\n✅  Done — {processed} files converted, {skipped} skipped")
    print(f"   Output: {output_dir.resolve()}")


if __name__ == '__main__':
    main()
