#!/usr/bin/env python3
"""
Workout Pace Page Generator with Printable Group Sheets
Generates HTML pages showing workout paces for each group with built-in print functionality
"""

import re
from typing import List, Dict, Tuple, Optional
import json


class WorkoutPacePageGenerator:
    """Generate workout pace pages with printable group record sheets"""
    
    def __init__(self):
        self.css_styles = self._get_css_styles()
        self.js_script = self._get_javascript()
    
    def parse_workout_description(self, workout_desc: str) -> List[Dict[str, any]]:
        """
        Parse workout description to extract rep structure
        Examples:
            "12x200@mile (200j)+4x200@800 (45s)" 
            "2x200@mile+12x400@5k (200j) + 2x200@800"
        
        Returns list of dicts with: count, distance, pace
        """
        reps = []
        # Pattern: number x distance @ pace
        pattern = r'(\d+)x(\d+)@(\w+)'
        
        for match in re.finditer(pattern, workout_desc):
            reps.append({
                'count': int(match.group(1)),
                'distance': match.group(2),
                'pace': match.group(3).upper()
            })
        
        return reps
    
    def generate_page(self, 
                     workout_description: str,
                     groups: List[Dict],
                     squad_type: str = "Varsity",
                     week_number: Optional[int] = None,
                     day: Optional[str] = None) -> str:
        """
        Generate complete HTML page with workout paces and print functionality
        
        Args:
            workout_description: e.g., "12x200@mile (200j)+4x200@800 (45s)"
            groups: List of group dictionaries with structure:
                {
                    'name': 'Group 1',
                    'paces': {
                        '200m @ MILE': '31s-35s',
                        '200m @ 800': '28s-31s'
                    },
                    'athletes': [
                        {'name': 'Marshall Wilson', 'vdot': 65},
                        {'name': 'Anthony Passafiume', 'vdot': None}  # manual entry
                    ]
                }
            squad_type: "Varsity" or "JV"
            week_number: Optional week number for title
            day: Optional day for title
        
        Returns:
            Complete HTML page as string
        """
        
        # Build title
        title_parts = []
        if squad_type:
            title_parts.append(squad_type)
        if week_number:
            title_parts.append(f"Week {week_number}")
        if day:
            title_parts.append(day)
        
        page_title = " - ".join(title_parts) if title_parts else "Workout Paces"
        
        # Build back link — goes to week page if we know the week, else index
        if week_number:
            back_href = f"../week{week_number:02d}.html"
            back_label = f"← Week {week_number}"
        else:
            back_href = "index.html"
            back_label = "← Schedule"
        
        # Generate HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{page_title} - STX Training</title>
{self.css_styles}
</head>
<body>
<a class="back-btn no-print" href="{back_href}">{back_label}</a>
<h1 class="no-print">Workout Paces{' - ' + page_title if title_parts else ''}</h1>

<div class="workout-description no-print" id="workoutDesc">{workout_description}</div>

<div class="action-buttons no-print">
    <button class="print-btn" onclick="printGroupSheets()">🖨️ Print Group Record Sheets</button>
</div>

<!-- Screen View Groups -->
<div class="groups-container no-print" id="groupsContainer">
</div>

<!-- Print View (hidden on screen) -->
<div id="printContainer" style="display: none;">
</div>

<div class="footer no-print">
    St. Xavier High School Cross Country &amp; Track
</div>

<script>
// Group data structure
const groupsData = {json.dumps(groups, indent=4)};

{self.js_script}
</script>
</body>
</html>"""
        
        return html
    
    def _get_css_styles(self) -> str:
        """Return CSS styles for the page"""
        return """<style>
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
        
        .back-btn {
            display: inline-block;
            margin-bottom: 12px;
            padding: 7px 14px;
            background: white;
            color: #2c5530;
            border: 2px solid #4a7c59;
            border-radius: 4px;
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 600;
            transition: all 0.2s;
        }
        .back-btn:hover {
            background: #4a7c59;
            color: white;
        }
        
        .action-buttons {
            text-align: center;
            margin: 20px 0;
        }
        
        .print-btn {
            padding: 12px 30px;
            background: #28a745;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            margin: 0 10px;
        }
        
        .print-btn:hover {
            background: #218838;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        
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
        
        .athlete-name {
            font-weight: 500;
        }
        
        .vdot-value {
            margin-left: 8px;
            padding: 2px 8px;
            background: #e3f2fd;
            color: #1976d2;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .manual-entry {
            font-style: italic;
            color: #888;
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

        .no-print {
            display: block;
        }

        /* Print Styles */
        @media print {
            body {
                background: white;
                padding: 0;
                max-width: 100%;
            }
            
            .no-print {
                display: none !important;
            }
            
            .print-page {
                page-break-after: always;
                padding: 20px;
            }
            
            .print-page:last-child {
                page-break-after: auto;
            }
            
            .print-group-header {
                text-align: center;
                margin-bottom: 20px;
            }
            
            .print-group-title {
                font-size: 24pt;
                font-weight: bold;
                margin-bottom: 10px;
            }
            
            .print-workout-desc {
                font-size: 14pt;
                margin-bottom: 15px;
                color: #333;
            }
            
            .print-paces {
                margin-bottom: 20px;
                padding: 10px;
                border: 2px solid #003366;
            }
            
            .print-pace-item {
                display: inline-block;
                margin-right: 20px;
                font-size: 12pt;
            }
            
            .print-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            
            .print-table th,
            .print-table td {
                border: 1px solid #333;
                padding: 8px;
                text-align: left;
            }
            
            .print-table th {
                background-color: #f0f0f0;
                font-weight: bold;
            }
            
            .print-table .rep-col {
                width: 60px;
                text-align: center;
            }
            
            .print-table .name-col {
                width: 150px;
            }
        }
</style>"""
    
    def _get_javascript(self) -> str:
        """Return JavaScript for page functionality"""
        return r"""
// Parse workout description to get rep structure
// Handles both simple patterns (12x400@5k) and bracketed patterns (3x[600@3k + 400@mile + 200@800])
function parseWorkout(workoutDesc) {
    const allReps = [];
    
    // First, check for bracketed repetitions: 3x[600@3k + 400@mile + 200@800]
    const bracketPattern = /(\d+)x\[(.*?)\]/g;
    let bracketMatch;
    
    while ((bracketMatch = bracketPattern.exec(workoutDesc)) !== null) {
        const outerReps = parseInt(bracketMatch[1]);  // The "3" in "3x[...]"
        const bracketedContent = bracketMatch[2];      // Everything inside brackets
        
        // Find all distance@pace patterns inside the brackets
        const innerPattern = /(\d+)(?:m)?@(\w+)/g;
        const innerDistances = [];
        let innerMatch;
        
        while ((innerMatch = innerPattern.exec(bracketedContent)) !== null) {
            innerDistances.push({
                distance: innerMatch[1],
                pace: innerMatch[2].toUpperCase()
            });
        }
        
        // Expand the bracketed pattern: if it's 3x[600, 400, 200], create 9 columns
        for (let i = 0; i < outerReps; i++) {
            for (const item of innerDistances) {
                allReps.push({
                    count: 1,  // Each column is a single rep
                    distance: item.distance,
                    pace: item.pace
                });
            }
        }
    }
    
    // Then, look for non-bracketed patterns: 12x400@5k
    // Remove bracketed sections first to avoid double-counting
    const descWithoutBrackets = workoutDesc.replace(/\d+x\[.*?\]/g, '');
    const simplePattern = /(\d+)x(\d+)(?:m)?@(\w+)/g;
    let simpleMatch;
    
    while ((simpleMatch = simplePattern.exec(descWithoutBrackets)) !== null) {
        allReps.push({
            count: parseInt(simpleMatch[1]),
            distance: simpleMatch[2],
            pace: simpleMatch[3].toUpperCase()
        });
    }
    
    return allReps;
}

// Generate print view for all groups
function printGroupSheets() {
    const workoutDesc = document.getElementById('workoutDesc').textContent;
    const reps = parseWorkout(workoutDesc);
    const printContainer = document.getElementById('printContainer');
    
    // Clear previous content
    printContainer.innerHTML = '';
    
    // Generate a page for each group
    groupsData.forEach((group, index) => {
        if (group.name.includes('Unassigned')) return; // Skip unassigned
        
        const page = document.createElement('div');
        page.className = 'print-page';
        
        // Header
        const header = document.createElement('div');
        header.className = 'print-group-header';
        header.innerHTML = `
            <div class="print-group-title">${group.name}</div>
            <div class="print-workout-desc">${workoutDesc}</div>
            <div class="print-paces">
                ${Object.entries(group.paces).map(([label, pace]) => 
                    `<span class="print-pace-item"><strong>${label}:</strong> ${pace}</span>`
                ).join(' | ')}
            </div>
        `;
        page.appendChild(header);
        
        // Table
        const table = document.createElement('table');
        table.className = 'print-table';
        
        // Table header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        headerRow.innerHTML = '<th class="name-col">Athlete</th>';
        
        reps.forEach((rep, repIndex) => {
            if (rep.count > 1) {
                // Multiple reps: number them (e.g., "400m #1", "400m #2")
                for (let i = 1; i <= rep.count; i++) {
                    headerRow.innerHTML += `<th class="rep-col">${rep.distance}m<br/>#${i}</th>`;
                }
            } else {
                // Single rep (from bracketed patterns): just show distance
                headerRow.innerHTML += `<th class="rep-col">${rep.distance}m</th>`;
            }
        });
        
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Table body
        const tbody = document.createElement('tbody');
        group.athletes.forEach(athlete => {
            const row = document.createElement('tr');
            row.innerHTML = `<td class="name-col">${athlete.name}</td>`;
            
            // Add empty cells for each rep
            reps.forEach(rep => {
                for (let i = 0; i < rep.count; i++) {
                    row.innerHTML += '<td class="rep-col"></td>';
                }
            });
            
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        
        page.appendChild(table);
        printContainer.appendChild(page);
    });
    
    // Show print container and trigger print
    printContainer.style.display = 'block';
    window.print();
    printContainer.style.display = 'none';
}

// Load groups on page load (for screen view)
window.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('groupsContainer');
    
    groupsData.forEach(group => {
        const card = document.createElement('div');
        card.className = 'group-card';
        
        const header = document.createElement('div');
        header.className = 'group-header';
        header.textContent = group.name;
        card.appendChild(header);
        
        // Pace section
        const paceSection = document.createElement('div');
        paceSection.className = 'pace-section';
        paceSection.innerHTML = '<h3>Target Paces</h3><div class="pace-grid">';
        
        Object.entries(group.paces).forEach(([label, pace]) => {
            paceSection.innerHTML += `
                <div class="pace-item">
                    <div class="pace-label">${label}</div>
                    <div class="pace-value">${pace}</div>
                </div>
            `;
        });
        
        paceSection.innerHTML += '</div>';
        card.appendChild(paceSection);
        
        // Athletes list
        const ul = document.createElement('ul');
        ul.className = 'athlete-list';
        
        group.athletes.forEach(athlete => {
            const li = document.createElement('li');
            if (!athlete.vdot) li.className = 'manual-entry';
            li.innerHTML = `
                <span class="athlete-name">${athlete.name}</span>
                ${athlete.vdot ? `<span class="vdot-value">VDOT: ${athlete.vdot}</span>` : ''}
            `;
            ul.appendChild(li);
        });
        
        card.appendChild(ul);
        container.appendChild(card);
    });
});
"""


# Example usage function
def create_example_page():
    """Example of how to use the generator"""
    
    generator = WorkoutPacePageGenerator()
    
    # Example workout data
    workout_description = "2x200@mile+12x400@5k (200j) + 2x200@800"
    
    groups = [
        {
            "name": "Group 1",
            "paces": {
                "200m @ MILE": "31s-35s",
                "400m @ 5K": "1:09-1:17",
                "200m @ 800": "28s-31s"
            },
            "athletes": [
                {"name": "Marshall Wilson", "vdot": 65},
                {"name": "Matthew Frick", "vdot": 66},
                {"name": "Nick Sanders", "vdot": 72},
                {"name": "Sam Schweickhardt", "vdot": 66},
                {"name": "Tony Parilli", "vdot": 65},
                {"name": "Nolan Crider", "vdot": 64},
                {"name": "Anthony Passafiume", "vdot": None}
            ]
        },
        {
            "name": "Group 2",
            "paces": {
                "200m @ MILE": "35s",
                "400m @ 5K": "1:17-1:18",
                "200m @ 800": "31s"
            },
            "athletes": [
                {"name": "James George", "vdot": 64},
                {"name": "Ian O'Bryan", "vdot": 64},
                {"name": "James Bush", "vdot": 64}
            ]
        }
    ]
    
    html = generator.generate_page(
        workout_description=workout_description,
        groups=groups,
        squad_type="Varsity",
        week_number=39,
        day="Tuesday"
    )
    
    return html


if __name__ == "__main__":
    # Generate example page
    html = create_example_page()
    
    # Save to file
    with open("example_workout_paces.html", "w") as f:
        f.write(html)
    
    print("Generated example_workout_paces.html")
    print("\nTo use in your workflow:")
    print("1. Import the WorkoutPacePageGenerator class")
    print("2. Create an instance: generator = WorkoutPacePageGenerator()")
    print("3. Call generator.generate_page() with your workout data")
    print("4. Save the returned HTML to a file")
