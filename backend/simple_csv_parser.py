#!/usr/bin/env python3
"""
Simple CSV Parser - No Dependencies, Pure Python
Converts ALL CSV rows to JSON format for uniform processing
"""

import csv
import json
import io
from typing import List, Dict, Any

class SimpleCSVParser:
    """Simple CSV parser that converts all rows to JSON without external dependencies"""
    
    def parse_csv_to_json(self, csv_content: str) -> List[Dict[str, Any]]:
        """
        Parse CSV content and return list of JSON objects
        Each row becomes a JSON object with column headers as keys
        """
        try:
            # Clean the CSV content
            csv_content = csv_content.strip()
            if not csv_content:
                return []
            
            # Use StringIO to treat string as file
            csv_file = io.StringIO(csv_content)
            
            # Try different delimiters and find the best one
            delimiter = self._detect_delimiter(csv_content.split('\n')[:5])
            print(f" Detected delimiter: '{delimiter}'")
            
            # Reset file pointer
            csv_file.seek(0)
            
            # Parse CSV with detected delimiter
            csv_reader = csv.DictReader(csv_file, delimiter=delimiter)
            
            # Get fieldnames to debug
            fieldnames = csv_reader.fieldnames
            print(f" CSV columns detected: {fieldnames}")
            
            json_records = []
            for row_num, row in enumerate(csv_reader):
                try:
                    # Clean and convert each row to JSON object
                    clean_row = {}
                    for key, value in row.items():
                        # Clean column name - handle None keys from malformed CSV
                        if key is None:
                            continue  # Skip None keys
                            
                        clean_key = str(key).strip().replace(' ', '_').replace('-', '_')
                        clean_key = ''.join(c for c in clean_key if c.isalnum() or c == '_')
                        
                        if not clean_key:  # Skip empty keys
                            continue
                        
                        # Clean and convert value
                        if value is None or value == '':
                            clean_value = None
                        else:
                            clean_value = str(value).strip()
                            
                            # Try to convert to number if possible
                            if clean_value and clean_value.replace('.', '').replace('-', '').replace('+', '').isdigit():
                                try:
                                    clean_value = float(clean_value) if '.' in clean_value else int(clean_value)
                                except ValueError:
                                    pass  # Keep as string if conversion fails
                        
                        clean_row[clean_key] = clean_value
                    
                    # Only add row if it has actual data
                    if any(v is not None and v != '' for v in clean_row.values()):
                        # Add metadata
                        clean_row['_row_number'] = row_num + 1
                        clean_row['_source_format'] = 'csv'
                        json_records.append(clean_row)
                    
                except Exception as row_error:
                    print(f"  Error parsing row {row_num}: {row_error}")
                    continue
            
            print(f" Parsed {len(json_records)} CSV rows to JSON")
            return json_records
            
        except Exception as e:
            print(f" CSV parsing failed: {e}")
            return []
    
    def _detect_delimiter(self, sample_lines: List[str]) -> str:
        """Detect the most likely delimiter based on sample lines"""
        delimiters = [',', ';', '\t', '|']
        delimiter_scores = {}
        
        for delimiter in delimiters:
            score = 0
            consistent_columns = True
            column_counts = []
            
            for line in sample_lines:
                if line.strip():
                    # Count how many columns this delimiter would create
                    columns = len(line.split(delimiter))
                    column_counts.append(columns)
                    if columns > 1:
                        score += columns
            
            # Prefer delimiters that give consistent column counts
            if column_counts:
                most_common_count = max(set(column_counts), key=column_counts.count)
                consistency_ratio = column_counts.count(most_common_count) / len(column_counts)
                score = score * consistency_ratio
            
            delimiter_scores[delimiter] = score
        
        # Return delimiter with highest score
        best_delimiter = max(delimiter_scores.keys(), key=lambda k: delimiter_scores[k])
        return best_delimiter if delimiter_scores[best_delimiter] > 0 else ','

# Create global instance
simple_csv_parser = SimpleCSVParser() 