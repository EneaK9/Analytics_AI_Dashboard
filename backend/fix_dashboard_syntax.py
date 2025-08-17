"""
Quick script to fix syntax issues in dashboard_inventory_analyzer.py
"""

def fix_dashboard_syntax():
    file_path = "dashboard_inventory_analyzer.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Look for duplicate method definitions
    lines = content.split('\n')
    
    # Find all occurrences of _get_trend_visualizations
    trend_viz_lines = []
    for i, line in enumerate(lines):
        if "async def _get_trend_visualizations" in line:
            trend_viz_lines.append(i)
    
    print(f"Found _get_trend_visualizations method at lines: {trend_viz_lines}")
    
    # If there are duplicates, keep only the first one
    if len(trend_viz_lines) > 1:
        print("Removing duplicate method definition...")
        
        # Find the end of the duplicate method (looking for next method definition)
        start_duplicate = trend_viz_lines[1]
        
        # Find next method or end of class
        end_duplicate = len(lines)
        for i in range(start_duplicate + 1, len(lines)):
            if lines[i].strip().startswith("def ") or lines[i].strip().startswith("async def "):
                end_duplicate = i
                break
            elif lines[i].strip().startswith("class ") or (lines[i].strip() and not lines[i].startswith(" ") and not lines[i].startswith("\t")):
                end_duplicate = i
                break
        
        # Remove the duplicate method
        new_lines = lines[:start_duplicate] + lines[end_duplicate:]
        
        # Write back the corrected file
        with open(file_path, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print(f"Removed duplicate method from line {start_duplicate} to {end_duplicate}")
    
    print("✅ Syntax fix completed")

if __name__ == "__main__":
    fix_dashboard_syntax()
