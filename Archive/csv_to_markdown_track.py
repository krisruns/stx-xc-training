#!/usr/bin/env python3
"""
Convert weekly TRACK training CSV to markdown format (handles 6 groups)
Usage: python csv_to_markdown_track.py week25_schedule.csv
"""

import csv
from collections import defaultdict
import sys

def read_schedule(csv_file):
    """Read the CSV schedule file"""
    schedule = defaultdict(lambda: defaultdict(dict))
    totals = defaultdict(int)
    week_info = {}
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            week = row['Week']
            day = row['Day']
            group = row['Group']
            
            # Store week number for header
            week_info['week'] = week
            if row['Notes'] and not week_info.get('phase'):
                week_info['phase'] = row['Notes']
            
            # Store workout details
            schedule[day][group] = {
                'pre': row['Pre'],
                'main': row['Main_Workout'],
                'post': row['Post'],
                'miles': float(row['Miles']) if row['Miles'] else 0,
                'notes': row['Notes']
            }
            
            # Calculate totals
            totals[group] += float(row['Miles']) if row['Miles'] else 0
    
    return schedule, totals, week_info

def generate_markdown(schedule, totals, week_info):
    """Generate markdown from schedule data"""
    
    # Week header
    md = f"# Track Week {week_info['week']} Training Schedule\n"
    phase = week_info.get('phase', 'Base Building')
    md += f"**{phase}**\n\n"
    
    # Weekly totals with color indicators
    md += "## 📊 Weekly Mileage Totals\n\n"
    md += "**JV Groups:**\n"
    md += f"🔵 **Freshman:** {totals.get('Freshman', 0):.0f} mi | "
    md += f"⚪ **White:** {totals.get('White', 0):.0f} mi | "
    md += f"🟢 **Green JV:** {totals.get('Green JV', 0):.0f} mi | "
    md += f"🟡 **Gold JV:** {totals.get('Gold JV', 0):.0f} mi\n\n"
    md += "**Varsity Groups:**\n"
    md += f"🟢 **Green Varsity:** {totals.get('Green Varsity', 0):.0f} mi | "
    md += f"🟡 **Gold Varsity:** {totals.get('Gold Varsity', 0):.0f} mi\n\n"
    
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
        
        # Get all unique pre-work
        pre_work = set()
        for group in ['Freshman', 'White', 'Green JV', 'Green Varsity', 'Gold JV', 'Gold Varsity']:
            if group in schedule[day] and schedule[day][group]['pre']:
                pre_work.add(schedule[day][group]['pre'])
        
        if pre_work:
            md += f"**PRE-WORK:** {', '.join(pre_work)}\n\n"
        
        # Main workouts by group
        md += "**WORKOUT:**\n\n"
        
        # JV Groups
        md += "*JV Groups:*\n"
        for group in ['Freshman', 'White', 'Green JV', 'Gold JV']:
            if group not in schedule[day]:
                continue
            
            workout = schedule[day][group]
            emoji = {'Freshman': '🔵', 'White': '⚪', 'Green JV': '🟢', 'Gold JV': '🟡'}[group]
            main = workout['main'] or 'REST'
            miles = f"{workout['miles']:.0f} mi" if workout['miles'] > 0 else 'REST'
            
            md += f"- {emoji} **{group}:** {main} — *{miles}*\n"
        
        # Varsity Groups
        md += "\n*Varsity Groups:*\n"
        for group in ['Green Varsity', 'Gold Varsity']:
            if group not in schedule[day]:
                continue
            
            workout = schedule[day][group]
            emoji = {'Green Varsity': '🟢', 'Gold Varsity': '🟡'}[group]
            main = workout['main'] or 'REST'
            miles = f"{workout['miles']:.0f} mi" if workout['miles'] > 0 else 'REST'
            
            md += f"- {emoji} **{group}:** {main} — *{miles}*\n"
        
        # Get all unique post-work
        post_work = set()
        for group in ['Freshman', 'White', 'Green JV', 'Green Varsity', 'Gold JV', 'Gold Varsity']:
            if group in schedule[day] and schedule[day][group]['post']:
                post_work.add(schedule[day][group]['post'])
        
        if post_work:
            md += f"\n**POST-WORK:** {', '.join(post_work)}\n"
        
        md += "\n---\n\n"
    
    # Footer with legend
    md += "## 🔑 Key\n\n"
    md += "**Training Groups:**\n"
    md += "- 🔵 Freshman | ⚪ White | 🟢 Green (JV & Varsity) | 🟡 Gold (JV & Varsity)\n\n"
    md += "**Phase:** All mileage shown is EASY running to establish aerobic base before track workouts begin\n"
    
    return md

def main():
    if len(sys.argv) < 2:
        print("Usage: python csv_to_markdown_track.py <csv_file>")
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
