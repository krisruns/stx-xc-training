#!/usr/bin/env python3
"""
Generate workout-specific pace pages from athlete_groups.html template.
Adds workout-specific paces to the existing athlete group structure.
"""

import pandas as pd
import re
from pathlib import Path
from bs4 import BeautifulSoup
import sys
from workout_pace_generator import WorkoutPacePageGenerator

# ============================================================================
# PACE DATA LOADING
# ============================================================================

def load_training_paces(csv_path='training_paces.csv'):
    """
    Load the training paces CSV and create a lookup dictionary.
    
    Returns:
        dict: {VDOT: {'200m_mile': seconds, '400m_5k': seconds, ...}}
    """
    # Read CSV, skipping the first 3 header rows
    df = pd.read_csv(csv_path, skiprows=3)
    
    # Column mapping based on the CSV structure
    pace_columns = {
        # Tempo paces
        'tempo_400': 10,
        'tempo_1000': 11,
        'tempo_mile': 12,
        
        # Pre 30/40 paces
        'pre_200': 13,
        
        # CV Pace (10k pace)
        'cv_400': 17,
        'cv_800': 18,
        'cv_1000': 19,
        'cv_1200': 20,
        
        # 5K Pace (Interval pace)
        '5k_400': 21,
        '5k_1000': 22,
        '5k_1200': 23,
        '5k_mile': 24,
        
        # Mile Pace
        'mile_200': 25,
        'mile_300': 26,
        'mile_400': 27,
        'mile_600': 28,
        'mile_800': 29,
        
        # 800 Pace
        '800_200': 30,
        '800_300': 31,
        '800_400': 32,
        
        # 400 Pace
        '400_100': 33,
        '400_150': 34,
        '400_200': 35,
    }
    
    # Create VDOT lookup dictionary
    vdot_paces = {}
    
    for idx, row in df.iterrows():
        vdot = int(row.iloc[0])  # First column is VDOT
        
        pace_dict = {}
        for pace_key, col_idx in pace_columns.items():
            try:
                value = row.iloc[col_idx]
                # Convert to seconds
                if pd.notna(value) and value != '-----':
                    if isinstance(value, str) and ':' in value:
                        parts = value.split(':')
                        seconds = int(parts[0]) * 60 + int(parts[1])
                    else:
                        seconds = int(value)
                    pace_dict[pace_key] = seconds
            except (IndexError, ValueError):
                pass
        
        vdot_paces[vdot] = pace_dict
    
    return vdot_paces

# ============================================================================
# WORKOUT PARSING
# ============================================================================

def parse_workout_description(description):
    """
    Parse workout description to extract pace requirements.
    
    Examples:
        "2x200@mile (200j)" -> [('200', 'mile')]
        "12x400@5k(200j)" -> [('400', '5k')]
        "2x200@mile (200j) + 12x400@5k(200j)+ 2x200@800 (60s)" 
            -> [('200', 'mile'), ('400', '5k'), ('200', '800')]
        "3x[600@3k (2:00) + 400@mile (2:00) + 200@800 (1:00)]"
            -> [('600', '3k'), ('400', 'mile'), ('200', '800')]
    
    Returns:
        list of tuples: [(distance, pace_type), ...]
    """
    if not description or pd.isna(description):
        return []
    
    pace_needs = []
    
    # First, check for bracketed repetitions: 3x[600@3k + 400@mile + 200@800]
    # Pattern: [number]x[...contents...]
    bracket_pattern = r'(\d+)x\[(.*?)\]'
    bracket_matches = re.findall(bracket_pattern, description.lower())
    
    # Process bracketed content
    for reps, bracketed_content in bracket_matches:
        # Parse all pace patterns inside the brackets
        inner_pattern = r'(\d+)(?:m)?@([\w\d]+)'
        inner_matches = re.findall(inner_pattern, bracketed_content)
        for distance, pace_type in inner_matches:
            pace_needs.append((distance, pace_type))
    
    # Then, look for non-bracketed patterns: [number]x[distance]@[pace_type]
    # But exclude anything that's inside brackets (already processed)
    # Remove bracketed sections first
    desc_without_brackets = re.sub(r'\d+x\[.*?\]', '', description.lower())
    
    # Pattern: [number]x[distance]@[pace_type]
    pattern = r'(\d+)x(\d+)(?:m)?@([\w\d]+)'
    matches = re.findall(pattern, desc_without_brackets)
    
    for match in matches:
        reps, distance, pace_type = match
        pace_needs.append((distance, pace_type))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_paces = []
    for item in pace_needs:
        if item not in seen:
            seen.add(item)
            unique_paces.append(item)
    
    return unique_paces

def extract_group_vdot_ranges(html_content):
    """
    Extract VDOT ranges for each group from the athlete_groups.html file.
    
    Returns:
        dict: {group_num: {'min_vdot': X, 'max_vdot': Y}}
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    group_ranges = {}
    
    for group_num in range(1, 8):
        vdots = []
        group_card = soup.find('div', class_='group-header', string=f'Group {group_num}')
        if group_card:
            parent = group_card.parent
            vdot_elements = parent.find_all('span', class_='vdot-value')
            for elem in vdot_elements:
                text = elem.get_text()
                match = re.search(r'VDOT:\s*(\d+)', text)
                if match:
                    vdots.append(int(match.group(1)))
        
        if vdots:
            group_ranges[group_num] = {
                'min_vdot': min(vdots),
                'max_vdot': max(vdots)
            }
    
    return group_ranges

def get_pace_range_for_group(vdot_paces, min_vdot, max_vdot, distance, pace_type):
    """
    Get the pace range for a specific VDOT range, distance, and pace type.
    
    Args:
        vdot_paces: Dictionary from load_training_paces()
        min_vdot: Minimum VDOT in group
        max_vdot: Maximum VDOT in group
        distance: "200", "400", "800", etc.
        pace_type: "mile", "5k", "800", "400", "tempo", etc.
    
    Returns:
        (min_seconds, max_seconds) or None if not found
    """
    # Normalize pace type aliases
    pace_aliases = {
        'i': '5k',
        'interval': '5k',
        'rp': '5k',
        't': 'tempo',
        'threshold': 'tempo',
        'r': '400',
        'rep': '400',
        'm': 'mile',
        '3k': 'cv',
        '10k': 'cv',
    }
    
    normalized_pace = pace_aliases.get(pace_type.lower(), pace_type.lower())
    lookup_key = f"{normalized_pace}_{distance}"
    
    try:
        available_vdots = sorted(vdot_paces.keys(), reverse=True)
        
        # Find closest VDOTs
        vdot_high = min([v for v in available_vdots if v >= max_vdot], default=max(available_vdots))
        vdot_low = max([v for v in available_vdots if v <= min_vdot], default=min(available_vdots))
        
        # Higher VDOT = faster = lower time
        pace_fast = vdot_paces[vdot_high].get(lookup_key)
        pace_slow = vdot_paces[vdot_low].get(lookup_key)
        
        if pace_fast and pace_slow:
            return (pace_fast, pace_slow)
        elif pace_fast:
            return (pace_fast, pace_fast)
        elif pace_slow:
            return (pace_slow, pace_slow)
        else:
            return None
            
    except (KeyError, ValueError):
        return None

def format_time(seconds):
    """Convert seconds to display format."""
    if seconds >= 60:
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}:{secs:02d}"
    else:
        return f"{seconds}s"

# ============================================================================
# HTML MODIFICATION
# ============================================================================

def add_paces_to_html(html_content, pace_needs, vdot_paces, workout_desc=""):
    """
    Add workout-specific paces to the athlete_groups.html template.
    
    Args:
        html_content: Content of athlete_groups.html
        pace_needs: [(distance, pace_type), ...]
        vdot_paces: Dictionary from load_training_paces()
        workout_desc: Original workout description
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Update title
    title = soup.find('title')
    if title:
        title.string = 'Workout Paces - STX Training'
    
    # Update main heading
    h1 = soup.find('h1')
    if h1:
        h1.string = 'Workout Paces'
    
    # Add workout description after h1
    if workout_desc:
        workout_div = soup.new_tag('div', **{'class': 'workout-description'})
        workout_div.string = workout_desc
        h1.insert_after(workout_div)
        
        # Add CSS for workout description
        style = soup.find('style')
        if style:
            workout_css = """
        .workout-description {
            text-align: center;
            background: #e3f2fd;
            padding: 15px;
            margin: 20px 0;
            border-radius: 8px;
            font-size: 1.1em;
            font-weight: 500;
            color: #1976d2;
        }
        
        .pace-section {
            background: #f0f7ff;
            padding: 15px;
            margin-top: 15px;
            border-radius: 5px;
            border-left: 4px solid #1976d2;
        }
        
        .pace-section h3 {
            margin: 0 0 10px 0;
            color: #1976d2;
            font-size: 1em;
            font-weight: 600;
        }
        
        .pace-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
        }
        
        .pace-item {
            background: white;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #bbdefb;
        }
        
        .pace-label {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 3px;
        }
        
        .pace-value {
            font-size: 1.2em;
            font-weight: bold;
            color: #1976d2;
        }
"""
            style.string = str(style.string) + workout_css
    
    # Extract VDOT ranges from the existing HTML
    group_ranges = extract_group_vdot_ranges(str(soup))
    
    # Add pace section to each group
    for group_num in range(1, 8):
        group_header = soup.find('div', class_='group-header', string=f'Group {group_num}')
        if group_header and group_num in group_ranges:
            parent = group_header.parent
            athlete_list = parent.find('ul', class_='athlete-list')
            
            if athlete_list:
                # Create pace section
                pace_section = soup.new_tag('div', **{'class': 'pace-section'})
                pace_h3 = soup.new_tag('h3')
                pace_h3.string = 'Target Paces'
                pace_section.append(pace_h3)
                
                pace_grid = soup.new_tag('div', **{'class': 'pace-grid'})
                
                min_vdot = group_ranges[group_num]['min_vdot']
                max_vdot = group_ranges[group_num]['max_vdot']
                
                for distance, pace_type in pace_needs:
                    pace_range = get_pace_range_for_group(
                        vdot_paces, min_vdot, max_vdot, distance, pace_type
                    )
                    
                    pace_item = soup.new_tag('div', **{'class': 'pace-item'})
                    
                    pace_label = soup.new_tag('div', **{'class': 'pace-label'})
                    pace_label.string = f"{distance}m @ {pace_type.upper()}"
                    pace_item.append(pace_label)
                    
                    pace_value = soup.new_tag('div', **{'class': 'pace-value'})
                    
                    if pace_range:
                        min_time, max_time = pace_range
                        if min_time == max_time:
                            pace_value.string = format_time(min_time)
                        else:
                            pace_value.string = f"{format_time(min_time)}-{format_time(max_time)}"
                    else:
                        pace_value.string = "N/A"
                    
                    pace_item.append(pace_value)
                    pace_grid.append(pace_item)
                
                pace_section.append(pace_grid)
                
                # Insert pace section before athlete list
                athlete_list.insert_before(pace_section)
    
    return str(soup)

# ============================================================================
# MAIN PROCESSING
# ============================================================================

def process_training_overview(overview_csv, paces_csv, athlete_groups_html, output_dir='output'):
    """
    Read Training Overview CSV and generate workout pace pages.
    """
    # Load pace data
    print("Loading training paces...")
    vdot_paces = load_training_paces(paces_csv)
    print(f"✓ Loaded paces for {len(vdot_paces)} VDOT levels")
    
    # Load athlete groups HTML template
    print(f"\nReading athlete groups template: {athlete_groups_html}")
    with open(athlete_groups_html, 'r') as f:
        athlete_html = f.read()
    print("✓ Loaded athlete groups template")
    
    # Load training overview
    print(f"\nReading training overview: {overview_csv}")
    df = pd.read_csv(overview_csv)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    generated_files = []
    
    # Process each row
    for idx, row in df.iterrows():
        week = row['Week']
        squad = row.iloc[0]  # V or JV
        
        # Process each day
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day in days:
            workout_desc = row[day]
            
            if pd.isna(workout_desc) or workout_desc.strip() == '':
                continue
            
            # Parse what paces are needed
            pace_needs = parse_workout_description(workout_desc)
            
            if not pace_needs:
                continue
            
            # Generate unique filename
            workout_name = f"{day.lower()[:3]}_week{week}"
            if squad and not pd.isna(squad):
                workout_name = f"{squad.lower()}_{workout_name}"
            
            # Add paces to HTML
            modified_html = add_paces_to_html(
                athlete_html,
                pace_needs,
                vdot_paces,
                workout_desc
            )
            
            # Save file
            output_file = output_path / f"workout-groups_{workout_name}.html"
            with open(output_file, 'w') as f:
                f.write(modified_html)
            
            generated_files.append(output_file.name)
            
            pace_summary = ', '.join([f'{d}m@{p}' for d, p in pace_needs])
            print(f"  ✓ {output_file.name:40s} [{pace_summary}]")
    
    print(f"\n✓ Generated {len(generated_files)} workout pace pages in {output_dir}/")
    return generated_files

# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate workout-specific pace pages from athlete_groups.html template'
    )
    parser.add_argument(
        'overview_csv',
        nargs='?',
        default='Training Master - Training_Overview.csv',
        help='Path to training overview CSV (default: Training Master - Training_Overview.csv)'
    )
    parser.add_argument(
        '--paces',
        default='training_paces.csv',
        help='Path to training paces CSV'
    )
    parser.add_argument(
        '--template',
        default='athlete_groups.html',
        help='Path to athlete_groups.html template'
    )
    parser.add_argument(
        '--output',
        default='pace_pages',
        help='Output directory (default: pace_pages)'
    )
    
    args = parser.parse_args()
    
    try:
        generated = process_training_overview(
            args.overview_csv,
            args.paces,
            args.template,
            args.output
        )
        print("\n✅ Success! All workout pace pages generated.")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the following files exist:")
        print(f"  - {args.overview_csv}")
        print(f"  - {args.paces}")
        print(f"  - {args.template}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
