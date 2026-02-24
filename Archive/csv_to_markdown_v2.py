#!/usr/bin/env python3
"""
Convert weekly training CSV to markdown format (handles optional Racer/Non-Racer status)
Usage: python csv_to_markdown.py week12_schedule.csv
"""

import csv
from collections import defaultdict
import sys

def read_schedule(csv_file):
    """Read the CSV schedule file"""
    schedule = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    totals = defaultdict(int)
    week_info = {}
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            week = row['Week']
            day = row['Day']
            group = row['Group']
            status = row.get('Status', '').strip()  # Could be 'Racer', 'Non-Racer', or blank
            
            # Store week number for header
            week_info['week'] = week
            if row.get('Notes') and not week_info.get('phase'):
                week_info['phase'] = row['Notes']
            
            # Store workout details
            # Structure: schedule[day][status][group] = {...}
            # If status is blank, use 'normal' as the key
            status_key = status if status else 'normal'
            
            schedule[day][status_key][group] = {
                'pre': row.get('Pre', ''),
                'main': row.get('Main_Workout', ''),
                'post': row.get('Post', ''),
                'miles': float(row.get('Miles', 0)) if row.get('Miles') else 0,
                'notes': row.get('Notes', '')
            }
            
            # Calculate totals
            totals[group] += float(row.get('Miles', 0)) if row.get('Miles') else 0
    
    return schedule, totals, week_info

def generate_markdown(schedule, totals, week_info):
    """Generate markdown from schedule data"""
    
    # Week header
    md = f"# Week {week_info['week']} Training Schedule\n"
    phase = week_info.get('phase', 'Training Week')
    md += f"**{phase}**\n\n"
    
    # Weekly totals with color indicators
    md += "## 📊 Weekly Mileage Totals\n"
    md += f"🟡 **Gold:** {totals.get('Gold', 0):.0f} mi | "
    md += f"🟢 **Green:** {totals.get('Green', 0):.0f} mi | "
    md += f"⚪ **White:** {totals.get('White', 0):.0f} mi | "
    md += f"🔵 **Freshman:** {totals.get('Freshman', 0):.0f} mi\n\n"
    
    md += "---\n\n"
    
    # Day-by-day schedule
    days_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    day_names = {
        'Mon': 'MONDAY',
        'Tue': 'TUESDAY', 
        'Wed': 'WEDNESDAY',
        'Thu': 'THURSDAY',
        'Fri': 'FRIDAY',
        'Sat': 'SATURDAY',
        'Sun': 'SUNDAY'
    }
    
    for day in days_order:
        if day not in schedule:
            continue
            
        md += f"## {day_names[day]}\n\n"
        
        # Check if this day has status distinctions (Racer/Non-Racer)
        statuses = list(schedule[day].keys())
        has_status_split = len(statuses) > 1 or (len(statuses) == 1 and statuses[0] != 'normal')
        
        if has_status_split:
            # Day has Racer/Non-Racer split
            for status in ['Racer', 'Non-Racer']:
                if status not in schedule[day]:
                    continue
                
                md += f"### {status}s\n\n"
                
                # Get unique pre-work for this status group
                pre_work = set()
                for group in ['Gold', 'Green', 'White', 'Freshman']:
                    if group in schedule[day][status] and schedule[day][status][group]['pre']:
                        pre_work.add(schedule[day][status][group]['pre'])
                
                if pre_work:
                    md += f"**PRE-WORK:** {', '.join(pre_work)}\n\n"
                
                # Workouts
                md += "**WORKOUT:**\n"
                for group in ['Gold', 'Green', 'White', 'Freshman']:
                    if group not in schedule[day][status]:
                        continue
                    
                    workout = schedule[day][status][group]
                    emoji = {'Gold': '🟡', 'Green': '🟢', 'White': '⚪', 'Freshman': '🔵'}[group]
                    main = workout['main'] or 'REST'
                    miles = f"{workout['miles']:.1f} mi" if workout['miles'] > 0 else 'REST'
                    
                    md += f"- {emoji} **{group}:** {main} — *{miles}*\n"
                
                # Get unique post-work for this status group
                post_work = set()
                for group in ['Gold', 'Green', 'White', 'Freshman']:
                    if group in schedule[day][status] and schedule[day][status][group]['post']:
                        post_work.add(schedule[day][status][group]['post'])
                
                if post_work:
                    md += f"\n**POST-WORK:** {', '.join(post_work)}\n"
                
                md += "\n"
        
        else:
            # Normal day - no status distinction
            day_workouts = schedule[day]['normal']
            
            # Get all unique pre-work
            pre_work = set()
            for group in ['Gold', 'Green', 'White', 'Freshman']:
                if group in day_workouts and day_workouts[group]['pre']:
                    pre_work.add(day_workouts[group]['pre'])
            
            if pre_work:
                md += f"**PRE-WORK:** {', '.join(pre_work)}\n\n"
            
            # Main workouts by group
            md += "**WORKOUT:**\n"
            for group in ['Gold', 'Green', 'White', 'Freshman']:
                if group not in day_workouts:
                    continue
                
                workout = day_workouts[group]
                emoji = {'Gold': '🟡', 'Green': '🟢', 'White': '⚪', 'Freshman': '🔵'}[group]
                main = workout['main'] or 'REST'
                miles = f"{workout['miles']:.1f} mi" if workout['miles'] > 0 else 'REST'
                
                md += f"- {emoji} **{group}:** {main} — *{miles}*\n"
            
            # Get all unique post-work
            post_work = set()
            for group in ['Gold', 'Green', 'White', 'Freshman']:
                if group in day_workouts and day_workouts[group]['post']:
                    post_work.add(day_workouts[group]['post'])
            
            if post_work:
                md += f"\n**POST-WORK:** {', '.join(post_work)}\n"
        
        md += "\n---\n\n"
    
    # Footer with legend
    md += "## 🔑 Key\n\n"
    md += "**Pace Zones:**\n"
    md += "- **@E** = Easy pace (conversational)\n"
    md += "- **@T** = Threshold pace (comfortably hard, 15K-HM effort)\n"
    md += "- **@I** = Interval pace (3K-5K race effort)\n"
    md += "- **@R** = Repetition pace (mile pace or faster)\n\n"
    md += "**Training Groups:**\n"
    md += "- 🟡 Gold | 🟢 Green | ⚪ White | 🔵 Freshman\n"
    
    return md

def main():
    if len(sys.argv) < 2:
        print("Usage: python csv_to_markdown.py <csv_file>")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    # Read and process
    schedule, totals, week_info = read_schedule(csv_file)
    
    # Generate markdown
    markdown = generate_markdown(schedule, totals, week_info)
    
    # Output to file
    output_file = f"week{week_info['week']}_schedule.md"
    with open(output_file, 'w') as f:
        f.write(markdown)
    
    print(f"✅ Generated: {output_file}")
    print(markdown)

if __name__ == "__main__":
    main()
