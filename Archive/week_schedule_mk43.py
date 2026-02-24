#!/usr/bin/env python3
"""
Generate weekly training schedule HTML with mileage ranges and workout detail links.

Features:
- Racer/Non-Racer week differentiation
- Workout library integration for detailed explanations
- Clickable workout links opening modal dialogs
- Automatic workout matching by ID or text similarity

Usage:
    python week_schedule_enhanced.py week34_input.csv [workout_library.csv]
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path
import re
from os.path import exists


def parse_mileage(miles_str):
    """Parse mileage string, handling REST and numeric values."""
    if isinstance(miles_str, (int, float)):
        return float(miles_str)
    miles_str = str(miles_str).strip().upper()
    if miles_str == 'REST' or miles_str == '0' or not miles_str:
        return 0.0
    try:
        return float(miles_str)
    except ValueError:
        return 0.0


def has_parseable_paces(workout_desc):
    """
    Check if workout description has parseable paces.
    Returns True if workout contains patterns like "12x400@5k", "2x200@mile", etc.
    """
    if not workout_desc:
        return False
    
    # Pattern: [number]x[distance]@[pace_type]
    pattern = r'(\d+)x(\d+)(?:m)?@([\w\d]+)'
    matches = re.findall(pattern, workout_desc.lower())
    
    return len(matches) > 0


def get_workout_pace_filename(day, week_num, status=''):
    """
    Generate the expected workout pace page filename.
    
    Args:
        day: Full day name (e.g., "Tuesday")
        week_num: Week number
        status: 'Varsity', 'JV', or '' for All
    
    Returns:
        Filename like "workout-groups_v_tue_week39.html"
    """
    day_abbr = day[:3].lower()  # tue, wed, etc.
    
    # Handle both 'Varsity' and 'V' formats
    if status:
        status_upper = status.upper()
        if 'VARSITY' in status_upper or status_upper == 'V':
            squad_prefix = 'v_'
        elif 'JV' in status_upper:
            squad_prefix = 'jv_'
        else:
            squad_prefix = ''
    else:
        squad_prefix = ''
    
    return f"workout-groups_{squad_prefix}{day_abbr}_week{week_num}.html"


def create_reference_links(text):
    """Convert Pre/Post text into HTML with links to reference pages."""
    if not text or text.strip() == '':
        return ''
    
    # Mapping of keywords to reference pages
    reference_map = {
        'Foot Drills': 'STX_XC_Foot_Drills_Reference.html',
        'Dynamics': 'STX_XC_Movement___Warmup_Reference.html',
        'WU': 'STX_XC_Movement___Warmup_Reference.html',
        'Awesomizer': 'STX_XC_Movement___Warmup_Reference.html',
        'Lunge Matrix': 'STX_XC_Movement___Warmup_Reference.html',
        'Strides': 'STX_XC_Movement___Warmup_Reference.html',
        'Mobility': 'mobility-strength.html',
        'Strength': 'mobility-strength.html',
        'Race Day WU': 'STX_XC_Movement___Warmup_Reference.html',
        'Post Race': 'STX_XC_Movement___Warmup_Reference.html',
    }
    
    # Split by comma or semicolon
    parts = [p.strip() for p in text.replace(';', ',').split(',')]
    linked_parts = []
    
    for part in parts:
        if not part:
            continue
        
        # Find matching reference
        link_url = None
        for keyword, url in reference_map.items():
            if keyword.lower() in part.lower():
                link_url = url
                break
        
        if link_url:
            linked_parts.append(f'<a href="{link_url}" target="_blank" class="ref-link">{part}</a>')
        else:
            linked_parts.append(part)
    
    return ', '.join(linked_parts)


def load_workout_library(library_path):
    """Load workout library from CSV."""
    if not library_path or not library_path.exists():
        return {}
    
    library = {}
    with open(library_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            workout_id = row.get('Workout_ID', '').strip()
            if workout_id:
                library[workout_id] = {
                    'short_name': row.get('Short_Name', ''),
                    'full_description': row.get('Full_Description', ''),
                    'key_points': row.get('Key_Points', '').split('|'),
                    'pace_info': row.get('Pace_Info', ''),
                    'duration': row.get('Duration', '')
                }
    return library


def find_workout_match(workout_text, library):
    """
    Find matching workout in library by ID or text similarity.
    Returns (workout_id, match_data) or (None, None) if no match.
    """
    # Direct ID match (if workout_text is an ID)
    if workout_text in library:
        return workout_text, library[workout_text]
    
    # Text-based matching for common patterns
    workout_lower = workout_text.lower()
    
    # Fartlek patterns
    if '5-4-3-2-1' in workout_text and 'fartlek' in workout_lower:
        if 'fartlek-5-4-3-2-1' in library:
            return 'fartlek-5-4-3-2-1', library['fartlek-5-4-3-2-1']
    
    # Hills patterns
    hills_match = re.search(r'hills.*?(\d+)min', workout_lower)
    if hills_match:
        duration = hills_match.group(1)
        workout_id = f'hills-{duration}'
        if workout_id in library:
            return workout_id, library[workout_id]
    
    # Tempo patterns
    tempo_match = re.search(r'tempo.*?(\d+)min', workout_lower)
    if tempo_match:
        duration = tempo_match.group(1)
        workout_id = f'tempo-{duration}'
        if workout_id in library:
            return workout_id, library[workout_id]
    
    # Strides patterns
    strides_match = re.search(r'(\d+)x200', workout_lower)
    if strides_match and 'stride' in workout_lower:
        count = strides_match.group(1)
        workout_id = f'strides-{count}x200'
        if workout_id in library:
            return workout_id, library[workout_id]
    
    # Pre 30/40 pattern (single combined workout)
    if ('pre 30/40' in workout_lower or 'pre30/40' in workout_lower or 
        'pre 30-40' in workout_lower or 'pre30-40' in workout_lower):
        if 'pre-30-40' in library:
            return 'pre-30-40', library['pre-30-40']
    
    # Long run progression
    if 'long run' in workout_lower and 'progression' in workout_lower:
        if 'long-run-progression' in library:
            return 'long-run-progression', library['long-run-progression']
    
    # Easy run
    if 'easy' in workout_lower and workout_lower.endswith('easy'):
        if 'easy-run' in library:
            return 'easy-run', library['easy-run']
    
    return None, None


def generate_workout_modal_html(workout_id, workout_data):
    """Generate HTML for a workout detail modal."""
    key_points_html = '\n'.join([f'<li>{point.strip()}</li>' for point in workout_data['key_points'] if point.strip()])
    
    # Add pace chart link for Pre 30/40
    pace_chart_link = ''
    if workout_id == 'pre-30-40':
        pace_chart_link = '<div class="pace-chart-link"><a href="STX_XC_800m_Rep_Paces_by_Group.html" target="_blank">📊 View Pre 30/40 Pace Chart</a></div>'
    
    return f'''
    <div id="modal-{workout_id}" class="modal">
        <div class="modal-content">
            <span class="modal-close" onclick="closeModal('{workout_id}')">&times;</span>
            <h2>{workout_data['short_name']}</h2>
            {pace_chart_link}
            <div class="modal-section">
                <h3>Overview</h3>
                <p>{workout_data['full_description']}</p>
            </div>
            <div class="modal-section">
                <h3>Key Points</h3>
                <ul class="key-points">
                    {key_points_html}
                </ul>
            </div>
            {f'<div class="modal-section"><h3>Pace</h3><p>{workout_data["pace_info"]}</p></div>' if workout_data['pace_info'] else ''}
            {f'<div class="modal-section"><h3>Duration</h3><p>{workout_data["duration"]}</p></div>' if workout_data['duration'] else ''}
        </div>
    </div>'''


def calculate_group_totals(workouts):
    """Calculate varsity and JV weekly mileage for each group."""
    group_mileage = defaultdict(lambda: {'Varsity': 0.0, 'JV': 0.0, 'All': 0.0})
    
    for day, status, group, pre, workout, post, miles, groups_file, workout_id in workouts:
        miles_val = parse_mileage(miles)
        group_mileage[group][status] += miles_val
    
    totals = {}
    for group, mileage in group_mileage.items():
        varsity_total = mileage['All'] + mileage['Varsity']
        jv_total = mileage['All'] + mileage['JV']
        totals[group] = (varsity_total, jv_total)
    
    return totals


def format_mileage_display(varsity_miles, jv_miles):
    """Format mileage for display."""
    if varsity_miles == jv_miles:
        return str(int(varsity_miles)) if varsity_miles == int(varsity_miles) else str(varsity_miles)
    else:
        jv_str = str(int(jv_miles)) if jv_miles == int(jv_miles) else str(jv_miles)
        varsity_str = str(int(varsity_miles)) if varsity_miles == int(varsity_miles) else str(varsity_miles)
        return f"{jv_str}-{varsity_str}"


def generate_html(week_num, workouts, totals, library):
    """Generate complete HTML with workout details."""
    
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    schedule = {day: {'Varsity': [], 'JV': [], 'All': []} for day in days}
    day_groups_files = {}  # Track groups file for each day
    
    # Track which workouts have details
    used_workout_ids = set()
    
    for day, status, group, pre, workout, post, miles, groups_file, workout_id in workouts:
        day_title = day.title()
        if day_title not in schedule:
            continue
        schedule[day_title][status].append((group, pre, workout, post, miles, workout_id))
        if workout_id:
            used_workout_ids.add(workout_id)
        # Store groups file for this day (same for all workouts on this day)
        if groups_file and day_title not in day_groups_files:
            day_groups_files[day_title] = groups_file
        
        # Check for workout-specific pace pages for this day
        if day_title not in day_groups_files or day_groups_files[day_title] == 'athlete_groups.html':
            # Only override if workout has parseable paces
            if has_parseable_paces(workout):
                pace_filename = get_workout_pace_filename(day_title, week_num, status if status != 'All' else '')
                if exists(pace_filename):
                    day_groups_files[day_title] = pace_filename
    
    # Generate totals section
    groups = ['Gold', 'Green', 'White', 'Freshman']
    totals_html = []
    for group in groups:
        group_lower = group.lower()
        varsity_miles, jv_miles = totals.get(group, (0, 0))
        display = format_mileage_display(varsity_miles, jv_miles)
        totals_html.append(f'''        <div class="total {group_lower}" onclick="filterGroup('{group}')" id="total-{group}">
            <div class="total-label">{group}</div>
            <div class="total-miles">{display}</div>
        </div>''')
    
    # HTML template with modal styles
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>STX Training Week {week_num}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif; max-width: 1000px; margin: 20px auto; padding: 0 20px; background: #fafafa; }}
        h1 {{ color: #2c5530; border-bottom: 3px solid #4a7c59; padding-bottom: 10px; }}
        .subtitle {{ color: #666; margin-bottom: 20px; }}
        .totals {{ display: flex; gap: 10px; margin: 20px 0; flex-wrap: wrap; }}
        .total {{ padding: 15px 20px; background: white; border-radius: 6px; flex: 1; min-width: 140px; text-align: center; cursor: pointer; transition: all 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .total:hover {{ transform: translateY(-2px); box-shadow: 0 2px 6px rgba(0,0,0,0.15); }}
        .total.gold {{ border-left: 4px solid #DAA520; }}
        .total.gold.active {{ background: #DAA520; color: white; }}
        .total.green {{ border-left: 4px solid #4a7c59; }}
        .total.green.active {{ background: #4a7c59; color: white; }}
        .total.white {{ border-left: 4px solid #888; }}
        .total.white.active {{ background: #888; color: white; }}
        .total.freshman {{ border-left: 4px solid #4169E1; }}
        .total.freshman.active {{ background: #4169E1; color: white; }}
        .total-label {{ font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 5px; }}
        .total-miles {{ font-size: 1.8rem; font-weight: 700; }}
        .filters {{ margin: 20px 0; text-align: center; }}
        .filter-btn {{ padding: 8px 16px; margin: 0 5px 5px 0; border: 2px solid #4a7c59; background: white; color: #4a7c59; border-radius: 4px; cursor: pointer; font-size: 0.9rem; transition: all 0.2s; }}
        .filter-btn:hover, .filter-btn.active {{ background: #4a7c59; color: white; }}
        
        /* Week Notes Section */
        .week-notes {{ 
            margin: 25px 0; 
            border-radius: 8px; 
            overflow: hidden; 
            background: #FFF9E6; 
            border: 3px solid #DAA520; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        }}
        .notes-header {{ 
            background: linear-gradient(135deg, #DAA520 0%, #B8860B 100%); 
            padding: 15px 20px; 
            color: white; 
            font-size: 1.2rem; 
            font-weight: 700; 
            letter-spacing: 0.5px; 
        }}
        .notes-content {{ 
            padding: 20px; 
            color: #333; 
        }}
        .notes-content p {{ 
            margin: 0 0 10px 0; 
        }}
        .notes-content ul {{ 
            margin: 10px 0 0 20px; 
        }}
        .notes-content li {{ 
            margin-bottom: 5px; 
        }}
        
        .day {{ margin: 25px 0; border-radius: 8px; overflow: hidden; background: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .day-header {{ 
            background: linear-gradient(135deg, #2c5530 0%, #4a7c59 100%); 
            padding: 15px 20px; 
            color: white; 
            font-size: 1.2rem; 
            font-weight: 700; 
            letter-spacing: 0.5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .groups-btn {{
            background: rgba(255, 255, 255, 0.2);
            color: white;
            padding: 6px 12px;
            border-radius: 4px;
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 600;
            transition: all 0.2s;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }}
        .groups-btn:hover {{
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-1px);
        }}
        .day-content {{ padding: 20px; }}
        .status-section {{ margin-bottom: 25px; }}
        .status-section:last-child {{ margin-bottom: 0; }}
        .status-title {{ font-size: 1.1rem; font-weight: 700; color: #2c5530; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 2px solid #e0e0e0; }}
        .section {{ margin-bottom: 20px; }}
        .section:last-child {{ margin-bottom: 0; }}
        .section-label {{ font-size: 0.8rem; font-weight: 700; text-transform: uppercase; color: #666; margin-bottom: 10px; letter-spacing: 0.5px; }}
        .workout-item {{ padding: 10px 15px; margin-bottom: 8px; border-radius: 4px; display: flex; align-items: center; gap: 12px; transition: all 0.2s; }}
        .workout-item:last-child {{ margin-bottom: 0; }}
        .workout-item.hidden {{ display: none; }}
        .workout-item.gold {{ background: #FFF9E6; border-left: 4px solid #DAA520; }}
        .workout-item.green {{ background: #F0F9F0; border-left: 4px solid #4a7c59; }}
        .workout-item.white {{ background: #F5F5F5; border-left: 4px solid #888; }}
        .workout-item.freshman {{ background: #E6F0FF; border-left: 4px solid #4169E1; }}
        .workout-item:hover {{ transform: translateX(5px); }}
        .group-badge {{ font-weight: 700; min-width: 80px; font-size: 0.9rem; text-transform: uppercase; }}
        .group-badge.gold {{ color: #B8860B; }}
        .group-badge.green {{ color: #2c5530; }}
        .group-badge.white {{ color: #555; }}
        .group-badge.freshman {{ color: #1E3A8A; }}
        .workout-desc {{ flex: 1; font-size: 0.95rem; display: flex; align-items: center; gap: 8px; }}
        .workout-details {{ flex: 1; display: flex; flex-direction: column; gap: 4px; }}
        .workout-pre, .workout-post {{ font-size: 0.85rem; color: #666; }}
        .workout-pre {{ font-style: italic; }}
        .workout-post {{ font-style: italic; }}
        .ref-link {{ 
            color: #4a7c59; 
            text-decoration: none; 
            border-bottom: 1px dotted #4a7c59;
            transition: all 0.2s;
        }}
        .ref-link:hover {{ 
            color: #2c5530; 
            border-bottom-style: solid;
        }}
        .pace-link {{
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
        }}
        .pace-link:hover {{
            background: #1565c0;
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        .workout-miles {{ font-weight: 700; font-size: 1rem; white-space: nowrap; }}
        .info-icon {{ 
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
        }}
        .info-icon:hover {{
            background: #2c5530;
            transform: scale(1.1);
        }}
        
        /* Modal Styles */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.6);
            overflow-y: auto;
        }}
        .modal.active {{ display: flex; align-items: center; justify-content: center; }}
        .modal-content {{
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
        }}
        .modal-close {{
            position: absolute;
            top: 15px;
            right: 20px;
            font-size: 2rem;
            font-weight: 700;
            color: #999;
            cursor: pointer;
            transition: color 0.2s;
        }}
        .modal-close:hover {{ color: #333; }}
        .modal-content h2 {{
            color: #2c5530;
            margin: 0 0 20px 0;
            padding-bottom: 10px;
            border-bottom: 3px solid #4a7c59;
        }}
        .modal-section {{
            margin-bottom: 20px;
        }}
        .modal-section h3 {{
            color: #4a7c59;
            font-size: 1.1rem;
            margin: 0 0 10px 0;
        }}
        .modal-section p {{
            color: #333;
            line-height: 1.6;
            margin: 0;
        }}
        .key-points {{
            list-style: none;
            padding: 0;
            margin: 0;
        }}
        .key-points li {{
            padding: 8px 0 8px 25px;
            position: relative;
            color: #333;
            line-height: 1.5;
        }}
        .key-points li:before {{
            content: "→";
            position: absolute;
            left: 0;
            color: #4a7c59;
            font-weight: 700;
        }}
        .pace-chart-link {{
            background: #e8f5e8;
            border: 2px solid #4a7c59;
            border-radius: 6px;
            padding: 12px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .pace-chart-link a {{
            color: #2c5530;
            text-decoration: none;
            font-weight: 600;
            font-size: 1.05rem;
        }}
        .pace-chart-link a:hover {{
            color: #4a7c59;
            text-decoration: underline;
        }}
        
        @media (max-width: 768px) {{
            .totals {{ flex-direction: column; }}
            .workout-item {{ flex-direction: column; align-items: flex-start; gap: 8px; }}
            .workout-miles {{ align-self: flex-end; }}
            .modal-content {{ padding: 20px; margin: 10px; }}
        }}
    </style>
</head>
<body>
    <h1>🏃 STX Training - Week {week_num}</h1>
    <div class="subtitle"><strong>Training Week</strong></div>
    
    <div class="totals">
{chr(10).join(totals_html)}
    </div>
    
    <div class="filters">
        <button class="filter-btn active" onclick="showAll()">Show All</button>
        <button class="filter-btn" onclick="filterGroup('Gold')">Gold</button>
        <button class="filter-btn" onclick="filterGroup('Green')">Green</button>
        <button class="filter-btn" onclick="filterGroup('White')">White</button>
        <button class="filter-btn" onclick="filterGroup('Freshman')">Freshman</button>
    </div>
    
    <!-- ============================================================
         WEEK NOTES SECTION
         To activate: Remove the opening and closing comment tags
         To edit: Replace the text between <p> tags below
         ============================================================ -->
    <!--
    <div class="week-notes">
        <div class="notes-header">📝 Week Notes</div>
        <div class="notes-content">
            <p><strong>Important:</strong> Add your notes here!</p>
            <p>Examples:</p>
            <ul>
                <li>Meet schedule changes</li>
                <li>Special workout modifications</li>
                <li>Weather considerations</li>
                <li>Reminders for the week</li>
            </ul>
        </div>
    </div>
    -->
    <!-- ============================================================ -->
    '''
    
    # Generate day sections
    for day in days:
        if not any(schedule[day].values()):
            continue
        
        # Check if this day has a groups file
        groups_button = ''
        if day in day_groups_files:
            groups_file = day_groups_files[day]
            # Determine button text based on file type
            if 'workout-groups_' in groups_file:
                button_text = '🎯 Workout Paces'
                button_title = 'View paces for this workout'
            else:
                button_text = '👥 Groups'
                button_title = 'View training groups'
            groups_button = f' <a href="{groups_file}" target="_blank" class="groups-btn" title="{button_title}">{button_text}</a>'
            
        html += f'''
    <div class="day">
        <div class="day-header">
            <span>{day.upper()}</span>{groups_button}
        </div>
        <div class="day-content">'''
        
        for status in ['Varsity', 'JV', 'All']:
            workouts_list = schedule[day][status]
            if not workouts_list:
                continue
            
            if status != 'All':
                # Use proper label (don't just add 's' for Varsity/JV)
                status_label = status  # "Varsity" or "JV" without modification
                html += f'''
            <div class="status-section">
                <div class="status-title">{status_label}</div>'''
            
            html += '''
                <div class="section">
                    <div class="section-label">WORKOUT</div>'''
            
            for group, pre, workout, post, miles, workout_id in sorted(workouts_list, key=lambda x: groups.index(x[0]) if x[0] in groups else 999):
                group_lower = group.lower()
                miles_display = 'REST' if parse_mileage(miles) == 0 else f"{miles} mi"
                
                # Add info icon if workout has details
                info_icon = f'<span class="info-icon" onclick="openModal(\'{workout_id}\')" title="Click for workout details">i</span>' if workout_id else ''
                
                # Check for workout pace page
                pace_page_link = ''
                if has_parseable_paces(workout):
                    pace_filename = get_workout_pace_filename(day, week_num, status if status != 'All' else '')
                    if exists(pace_filename):
                        pace_page_link = f'<a href="{pace_filename}" class="pace-link" target="_blank">Workout Paces</a>'
                
                # Create reference links for Pre and Post
                pre_html = create_reference_links(pre) if pre else ''
                post_html = create_reference_links(post) if post else ''
                
                html += f'''
                    <div class="workout-item {group_lower}" data-group="{group}">
                        <div class="group-badge {group_lower}">{group}</div>
                        <div class="workout-details">
                            {f'<div class="workout-pre">{pre_html}</div>' if pre else ''}
                            <div class="workout-desc">
                                <span>{workout}</span>
                                {info_icon}
                                {pace_page_link}
                            </div>
                            {f'<div class="workout-post">{post_html}</div>' if post else ''}
                        </div>
                        <div class="workout-miles">{miles_display}</div>
                    </div>'''
            
            html += '''
                </div>'''
            
            if status != 'All':
                html += '''
            </div>'''
        
        html += '''
        </div>
    </div>'''
    
    # Add modals for workouts with details
    for workout_id in used_workout_ids:
        if workout_id in library:
            html += generate_workout_modal_html(workout_id, library[workout_id])
    
    # Add JavaScript
    html += '''

    <script>
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
    </script>
</body>
</html>'''
    
    return html


def main():
    if len(sys.argv) < 2:
        print("Usage: python week_schedule_enhanced.py <week_number>")
        print("   or: python week_schedule_enhanced.py <csv_file> [workout_library.csv]")
        sys.exit(1)
    
    # Check if argument is just a week number (e.g., "36")
    if sys.argv[1].isdigit():
        week_num = sys.argv[1]
        # Look in weekly_schedules folder
        input_file = Path('weekly_schedules') / f'week{week_num}.csv'
    else:
        # Full file path provided
        input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"Error: {input_file} not found")
        sys.exit(1)
    
    # Determine workout library path
    if len(sys.argv) >= 3:
        # Explicit library path provided
        library_path = Path(sys.argv[2])
    else:
        # Auto-detect: look in current directory first, then input file's directory
        library_path = Path('workout_library.csv')
        if not library_path.exists():
            library_path = input_file.parent / 'workout_library.csv'
    
    # Load workout library
    library = load_workout_library(library_path)
    if library:
        print(f"✓ Loaded {len(library)} workouts from library")
    else:
        print("⚠ No workout library found - continuing without workout details")
    
    # Day name mapping
    day_map = {
        'Mon': 'Monday',
        'Tue': 'Tuesday', 
        'Wed': 'Wednesday',
        'Thu': 'Thursday',
        'Fri': 'Friday',
        'Sat': 'Saturday',
        'Sun': 'Sunday'
    }
    
    # Parse CSV
    workouts = []
    with open(input_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            day_raw = row.get('Day', '').strip()
            day = day_map.get(day_raw, day_raw)
            
            status = row.get('Status', 'All').strip() or 'All'
            group = row.get('Group', '').strip()
            
            pre = row.get('Pre', '').strip()
            workout = row.get('Workout', '').strip() or row.get('Main_Workout', '').strip()
            post = row.get('Post', '').strip()
            miles = row.get('Miles', '0').strip()
            groups_file = row.get('Groups', '').strip()
            
            # Check for explicit Workout_ID column, otherwise try to match
            workout_id = row.get('Workout_ID', '').strip()
            if not workout_id and library:
                workout_id, _ = find_workout_match(workout, library)
            
            if day and group and workout:
                workouts.append((day, status, group, pre, workout, post, miles, groups_file, workout_id))
    
    if not workouts:
        print("Error: No valid workouts found in CSV")
        sys.exit(1)
    
    # Extract week number
    week_num = ''.join(c for c in input_file.stem if c.isdigit()) or '1'
    
    # Calculate totals
    totals = calculate_group_totals(workouts)
    
    # Generate HTML
    html = generate_html(week_num, workouts, totals, library)
    
    # Write output
    output_file = input_file.stem + '_output.html'
    with open(output_file, 'w') as f:
        f.write(html)
    
    print(f"✓ Generated {output_file}")
    
    # Count workouts with details
    workouts_with_details = sum(1 for _, _, _, _, _, _, _, _, wid in workouts if wid)
    print(f"  - {workouts_with_details} workouts linked to detail pages")
    
    print("\nWeekly Mileage:")
    print("Group      Varsity  JV")
    print("-" * 35)
    for group in ['Gold', 'Green', 'White', 'Freshman']:
        varsity_miles, jv_miles = totals.get(group, (0, 0))
        varsity_str = f"{varsity_miles:.0f}" if varsity_miles == int(varsity_miles) else f"{varsity_miles:.1f}"
        jv_str = f"{jv_miles:.0f}" if jv_miles == int(jv_miles) else f"{jv_miles:.1f}"
        print(f"{group:9s}  {varsity_str:>6s}   {jv_str:>6s}")


if __name__ == '__main__':
    main()
