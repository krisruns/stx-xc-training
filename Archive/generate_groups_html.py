import csv
from collections import defaultdict

# Read the CSV file
groups = defaultdict(list)

with open('athlete_groups.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        athlete_name = row['Athlete']
        group_num = int(row['Group'])
        groups[group_num].append(athlete_name)

# Sort groups by group number and athletes alphabetically within each group
sorted_groups = sorted(groups.items())

# Generate HTML
html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>STX XC Training Groups</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        
        h1 {
            text-align: center;
            color: #003366;
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid #003366;
        }
        
        .groups-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
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
        
        .group-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .group-header {
            font-size: 1.5em;
            font-weight: bold;
            color: #003366;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }
        
        .athlete-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .athlete-list li {
            padding: 8px 0;
            border-bottom: 1px solid #f0f0f0;
            color: #555;
        }
        
        .athlete-list li:last-child {
            border-bottom: none;
        }
        
        .athlete-list li:hover {
            color: #003366;
            background-color: #f8f8f8;
            padding-left: 5px;
            transition: all 0.2s;
        }
        
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .groups-container {
                grid-template-columns: 1fr;
            }
            
            h1 {
                font-size: 1.5em;
            }
        }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #777;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <h1>St. Xavier XC/T&F Training Groups</h1>
    
    <div class="groups-container">
'''

# Add each group
for group_num, athletes in sorted_groups:
    html_content += f'''        <div class="group-card">
            <div class="group-header">Group {group_num}</div>
            <ul class="athlete-list">
'''
    
    # Sort athletes alphabetically within the group
    for athlete_name in sorted(athletes):
        html_content += f'                <li>{athlete_name}</li>\n'
    
    html_content += '''            </ul>
        </div>
'''

# Close HTML
html_content += '''    </div>
    
    <div class="footer">
        St. Xavier High School Cross Country
    </div>
</body>
</html>
'''

# Write to file
with open('athlete_groups.html', 'w') as f:
    f.write(html_content)

print("HTML file created successfully!")
print(f"\nGenerated {len(sorted_groups)} groups with {sum(len(athletes) for _, athletes in sorted_groups)} total athletes")
