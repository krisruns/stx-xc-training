#!/usr/bin/env python3
"""
Training Overview to Week Schedule CSV Converter
Generates weekly schedules in the STX training format

Usage:
    python overview_to_week_schedule.py Training_Master_-_Training_Overview.csv
"""

import pandas as pd
import csv
import sys
from pathlib import Path

# Standard pre/post workout routines
STANDARD_WARMUPS = {
    'easy_day': "Foot Drills, Dynamics",
    'workout_day': "WU, Dynamics",
    'easy_recovery': "Foot Drills, Awesomizer",
    'long_run_day': "Awesomizer, Lunge Matrix",
    'race_day': "Race Day WU",
    'rest_day': "Foot Drills, Mobility A/B"
}

STANDARD_COOLDOWNS = {
    'easy_day': "Strides; Mobility/Strength A",
    'workout_day': "Mobility/Strength B",
    'long_run_day': "Strides; Mobilty A, 18s",
    'post_race': "Post Race",
    'rest_day': "Strength",
    'progression_lr': "Mobility A, 21s"
}

# Group name mapping
GROUP_NAMES = {
    'GOLD': 'Gold',
    'GREEN': 'Green', 
    'WHITE': 'White',
    'FRESHMAN': 'Freshman'
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

def get_mileage_for_group(group, workout_desc, weekly_vol):
    """Calculate appropriate mileage based on group and workout type
    
    Maximum mileage caps per group:
    - Gold: 8 mi regular, 12 mi long run
    - Green: 7 mi regular, 10 mi long run
    - White: 6 mi regular, 8 mi long run
    - Freshman: 5 mi regular, 7 mi long run
    
    Time-based workouts (hills, fartlek):
    - 1.5 mi warmup + workout @ 7:00 pace + 1.5 mi cooldown
    """
    desc_lower = str(workout_desc).lower() if workout_desc else ''
    
    # Group scaling factors for different workout types
    group_idx = {'Gold': 0, 'Green': 1, 'White': 2, 'Freshman': 3}
    idx = group_idx.get(group, 3)
    
    # Maximum caps
    max_regular = [8, 7, 6, 5][idx]
    max_long_run = [12, 10, 8, 7][idx]
    
    if 'race' in desc_lower:
        # Race day mileage
        return [4, 4, 3, 3][idx]
    
    elif 'rest' in desc_lower:
        return 0
    
    elif 'hill' in desc_lower:
        # Calculate based on time: 1.5 WU + workout @ 7:00 pace + 1.5 CD
        durations = [35, 30, 25, 20][idx]  # minutes
        workout_miles = durations / 7.0  # 7:00 pace = 7 min/mile
        total = 1.5 + workout_miles + 1.5
        # Round to nearest 0.5 and apply cap
        total = round(total * 2) / 2
        return min(total, max_regular)
    
    elif 'fartlek' in desc_lower or 'pre' in desc_lower:
        # Time-based fartlek/pre workouts
        # Estimate workout portion (conservative)
        if 'pre 40' in desc_lower:
            workout_mins = 40
        elif 'pre 30' in desc_lower:
            workout_mins = 30
        else:
            # Default fartlek estimate based on group
            workout_mins = [35, 30, 25, 20][idx]
        
        workout_miles = workout_mins / 7.0
        total = 1.5 + workout_miles + 1.5
        total = round(total * 2) / 2
        return min(total, max_regular)
    
    elif 'long run' in desc_lower or 'lr' in desc_lower or 'progression' in desc_lower:
        # Long run - approximately 22% of weekly volume, capped at max
        miles = round(weekly_vol * 0.22 * 2) / 2
        return min(miles, max_long_run)
    
    elif 'easy' in desc_lower:
        # Easy day - approximately 13% of weekly volume, capped at max
        miles = round(weekly_vol * 0.13 * 2) / 2
        return min(miles, max_regular)
    
    else:
        # Workout day - approximately 14% of weekly volume, capped at max
        miles = round(weekly_vol * 0.14 * 2) / 2
        return min(miles, max_regular)

def expand_workout_description(desc, group, calculated_miles):
    """Expand general workout description into detailed Main_Workout
    
    Args:
        desc: Workout description from overview
        group: Training group (Gold, Green, White, Freshman)
        calculated_miles: The actual calculated mileage for this workout
    """
    if not desc or pd.isna(desc):
        return ""
    
    desc_str = str(desc).strip()
    desc_lower = desc_str.lower()
    
    # Group-specific scaling for rep counts
    group_idx = {'Gold': 0, 'Green': 1, 'White': 2, 'Freshman': 3}
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

def determine_pre_post(workout_desc, day):
    """Determine appropriate Pre and Post workout routines"""
    desc_lower = str(workout_desc).lower() if workout_desc else ''
    
    # Race day
    if 'race' in desc_lower:
        return STANDARD_WARMUPS['race_day'], STANDARD_COOLDOWNS['post_race']
    
    # Rest day
    elif 'rest' in desc_lower:
        return STANDARD_WARMUPS['rest_day'], STANDARD_COOLDOWNS['rest_day']
    
    # Long run or progression
    elif 'long run' in desc_lower or 'lr' in desc_lower or 'progression' in desc_lower:
        if 'progression' in desc_lower:
            return STANDARD_WARMUPS['workout_day'], STANDARD_COOLDOWNS['progression_lr']
        return STANDARD_WARMUPS['long_run_day'], STANDARD_COOLDOWNS['long_run_day']
    
    # Workout days (hills, fartlek, intervals)
    elif any(x in desc_lower for x in ['hill', 'fartlek', 'pre', 'interval', 'tempo']):
        return STANDARD_WARMUPS['workout_day'], STANDARD_COOLDOWNS['workout_day']
    
    # Day-specific patterns for easy runs
    # Friday easy runs (pre-race)
    elif day == 'Friday':
        return STANDARD_WARMUPS['easy_recovery'], STANDARD_COOLDOWNS['post_race']
    
    # Wednesday easy runs (uses Awesomizer warmup)
    elif day == 'Wednesday':
        return STANDARD_WARMUPS['long_run_day'], STANDARD_COOLDOWNS['long_run_day']
    
    # Monday easy runs (standard)
    elif day == 'Monday':
        return STANDARD_WARMUPS['easy_day'], STANDARD_COOLDOWNS['easy_day']
    
    # Default easy day
    else:
        return STANDARD_WARMUPS['easy_day'], STANDARD_COOLDOWNS['easy_day']

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
    
    for group in ['Gold', 'Green', 'White', 'Freshman']:
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
    output_file = output_dir / f"week{week_num}.csv"
    
    days_full = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    groups = ['Gold', 'Green', 'White', 'Freshman']
    
    # Get volume targets
    volumes = {
        'Gold': week_data.iloc[0]['Vol_Gold'],
        'Green': week_data.iloc[0]['Vol_Green'],
        'White': week_data.iloc[0]['Vol_White'],
        'Freshman': week_data.iloc[0]['Vol_FR']
    }
    
    # Build schedule from V and JV rows
    schedule = {'V': {}, 'JV': {}}
    groups_links = {}  # Store groups file links for each day
    
    for _, row in week_data.iterrows():
        squad = row.iloc[0]
        for day in days_full:
            if day in row and not pd.isna(row[day]) and str(row[day]).strip():
                schedule[squad][day] = str(row[day]).strip()
            
            # Check for Groups column for this day
            groups_col = f'{day}_Groups'  # e.g., "Monday_Groups"
            if groups_col in row and not pd.isna(row[groups_col]) and str(row[groups_col]).strip():
                groups_links[day] = str(row[groups_col]).strip()
    
    # Determine split days
    split_days = set(schedule['V'].keys()) & set(schedule['JV'].keys())
    v_only_days = set(schedule['V'].keys()) - split_days
    
    rows = []
    
    # Generate schedule for each day
    for day_full in days_full:
        day_abbrev = DAY_ABBREV[day_full]
        
        # Check if this day has workouts
        if day_full not in schedule['V'] and day_full not in schedule['JV']:
            continue
        
        # Process each group
        for group in groups:
            weekly_vol = volumes[group]
            if pd.isna(weekly_vol):
                weekly_vol = 0
            
            # Day with split schedule (Racer vs Non-Racer)
            if day_full in split_days:
                # Racer workout (V)
                v_desc = schedule['V'][day_full]
                miles = get_mileage_for_group(group, v_desc, weekly_vol)
                main_workout = expand_workout_description(v_desc, group, miles)
                pre, post = determine_pre_post(v_desc, day_full)
                
                rows.append({
                    'Week': week_num,
                    'Day': day_abbrev,
                    'Group': group,
                    'Status': 'Varsity',
                    'Pre': pre,
                    'Main_Workout': main_workout,
                    'Post': post,
                    'Miles': miles,
                    'Groups': groups_links.get(day_full, ''),
                    'Notes': ''
                })
                
                # Non-Racer workout (JV)
                jv_desc = schedule['JV'][day_full]
                miles = get_mileage_for_group(group, jv_desc, weekly_vol)
                main_workout = expand_workout_description(jv_desc, group, miles)
                pre, post = determine_pre_post(jv_desc, day_full)
                
                rows.append({
                    'Week': week_num,
                    'Day': day_abbrev,
                    'Group': group,
                    'Status': 'JV',
                    'Pre': pre,
                    'Main_Workout': main_workout,
                    'Post': post,
                    'Miles': miles,
                    'Groups': groups_links.get(day_full, ''),
                    'Notes': ''
                })
            
            # V-only day (all athletes do same workout)
            elif day_full in v_only_days:
                v_desc = schedule['V'][day_full]
                miles = get_mileage_for_group(group, v_desc, weekly_vol)
                main_workout = expand_workout_description(v_desc, group, miles)
                pre, post = determine_pre_post(v_desc, day_full)
                
                rows.append({
                    'Week': week_num,
                    'Day': day_abbrev,
                    'Group': group,
                    'Status': '',  # Blank for "All"
                    'Pre': pre,
                    'Main_Workout': main_workout,
                    'Post': post,
                    'Miles': miles,
                    'Groups': groups_links.get(day_full, ''),
                    'Notes': ''
                })
    
    # Sort by day order, then by group, then by status (blanks first, then JV, then Varsity)
    day_order = {day: i for i, day in enumerate(DAY_ABBREV.values())}
    group_order = {g: i for i, g in enumerate(groups)}
    status_order = {'': 0, 'JV': 1, 'Varsity': 2}
    
    df = pd.DataFrame(rows)
    df['_day_ord'] = df['Day'].map(day_order)
    df['_group_ord'] = df['Group'].map(group_order)
    df['_status_ord'] = df['Status'].map(status_order)
    df = df.sort_values(['_day_ord', '_group_ord', '_status_ord'])
    df = df.drop(['_day_ord', '_group_ord', '_status_ord'], axis=1)
    
    # NOTE: Mileage adjustment disabled - using max caps instead
    # Weekly totals may be less than overview targets due to caps
    
    # Replace NaN values with empty strings to prevent CSV parsing issues
    df['Status'] = df['Status'].fillna('')
    df['Groups'] = df['Groups'].fillna('')
    df['Notes'] = df['Notes'].fillna('')
    
    # Save to CSV with QUOTE_MINIMAL and Windows line endings for Excel compatibility
    df.to_csv(output_file, index=False, quoting=csv.QUOTE_MINIMAL, lineterminator='\r\n')
    
    print(f"✓ Created {output_file}")
    
    # Print summary
    print(f"  Week {week_num} schedule:")
    for day_full in days_full:
        if day_full in split_days:
            v_desc = schedule['V'][day_full]
            jv_desc = schedule['JV'][day_full]
            print(f"    {DAY_ABBREV[day_full]}: Varsity={v_desc}, JV={jv_desc}")
        elif day_full in v_only_days:
            print(f"    {DAY_ABBREV[day_full]}: All={schedule['V'][day_full]}")
    
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
