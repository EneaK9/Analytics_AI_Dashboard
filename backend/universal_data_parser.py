#!/usr/bin/env python3
"""
Universal Data Parser - No Dependencies, Pure Python  
Converts ALL data formats to JSON for uniform processing
"""

import csv
import json
import io
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
import re

class UniversalDataParser:
    """Universal parser that converts ALL data formats to JSON without external dependencies"""
    
    def parse_to_json(self, content: str, format_type: str) -> List[Dict[str, Any]]:
        """
        Parse any format and return list of JSON objects
        Supported formats: JSON, CSV, XML, TSV, YAML, TXT
        """
        try:
            format_type = format_type.lower()
            
            if format_type == 'json':
                return self._parse_json(content)
            elif format_type == 'csv':
                return self._parse_csv(content)
            elif format_type == 'xml':
                return self._parse_xml(content)
            elif format_type == 'tsv':
                return self._parse_tsv(content)
            elif format_type in ['yaml', 'yml']:
                return self._parse_yaml(content)
            elif format_type == 'txt':
                return self._parse_txt(content)
            else:
                # Try to auto-detect format
                return self._auto_detect_and_parse(content)
                
        except Exception as e:
            print(f"❌ Universal parsing failed for {format_type}: {e}")
            return []
    
    def _parse_json(self, content: str) -> List[Dict[str, Any]]:
        """Parse JSON content"""
        try:
            data = json.loads(content.strip())
            
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                if 'data' in data and isinstance(data['data'], list):
                    records = data['data']
                elif 'records' in data and isinstance(data['records'], list):
                    records = data['records']
                else:
                    records = [data]
            else:
                records = [{'value': data}]
            
            # Add metadata
            for i, record in enumerate(records):
                if isinstance(record, dict):
                    record['_row_number'] = i + 1
                    record['_source_format'] = 'json'
            
            print(f"✅ Parsed {len(records)} JSON records")
            return records
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            return []
    
    def _parse_csv(self, content: str) -> List[Dict[str, Any]]:
        """Parse CSV content with improved logic"""
        try:
            content = content.strip()
            if not content:
                return []
            
            # Auto-detect delimiter
            delimiter = self._detect_csv_delimiter(content)
            print(f"🔍 CSV delimiter detected: '{delimiter}'")
            
            csv_file = io.StringIO(content)
            csv_reader = csv.DictReader(csv_file, delimiter=delimiter)
            
            records = []
            for row_num, row in enumerate(csv_reader):
                clean_row = {}
                for key, value in row.items():
                    if key is None:
                        continue
                    
                    # Clean column name
                    clean_key = str(key).strip().replace(' ', '_').replace('-', '_')
                    clean_key = ''.join(c for c in clean_key if c.isalnum() or c == '_')
                    
                    if not clean_key:
                        continue
                    
                    # Clean and convert value
                    if value is None or value == '':
                        clean_value = None
                    else:
                        clean_value = str(value).strip()
                        # Try numeric conversion
                        if clean_value and re.match(r'^[+-]?\d*\.?\d+$', clean_value):
                            try:
                                clean_value = float(clean_value) if '.' in clean_value else int(clean_value)
                            except ValueError:
                                pass
                    
                    clean_row[clean_key] = clean_value
                
                if any(v is not None and v != '' for v in clean_row.values()):
                    clean_row['_row_number'] = row_num + 1
                    clean_row['_source_format'] = 'csv'
                    records.append(clean_row)
            
            print(f"✅ Parsed {len(records)} CSV records")
            return records
            
        except Exception as e:
            print(f"❌ CSV parsing failed: {e}")
            return []
    
    def _parse_xml(self, content: str) -> List[Dict[str, Any]]:
        """Parse XML content"""
        try:
            content = content.strip()
            if not content:
                return []
            
            root = ET.fromstring(content)
            records = []
            
            # Strategy 1: Look for repeating child elements
            children = list(root)
            if len(children) > 1:
                # Multiple child elements - treat each as a record
                for i, child in enumerate(children):
                    record = {'_element_name': child.tag}
                    
                    # Add attributes
                    if child.attrib:
                        record.update(child.attrib)
                    
                    # Add text content
                    if child.text and child.text.strip():
                        record['_text_content'] = child.text.strip()
                    
                    # Add sub-elements
                    for sub_elem in child:
                        key = sub_elem.tag.replace('-', '_').replace(' ', '_')
                        value = sub_elem.text.strip() if sub_elem.text else ''
                        
                        # Try numeric conversion
                        if value and re.match(r'^[+-]?\d*\.?\d+$', value):
                            try:
                                value = float(value) if '.' in value else int(value)
                            except ValueError:
                                pass
                        
                        record[key] = value
                    
                    record['_row_number'] = i + 1
                    record['_source_format'] = 'xml'
                    records.append(record)
            else:
                # Single element or flat structure
                record = {'_element_name': root.tag}
                
                if root.attrib:
                    record.update(root.attrib)
                
                if root.text and root.text.strip():
                    record['_text_content'] = root.text.strip()
                
                for elem in root:
                    key = elem.tag.replace('-', '_').replace(' ', '_')
                    value = elem.text.strip() if elem.text else ''
                    
                    if value and re.match(r'^[+-]?\d*\.?\d+$', value):
                        try:
                            value = float(value) if '.' in value else int(value)
                        except ValueError:
                            pass
                    
                    record[key] = value
                
                record['_row_number'] = 1
                record['_source_format'] = 'xml'
                records.append(record)
            
            print(f"✅ Parsed {len(records)} XML records")
            return records
            
        except ET.ParseError as e:
            print(f"❌ XML parsing failed: {e}")
            return []
    
    def _parse_tsv(self, content: str) -> List[Dict[str, Any]]:
        """Parse TSV (Tab-Separated Values) content"""
        try:
            # TSV is just CSV with tab delimiter
            content = content.strip()
            if not content:
                return []
            
            csv_file = io.StringIO(content)
            csv_reader = csv.DictReader(csv_file, delimiter='\t')
            
            records = []
            for row_num, row in enumerate(csv_reader):
                clean_row = {}
                for key, value in row.items():
                    if key is None:
                        continue
                    
                    clean_key = str(key).strip().replace(' ', '_').replace('-', '_')
                    clean_key = ''.join(c for c in clean_key if c.isalnum() or c == '_')
                    
                    if not clean_key:
                        continue
                    
                    if value is None or value == '':
                        clean_value = None
                    else:
                        clean_value = str(value).strip()
                        if clean_value and re.match(r'^[+-]?\d*\.?\d+$', clean_value):
                            try:
                                clean_value = float(clean_value) if '.' in clean_value else int(clean_value)
                            except ValueError:
                                pass
                    
                    clean_row[clean_key] = clean_value
                
                if any(v is not None and v != '' for v in clean_row.values()):
                    clean_row['_row_number'] = row_num + 1
                    clean_row['_source_format'] = 'tsv'
                    records.append(clean_row)
            
            print(f"✅ Parsed {len(records)} TSV records")
            return records
            
        except Exception as e:
            print(f"❌ TSV parsing failed: {e}")
            return []
    
    def _parse_yaml(self, content: str) -> List[Dict[str, Any]]:
        """Parse YAML content (simple implementation without PyYAML)"""
        try:
            content = content.strip()
            if not content:
                return []
            
            # Simple YAML parser for basic key-value structures
            records = []
            lines = content.split('\n')
            current_record = {}
            record_count = 0
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if line.startswith('---') or line.startswith('- '):
                    # New record
                    if current_record:
                        current_record['_row_number'] = record_count + 1
                        current_record['_source_format'] = 'yaml'
                        records.append(current_record)
                        record_count += 1
                    current_record = {}
                    continue
                
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().replace(' ', '_').replace('-', '_')
                    value = value.strip().strip('"').strip("'")
                    
                    # Try numeric conversion
                    if value and re.match(r'^[+-]?\d*\.?\d+$', value):
                        try:
                            value = float(value) if '.' in value else int(value)
                        except ValueError:
                            pass
                    elif value.lower() in ['true', 'false']:
                        value = value.lower() == 'true'
                    elif value.lower() == 'null':
                        value = None
                    
                    current_record[key] = value
            
            # Add the last record
            if current_record:
                current_record['_row_number'] = record_count + 1
                current_record['_source_format'] = 'yaml'
                records.append(current_record)
            
            print(f"✅ Parsed {len(records)} YAML records")
            return records
            
        except Exception as e:
            print(f"❌ YAML parsing failed: {e}")
            return []
    
    def _parse_txt(self, content: str) -> List[Dict[str, Any]]:
        """Parse plain text content (line-based)"""
        try:
            content = content.strip()
            if not content:
                return []
            
            lines = content.split('\n')
            records = []
            
            for i, line in enumerate(lines):
                line = line.strip()
                if line:  # Skip empty lines
                    record = {
                        'line_content': line,
                        'line_length': len(line),
                        'word_count': len(line.split()),
                        '_row_number': i + 1,
                        '_source_format': 'txt'
                    }
                    records.append(record)
            
            print(f"✅ Parsed {len(records)} TXT records (lines)")
            return records
            
        except Exception as e:
            print(f"❌ TXT parsing failed: {e}")
            return []
    
    def _auto_detect_and_parse(self, content: str) -> List[Dict[str, Any]]:
        """Auto-detect format and parse"""
        content = content.strip()
        
        # Try JSON first
        if content.startswith(('{', '[')):
            return self._parse_json(content)
        
        # Try XML
        if content.startswith('<'):
            return self._parse_xml(content)
        
        # Check for CSV/TSV patterns
        if '\t' in content and ',' not in content.split('\n')[0]:
            return self._parse_tsv(content)
        elif ',' in content and '\n' in content:
            return self._parse_csv(content)
        
        # Check for YAML patterns
        if ':' in content and any(line.strip().startswith('-') for line in content.split('\n')):
            return self._parse_yaml(content)
        
        # Default to text
        return self._parse_txt(content)
    
    def _detect_csv_delimiter(self, content: str) -> str:
        """Detect CSV delimiter"""
        delimiters = [',', ';', '\t', '|']
        delimiter_scores = {}
        sample_lines = content.split('\n')[:5]
        
        for delimiter in delimiters:
            score = 0
            column_counts = []
            
            for line in sample_lines:
                if line.strip():
                    columns = len(line.split(delimiter))
                    column_counts.append(columns)
                    if columns > 1:
                        score += columns
            
            # Prefer consistent column counts
            if column_counts:
                most_common = max(set(column_counts), key=column_counts.count)
                consistency = column_counts.count(most_common) / len(column_counts)
                score = score * consistency
            
            delimiter_scores[delimiter] = score
        
        best_delimiter = max(delimiter_scores.keys(), key=lambda k: delimiter_scores[k])
        return best_delimiter if delimiter_scores[best_delimiter] > 0 else ','

# Create global instance
universal_parser = UniversalDataParser() 