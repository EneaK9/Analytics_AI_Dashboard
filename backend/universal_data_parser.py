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
    
    def parse_to_json(self, content, format_type: str) -> List[Dict[str, Any]]:
        """
        Parse any format and return list of JSON objects
        Supported formats: JSON, CSV, XML, TSV, YAML, TXT, EXCEL, BAK
        Accepts both str and bytes content for better .bak file handling
        """
        try:
            format_type = format_type.lower()
            
            # 🔧 ENHANCED: Handle bytes content (from SFTP/file uploads) 
            if isinstance(content, bytes):
                if format_type == 'bak':
                    # Use app.py strategy: try multiple encodings for .bak files
                    print("🔄 Received bytes content, trying multiple encodings for .bak file...")
                    for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
                        try:
                            content = content.decode(encoding)
                            print(f"✅ Successfully decoded .bak file using {encoding} encoding")
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        print("❌ Could not decode .bak file with any encoding")
                        return []
                else:
                    # For other formats, try UTF-8 first, then latin-1
                    try:
                        content = content.decode('utf-8')
                    except UnicodeDecodeError:
                        content = content.decode('latin-1', errors='ignore')
            
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
            elif format_type == 'excel':
                return self._parse_excel(content)
            elif format_type == 'bak':
                return self._parse_bak(content)
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
            
            # 🚀 ROBUST CSV parsing with multiple fallback strategies
            records = []
            lines = content.split('\n')
            
            # Strategy 1: Try standard CSV parsing
            try:
                csv_file = io.StringIO(content)
                csv_reader = csv.DictReader(csv_file, delimiter=delimiter, 
                                          quoting=csv.QUOTE_ALL, skipinitialspace=True)
                
                for row_num, row in enumerate(csv_reader):
                    if not row or all(v is None or v == '' for v in row.values()):
                        continue
                        
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
                        
            except csv.Error as csv_error:
                print(f"⚠️ Standard CSV parsing failed: {csv_error}")
                print("🔄 Trying manual line-by-line parsing...")
                
                # Strategy 2: Manual line-by-line parsing for problematic files
                if len(lines) > 1:
                    # 🔧 SMART HEADER DETECTION - Try multiple approaches
                    header_line = lines[0].strip()
                    
                    # Try all possible delimiters to find the right one
                    best_delimiter = delimiter
                    max_fields = 0
                    
                    for test_delim in [',', ';', '\t', '|', ' ']:
                        test_headers = header_line.split(test_delim)
                        if len(test_headers) > max_fields:
                            max_fields = len(test_headers)
                            best_delimiter = test_delim
                    
                    print(f"🔍 Testing delimiters: detected '{delimiter}' but '{best_delimiter}' gives {max_fields} fields")
                    
                    # Use the best delimiter
                    delimiter = best_delimiter
                    headers = [h.strip().strip('"').strip("'") for h in header_line.split(delimiter)]
                    headers = [h for h in headers if h]  # Remove empty headers
                    
                    # If still too few headers, this might not be CSV - try alternate approach
                    if len(headers) < 2:
                        print("⚠️ Very few headers detected, trying pattern-based extraction...")
                        # Look for GUID patterns and use positional headers
                        if 'AB467008' in header_line or len(header_line) > 100:
                            headers = ['guid_1', 'guid_2', 'data_field', 'additional_data']
                            delimiter = None  # Use position-based parsing
                            print(f"🔧 Using positional parsing with {len(headers)} generic headers")
                    
                    print(f"📋 Found {len(headers)} headers: {headers[:5]}..." if len(headers) > 5 else f"📋 Found headers: {headers}")
                    
                    # Process data lines
                    for line_num, line in enumerate(lines[1:], 1):
                        line = line.strip()
                        if not line or len(line) < 5:  # Skip very short lines
                            continue
                        
                        # 🔧 SMART PARSING: Handle both delimiter-based and position-based
                        if delimiter is None:
                            # Position-based parsing for complex formats
                            values = []
                            
                            # Multiple GUID patterns for different formats  
                            import re as regex_module  # Use explicit import to avoid conflicts
                            guid_patterns = [
                                r'[A-F0-9]{8}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{4}-[A-F0-9]{12}',  # Standard GUID
                                r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}',  # Lowercase GUID
                                r'[A-Fa-f0-9]{32}',  # GUID without dashes
                            ]
                            
                            all_guids = []
                            remaining_line = line
                            
                            for pattern in guid_patterns:
                                guids = regex_module.findall(pattern, remaining_line)
                                all_guids.extend(guids)
                                # Remove found GUIDs from line for further processing
                                remaining_line = regex_module.sub(pattern, '|GUID|', remaining_line)
                            
                            if all_guids:
                                values.extend(all_guids[:3])  # Take up to 3 GUIDs
                                # Extract remaining meaningful data
                                parts = [p.strip() for p in remaining_line.split('|') 
                                        if p.strip() and p.strip() != 'GUID' and len(p.strip()) > 2]
                                
                                # Add the most meaningful parts (longer strings likely to be data)
                                meaningful_parts = sorted(parts, key=len, reverse=True)[:2]
                                values.extend(meaningful_parts)
                            else:
                                # Fallback: split by common patterns and take meaningful chunks
                                parts = [p.strip() for p in regex_module.split(r'[;,\t\x00-\x1f]', line) if p.strip()]
                                # Filter out very short or binary-looking parts
                                meaningful_parts = [p for p in parts if len(p) >= 3 and not all(ord(c) > 127 for c in p[:5])]
                                values = meaningful_parts[:4]
                            
                        else:
                            # Delimiter-based parsing with quote handling
                            values = []
                            current_value = ""
                            in_quotes = False
                            quote_char = None
                            
                            i = 0
                            while i < len(line):
                                char = line[i]
                                
                                if char in ['"', "'"] and not in_quotes:
                                    in_quotes = True
                                    quote_char = char
                                elif char == quote_char and in_quotes:
                                    in_quotes = False
                                    quote_char = None
                                elif char == delimiter and not in_quotes:
                                    values.append(current_value.strip())
                                    current_value = ""
                                    i += 1
                                    continue
                                else:
                                    current_value += char
                                i += 1
                            
                            # Add the last value
                            values.append(current_value.strip())
                        
                        # Create record if we have enough values
                        if len(values) >= len(headers):
                            clean_row = {}
                            for j, header in enumerate(headers):
                                if j < len(values):
                                    value = values[j].strip().strip('"').strip("'")
                                    # KEEP ALL VALUES - NO FILTERING
                                    clean_row[header] = value
                            
                            if clean_row:  # Only add if we have actual data
                                clean_row['_row_number'] = line_num
                                clean_row['_source_format'] = 'csv_manual'
                                records.append(clean_row)
                                
                                # No artificial limit - let the 1/8 sampling handle size control
                
                print(f"✅ Manual parsing extracted {len(records)} records")
                
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
    
    def _parse_excel(self, content: str) -> List[Dict[str, Any]]:
        """Parse Excel content (requires pandas and openpyxl for full support)"""
        try:
            # Try to use pandas if available for Excel parsing
            try:
                import pandas as pd
                from io import BytesIO
                
                # If content is a string, it might be base64 encoded or file path
                # For now, we'll assume it's binary data converted to string
                if isinstance(content, str):
                    # Try to decode if it's base64 encoded
                    try:
                        import base64
                        binary_content = base64.b64decode(content)
                    except:
                        # If not base64, treat as text and try CSV parsing
                        print("⚠️ Excel content appears to be text, falling back to CSV parsing")
                        return self._parse_csv(content)
                else:
                    binary_content = content
                
                # Parse Excel file
                df = pd.read_excel(BytesIO(binary_content), engine='openpyxl')
                
                # Convert to records
                records = []
                for i, row in df.iterrows():
                    record = {}
                    for col, value in row.items():
                        # Clean column name
                        clean_col = str(col).strip().replace(' ', '_').replace('-', '_')
                        clean_col = ''.join(c for c in clean_col if c.isalnum() or c == '_')
                        
                        # Handle NaN values
                        if pd.isna(value):
                            record[clean_col] = None
                        else:
                            record[clean_col] = value
                    
                    record['_row_number'] = i + 1
                    record['_source_format'] = 'excel'
                    records.append(record)
                
                print(f"✅ Parsed {len(records)} Excel records")
                return records
                
            except ImportError:
                print("⚠️ pandas/openpyxl not available, falling back to CSV parsing for Excel files")
                return self._parse_csv(content)
                
        except Exception as e:
            print(f"❌ Excel parsing failed: {e}")
            # Fallback to CSV parsing
            return self._parse_csv(content)
    
    def _parse_bak(self, content: str) -> List[Dict[str, Any]]:
        """Parse .bak files (SQL Server backup files) with proper database structure extraction"""
        try:
            print("🔍 Parsing SQL Server .bak file with database structure extraction...")
            print(f"📏 Original content length: {len(content)} characters")
            
            # Check if content is empty
            if not content or len(content.strip()) < 50:
                print("❌ .bak file content is empty or too small to parse")
                return []
            
            # STEP 1: Try to extract SQL data structures from the backup
            sql_records = self._extract_sql_from_bak(content)
            if sql_records:
                return sql_records
            
            # STEP 2: If SQL extraction fails, try to find database schema information
            schema_records = self._extract_database_schema(content)
            if schema_records:
                return schema_records
            
            # STEP 3: Last resort - extract meaningful text patterns but parse them better
            return self._extract_structured_data_from_bak(content)
            
        except Exception as e:
            print(f"❌ .bak file parsing failed: {e}")
            return self._create_bak_error_record(content, e)
    
    def _extract_sql_from_bak(self, content: str) -> List[Dict[str, Any]]:
        """Extract SQL data from BAK file content"""
        try:
            import re
            
            # Look for SQL-like patterns in the content
            sql_patterns = [
                r'CREATE TABLE\s+(\w+)\s*\(([^)]+)\)',  # Table definitions
                r'INSERT INTO\s+(\w+)\s+VALUES\s*\(([^)]+)\)',  # Insert statements
                r'(\w+)\s*=\s*[\'"]([^\'"]*)[\'"]',  # Key-value pairs
            ]
            
            records = []
            
            for pattern in sql_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                for match in matches[:50]:  # Limit to 50 matches per pattern
                    if len(match) >= 2:
                        record = {
                            'table_name': self._sanitize_text(match[0]),
                            'content': self._sanitize_text(match[1]),
                            'record_type': 'sql_structure',
                            '_source_format': 'bak_sql_extraction'
                        }
                        records.append(record)
            
            if records:
                print(f"✅ Extracted {len(records)} SQL structure records from BAK")
                return records[:100]  # Limit total records
            
            return []
            
        except Exception as e:
            print(f"❌ SQL extraction failed: {e}")
            return []
    
    def _extract_database_schema(self, content: str) -> List[Dict[str, Any]]:
        """Extract database schema information from BAK file"""
        try:
            import re
            
            # Look for table names and column definitions
            table_pattern = r'(\w+)\s*\(\s*(\w+(?:\s+\w+)*(?:\s*,\s*\w+(?:\s+\w+)*)*)\s*\)'
            column_pattern = r'(\w+)\s+(VARCHAR|INT|DECIMAL|DATE|DATETIME|TEXT|CHAR|FLOAT|DOUBLE|BOOLEAN)\s*(?:\(\d+\))?'
            
            records = []
            schema_info = {}
            
            # Extract table schemas
            table_matches = re.findall(table_pattern, content, re.IGNORECASE)
            for table_name, columns_text in table_matches[:20]:  # Limit to 20 tables
                column_matches = re.findall(column_pattern, columns_text, re.IGNORECASE)
                
                if column_matches:
                    table_record = {
                        'table_name': self._sanitize_text(table_name),
                        'record_type': 'table_schema',
                        'column_count': len(column_matches),
                        'columns': [{'name': col[0], 'type': col[1]} for col in column_matches],
                        '_source_format': 'bak_schema_extraction'
                    }
                    records.append(table_record)
                    schema_info[table_name] = column_matches
            
            # Look for data patterns based on schema
            for table_name, columns in schema_info.items():
                data_pattern = r'\b' + re.escape(table_name) + r'\b.*?(\d+(?:\s*,\s*[^\s,]+)*)'
                data_matches = re.findall(data_pattern, content, re.IGNORECASE)
                
                for i, data_match in enumerate(data_matches[:10]):  # Limit to 10 data records per table
                    values = [v.strip().strip("'\"") for v in data_match.split(',')]
                    
                    data_record = {
                        'table_name': table_name,
                        'record_type': 'data_row',
                        'record_id': i + 1,
                        '_source_format': 'bak_data_extraction'
                    }
                    
                    # Map values to column names
                    for j, (col_name, col_type) in enumerate(columns):
                        if j < len(values):
                            data_record[self._sanitize_text(col_name)] = self._convert_value_by_type(values[j], col_type)
                    
                    records.append(data_record)
            
            if records:
                print(f"✅ Extracted {len(records)} database schema records from BAK")
                return records
            
            return []
            
        except Exception as e:
            print(f"❌ Database schema extraction failed: {e}")
            return []
    
    def _extract_structured_data_from_bak(self, content: str) -> List[Dict[str, Any]]:
        """Last resort: extract structured data patterns from BAK content"""
        try:
            import re
            
            # Look for structured data patterns
            patterns = [
                r'(\w+):\s*([^\n\r]+)',  # Key-value pairs
                r'(\w+)\s*=\s*([^\n\r]+)',  # Assignment patterns
                r'(\d{4}-\d{2}-\d{2})',  # Dates
                r'(\d+\.\d+)',  # Decimal numbers
                r'(\d+)',  # Integers
            ]
            
            records = []
            extracted_data = {}
            
            for pattern_name, pattern in [
                ('key_value', patterns[0]),
                ('assignment', patterns[1]),
                ('dates', patterns[2]),
                ('decimals', patterns[3]),
                ('integers', patterns[4])
            ]:
                matches = re.findall(pattern, content, re.MULTILINE)
                if matches:
                    extracted_data[pattern_name] = matches[:20]  # Limit matches
            
            # Create records from extracted patterns
            record_id = 1
            
            for pattern_type, matches in extracted_data.items():
                for match in matches:
                    if isinstance(match, tuple) and len(match) >= 2:
                        record = {
                            'id': record_id,
                            'pattern_type': pattern_type,
                            'key': self._sanitize_text(str(match[0])),
                            'value': self._sanitize_text(str(match[1])),
                            'record_type': 'structured_data',
                            '_source_format': 'bak_pattern_extraction'
                        }
                        records.append(record)
                        record_id += 1
                    elif isinstance(match, str):
                        record = {
                            'id': record_id,
                            'pattern_type': pattern_type,
                            'value': self._sanitize_text(match),
                            'record_type': 'structured_data',
                            '_source_format': 'bak_pattern_extraction'
                        }
                        records.append(record)
                        record_id += 1
            
            if records:
                print(f"✅ Extracted {len(records)} structured data records from BAK")
                return records[:100]  # Limit to 100 records
            
            # If no structured patterns found, extract clean text lines
            return self._extract_clean_text_from_bak(content)
            
        except Exception as e:
            print(f"❌ Structured data extraction failed: {e}")
            return self._extract_clean_text_from_bak(content)
    
    def _extract_clean_text_from_bak(self, content: str) -> List[Dict[str, Any]]:
        """Extract clean readable text from BAK content"""
        try:
            lines = content.split('\n')
            records = []
            
            for line_num, line in enumerate(lines):
                # Extract only readable ASCII text
                clean_chars = []
                for char in line:
                    if 32 <= ord(char) <= 126 or char in [' ', '\t']:
                        clean_chars.append(char)
                
                clean_line = ''.join(clean_chars).strip()
                
                # Only keep lines with meaningful content
                if len(clean_line) >= 10 and any(c.isalpha() for c in clean_line):
                    record = {
                        'id': len(records) + 1,
                        'line_number': line_num + 1,
                        'text_content': clean_line[:200],  # Limit length
                        'content_length': len(clean_line),
                        'record_type': 'text_line',
                        '_source_format': 'bak_text_extraction'
                    }
                    records.append(record)
                    
                    if len(records) >= 100:  # Limit total records
                        break
            
            print(f"✅ Extracted {len(records)} clean text records from BAK")
            return records
            
        except Exception as e:
            print(f"❌ Clean text extraction failed: {e}")
            return []
    
    def _create_bak_error_record(self, content: str, error: Exception) -> List[Dict[str, Any]]:
        """Create error record when BAK parsing fails"""
        error_type = "unicode_error" if "unicode" in str(error).lower() else "parsing_error"
        
        return [{
            'id': 1,
            'filename': 'backup_file.bak',
            'error': str(error)[:200],
            'error_type': error_type,
            'content_length': len(content) if content else 0,
            'content_preview': content[:100] if content else 'empty',
            'record_type': 'parse_error',
            '_backup_file': True,
            '_original_format': 'bak',
            '_parse_failed': True,
            'recovery_message': 'BAK file parsing failed - try converting to CSV or SQL format'
        }]
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text content for safe processing"""
        if not isinstance(text, str):
            text = str(text)
        
        # Remove non-printable characters
        sanitized = ''.join(char for char in text if ord(char) >= 32 or char in ['\n', '\t'])
        
        # Limit length and strip
        return sanitized[:500].strip()
    
    def _convert_value_by_type(self, value: str, data_type: str) -> Any:
        """Convert string value to appropriate type based on SQL data type"""
        try:
            value = value.strip().strip("'\"")
            data_type = data_type.upper()
            
            if data_type in ['INT', 'INTEGER']:
                return int(value)
            elif data_type in ['FLOAT', 'DOUBLE', 'DECIMAL']:
                return float(value)
            elif data_type == 'BOOLEAN':
                return value.lower() in ['true', '1', 'yes', 'on']
            else:
                return value
        except:
            return value
    
    def _extract_sql_inserts(self, content: str) -> List[Dict[str, Any]]:
        """Extract data from SQL INSERT statements"""
        records = []
        try:
            import re
            
            # Look for INSERT INTO statements
            insert_pattern = r'INSERT\s+INTO\s+`?(\w+)`?\s*\([^)]+\)\s*VALUES\s*\(([^)]+)\)'
            matches = re.findall(insert_pattern, content, re.IGNORECASE | re.MULTILINE)
            
            for table_name, values in matches:
                # Parse the values and sanitize them
                value_list = [self._sanitize_text(v.strip().strip("'\"")) for v in values.split(',')]
                
                record = {
                    'table_name': self._sanitize_text(table_name),
                    'record_type': 'sql_insert',
                    'values': value_list,
                    'value_count': len(value_list)
                }
                
                # Try to create meaningful field names
                for i, value in enumerate(value_list):
                    record[f'field_{i+1}'] = value
                
                records.append(record)
                
        except Exception as e:
            print(f"⚠️ SQL extraction failed: {e}")
        
        return records
    
    def _extract_delimited_data(self, content: str) -> List[Dict[str, Any]]:
        """Extract MEANINGFUL delimited data patterns from content (not random binary garbage)"""
        records = []
        try:
            lines = content.split('\n')
            meaningful_lines = []
            
            # 🧠 SMART FILTERING: Only extract lines that look like actual business data
            for line_num, line in enumerate(lines):
                line = line.strip()
                if not line or len(line) < 10:  # Skip very short lines
                    continue
                
                # 🚫 SKIP GARBAGE: Filter out lines that are clearly binary/encoded junk
                if self._is_garbage_line(line):
                    continue
                
                # 🎯 LOOK FOR BUSINESS DATA: Only process lines that seem meaningful
                for delimiter in [',', '\t', '|', ';']:
                    if delimiter in line and len(line.split(delimiter)) >= 3:
                        values = line.split(delimiter)
                        
                        # 🧠 SMART VALIDATION: Only keep if it looks like real business data
                        if self._looks_like_business_data(values):
                            clean_values = [self._sanitize_text(v.strip()) for v in values]
                            
                            record = {
                                'line_number': line_num + 1,
                                'record_type': 'business_data',  # Changed from 'delimited_data'
                                'delimiter': delimiter,
                                'field_count': len(clean_values),
                                'raw_line': self._sanitize_text(line[:100])
                            }
                            
                            # Add individual fields with better names
                            for i, value in enumerate(clean_values):
                                record[f'field_{i+1}'] = value
                            
                            records.append(record)
                            meaningful_lines.append(line_num + 1)
                            break  # Found valid delimiter, move to next line
                
        except Exception as e:
            print(f"⚠️ Delimited data extraction failed: {e}")
        
        if meaningful_lines:
            print(f"📊 Found meaningful business data on lines: {meaningful_lines[:10]}{'...' if len(meaningful_lines) > 10 else ''}")
        
        return records  # No limit - process all records
    
    def _extract_json_from_text(self, content: str) -> List[Dict[str, Any]]:
        """Extract high-quality JSON objects from within text content with enhanced business data detection"""
        records = []
        try:
            import re
            import json
            
            print("🔍 Enhanced JSON extraction with business data prioritization...")
            
            # Look for JSON object patterns with better business data detection
            json_pattern = r'\{[^{}]*\}'
            matches = re.findall(json_pattern, content)
            
            # Business-relevant field names to prioritize
            business_keywords = [
                'id', 'name', 'email', 'phone', 'address', 'city', 'state', 'country', 'zip',
                'price', 'cost', 'amount', 'total', 'value', 'revenue', 'profit',
                'order', 'product', 'customer', 'client', 'user', 'account',
                'date', 'time', 'created', 'updated', 'modified',
                'status', 'type', 'category', 'description', 'notes',
                'quantity', 'stock', 'inventory', 'supplier', 'vendor'
            ]
            
            business_json_count = 0
            for match in matches:
                try:
                    json_obj = json.loads(match)
                    if isinstance(json_obj, dict) and len(json_obj) > 0:
                        # 🎯 Prioritize JSON objects with business-relevant fields
                        field_names = [str(key).lower() for key in json_obj.keys()]
                        business_relevance = sum(1 for keyword in business_keywords 
                                               if any(keyword in field for field in field_names))
                        
                        # Only include if it has business relevance OR is a substantial object
                        if business_relevance > 0 or len(json_obj) >= 3:
                            json_obj['record_type'] = 'embedded_json'
                            json_obj['_business_relevance_score'] = business_relevance
                            records.append(json_obj)
                            if business_relevance > 0:
                                business_json_count += 1
                except:
                    continue
            
            if business_json_count > 0:
                print(f"💼 Found {business_json_count} business-relevant JSON objects out of {len(records)} total")
                    
        except Exception as e:
            print(f"⚠️ JSON extraction failed: {e}")
        
        return records  # No limit - process all JSON objects
    
    def _extract_key_value_pairs(self, content: str) -> List[Dict[str, Any]]:
        """Extract MEANINGFUL key-value pairs from content (not binary garbage)"""
        records = []
        try:
            import re
            
            lines = content.split('\n')
            current_record = {}
            meaningful_pairs = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    if current_record and meaningful_pairs > 0:
                        current_record['record_type'] = 'configuration_data'  # More specific name
                        # Sanitize all values in the record
                        for k, v in current_record.items():
                            if isinstance(v, str):
                                current_record[k] = self._sanitize_text(v)
                        records.append(current_record)
                        current_record = {}
                        meaningful_pairs = 0
                    continue
                
                # 🚫 SKIP GARBAGE: Don't process obviously binary lines
                if self._is_garbage_line(line):
                    continue
                
                # Look for key-value patterns
                for pattern in [r'(\w+):\s*(.+)', r'(\w+)=(.+)', r'(\w+)\s+(.+)']:
                    match = re.match(pattern, line)
                    if match:
                        key, value = match.groups()
                        key = key.strip()
                        value = value.strip()
                        
                        # 🧠 ONLY KEEP MEANINGFUL KEY-VALUE PAIRS
                        if (len(key) > 1 and len(value) > 0 and 
                            not self._is_garbage_line(key + value) and
                            len(key) < 50 and len(value) < 500):  # Reasonable lengths
                            
                            current_record[key] = self._sanitize_text(value)
                            meaningful_pairs += 1
                            break
            
            # Add final record if exists and has meaningful data
            if current_record and meaningful_pairs > 0:
                current_record['record_type'] = 'configuration_data'
                # Sanitize all values in the final record
                for k, v in current_record.items():
                    if isinstance(v, str):
                        current_record[k] = self._sanitize_text(v)
                records.append(current_record)
                
        except Exception as e:
            print(f"⚠️ Key-value extraction failed: {e}")
        
        if records:
            print(f"📊 Found {len(records)} meaningful configuration/key-value records")
        
        return records  # No limit - process all records
    
    def _create_binary_summary_records(self, content: str) -> List[Dict[str, Any]]:
        """Create summary records for binary content with useful analytics"""
        try:
            # Analyze the binary content and create multiple meaningful records
            records = []
            
            # Overall file summary
            records.append({
                'record_type': 'file_summary',
                'total_size': len(content),
                'file_type': 'binary_backup',
                'encoding_detected': 'binary',
                '_backup_file': True,
                '_original_format': 'bak'
            })
            
            # Character frequency analysis (useful for some analytics)
            char_counts = {}
            for char in content[:1000]:  # Sample first 1000 chars
                char_counts[ord(char)] = char_counts.get(ord(char), 0) + 1
            
            # Create records for most common characters
            sorted_chars = sorted(char_counts.items(), key=lambda x: x[1], reverse=True)
            for i, (char_code, count) in enumerate(sorted_chars[:10]):
                records.append({
                    'record_type': 'character_frequency',
                    'character_code': char_code,
                    'character': chr(char_code) if 32 <= char_code <= 126 else f'\\x{char_code:02x}',
                    'frequency': count,
                    'rank': i + 1,
                    '_backup_file': True,
                    '_original_format': 'bak'
                })
            
            return records
            
        except Exception as e:
            print(f"⚠️ Binary summary creation failed: {e}")
            return [{
                'record_type': 'binary_file',
                'content_length': len(content),
                'error': str(e),
                '_backup_file': True,
                '_original_format': 'bak'
            }]
    
    def _extract_text_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Extract patterns from text content to create analyzable records"""
        records = []
        try:
            lines = content.split('\n')
            
            # Create records for different types of content found
            for line_num, line in enumerate(lines):  # Process all lines
                line = line.strip()
                if not line:
                    continue
                
                record = {
                    'line_number': line_num + 1,
                    'line_length': len(line),
                    'word_count': len(line.split()),
                    'content_preview': self._sanitize_text(line[:50]),
                    'line_type': self._classify_line_type(line),
                    'record_type': 'text_line',
                    '_backup_file': True,
                    '_original_format': 'bak'
                }
                
                records.append(record)
            
            return records
            
        except Exception as e:
            print(f"⚠️ Text pattern extraction failed: {e}")
            return [{
                'record_type': 'text_content',
                'content_length': len(content),
                'line_count': len(content.split('\n')),
                '_backup_file': True,
                '_original_format': 'bak'
            }]
    
    def _classify_line_type(self, line: str) -> str:
        """Classify the type of content in a line"""
        if line.startswith(('INSERT', 'UPDATE', 'DELETE', 'SELECT')):
            return 'sql_statement'
        elif ',' in line and len(line.split(',')) >= 3:
            return 'delimited_data'
        elif ':' in line or '=' in line:
            return 'key_value'
        elif line.startswith(('<', '?xml')):
            return 'xml_content'
        elif line.startswith(('{', '[')):
            return 'json_content'
        elif line.isdigit():
            return 'numeric'
        else:
            return 'text'
    
    def _is_garbage_line(self, line: str) -> bool:
        """Detect if a line contains binary garbage instead of meaningful data"""
        if not line or len(line) < 3:
            return True
        
        # Count non-printable characters
        non_printable = sum(1 for c in line if ord(c) < 32 and c not in '\t\n\r')
        
        # If more than 20% of characters are non-printable, it's likely garbage
        if non_printable / len(line) > 0.2:
            return True
        
        # Check for too many special characters (indicates binary data)
        special_chars = sum(1 for c in line if ord(c) > 127)
        if special_chars / len(line) > 0.3:
            return True
        
        # Check for patterns that indicate binary/encoded data
        garbage_patterns = [
            b'\x00', b'\xff', b'\xfe', b'\xef\xbb\xbf',  # Common binary markers
            r'\x', r'\u', '\x00',  # Escape sequences (using raw strings)
        ]
        
        for pattern in garbage_patterns:
            if isinstance(pattern, bytes):
                try:
                    pattern = pattern.decode('utf-8', errors='ignore')
                except:
                    continue
            if pattern in line:
                return True
        
        return False
    
    def _looks_like_business_data(self, values: list) -> bool:
        """Check if delimited values look like actual business data"""
        if not values or len(values) < 2:
            return False
        
        meaningful_count = 0
        
        for value in values:
            value = str(value).strip()
            if not value:
                continue
                
            # Check for common business data patterns
            if any([
                # Numbers (IDs, prices, quantities)
                value.replace('.', '').replace('-', '').isdigit(),
                # Dates
                re.match(r'\d{1,4}[-/]\d{1,2}[-/]\d{1,4}', value),
                # Email-like
                '@' in value and '.' in value,
                # Common business words
                any(keyword in value.lower() for keyword in [
                    'name', 'id', 'email', 'phone', 'address', 'order', 'product',
                    'customer', 'price', 'date', 'total', 'qty', 'quantity',
                    'description', 'category', 'status', 'invoice', 'payment'
                ]),
                # Reasonable text (alphanumeric with spaces/common punctuation)
                re.match(r'^[a-zA-Z0-9\s\-_.@#$%&()]+$', value) and len(value) > 2
            ]):
                meaningful_count += 1
        
        # At least 50% of values should look meaningful
        return meaningful_count >= len(values) * 0.5
    
    def _sanitize_text(self, text: str) -> str:
        """Remove null bytes and other problematic characters that cause database issues"""
        if not isinstance(text, str):
            return str(text)
        
        # Remove null bytes (the main culprit)
        text = text.replace('\x00', '')
        
        # Remove other problematic control characters but keep common ones
        import re
        # Keep \t (tab), \n (newline), \r (carriage return) but remove others
        text = re.sub(r'[\x01-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        
        # Ensure text is valid UTF-8
        try:
            text = text.encode('utf-8', errors='ignore').decode('utf-8')
        except:
            text = str(text)
        
        # Limit length to prevent huge strings
        if len(text) > 1000:
            text = text[:997] + '...'
        
        return text
    
    def _extract_sql_server_headers(self, content: str) -> List[str]:
        """Extract column headers from SQL Server backup files"""
        headers = []
        try:
            import re
            
            # Look for CREATE TABLE statements
            create_table_pattern = r'CREATE\s+TABLE\s+\[?(\w+)\]?\s*\(\s*([^)]+)\)'
            matches = re.findall(create_table_pattern, content, re.IGNORECASE | re.MULTILINE)
            
            for table_name, columns_def in matches:
                print(f"🏗️ Found table: {table_name}")
                # Extract column names from definition
                column_pattern = r'\[?(\w+)\]?\s+\w+'
                columns = re.findall(column_pattern, columns_def)
                headers.extend(columns)
                print(f"📊 Table {table_name} columns: {columns}")
            
            # Also look for INSERT INTO statements to get column lists
            insert_pattern = r'INSERT\s+INTO\s+\[?(\w+)\]?\s*\(\s*([^)]+)\)'
            insert_matches = re.findall(insert_pattern, content, re.IGNORECASE)
            
            for table_name, columns_list in insert_matches:
                columns = [col.strip().strip('[]') for col in columns_list.split(',')]
                headers.extend(columns)
                print(f"📝 INSERT columns for {table_name}: {columns}")
                
        except Exception as e:
            print(f"⚠️ SQL Server header extraction failed: {e}")
        
        return list(set(headers))  # Remove duplicates
    
    def _extract_backup_headers(self, content: str) -> List[str]:
        """Extract headers from general SQL backup files"""
        headers = []
        try:
            import re
            
            # Look for common SQL patterns
            patterns = [
                r'CREATE\s+TABLE\s+(\w+)\s*\(\s*([^)]+)\)',
                r'INSERT\s+INTO\s+(\w+)\s*\(\s*([^)]+)\)',
                r'ALTER\s+TABLE\s+(\w+)\s+ADD\s+(\w+)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if len(match) == 2:
                        table_name, definition = match
                        # Extract column names
                        if ',' in definition:
                            columns = [col.strip().strip('[]') for col in definition.split(',')]
                            headers.extend(columns)
                        else:
                            headers.append(definition.strip())
                            
        except Exception as e:
            print(f"⚠️ Backup header extraction failed: {e}")
        
        return list(set(headers))
    
    def _extract_sql_dump_headers(self, content: str) -> List[str]:
        """Extract headers from SQL dump files"""
        headers = []
        try:
            import re
            
            # Look for INSERT INTO statements with column lists
            insert_pattern = r'INSERT\s+INTO\s+`?(\w+)`?\s*\(\s*([^)]+)\)\s*VALUES'
            matches = re.findall(insert_pattern, content, re.IGNORECASE)
            
            for table_name, columns_list in matches:
                columns = [col.strip().strip('`[]') for col in columns_list.split(',')]
                headers.extend(columns)
                print(f"📝 SQL dump table {table_name} columns: {columns}")
            
            # Look for CREATE TABLE statements
            create_pattern = r'CREATE\s+TABLE\s+`?(\w+)`?\s*\(\s*([^;]+)\);?'
            create_matches = re.findall(create_pattern, content, re.IGNORECASE | re.DOTALL)
            
            for table_name, table_def in create_matches:
                # Extract column definitions
                column_pattern = r'`?(\w+)`?\s+\w+'
                columns = re.findall(column_pattern, table_def)
                headers.extend(columns)
                print(f"🏗️ SQL dump CREATE TABLE {table_name} columns: {columns}")
                
        except Exception as e:
            print(f"⚠️ SQL dump header extraction failed: {e}")
        
        return list(set(headers))
    
    def _extract_generic_headers(self, content: str) -> List[str]:
        """Extract headers from generic database backup files using heuristics"""
        headers = []
        try:
            import re
            
            # Look for patterns that might be column names
            lines = content.split('\n')[:100]  # Check first 100 lines
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for comma-separated identifiers (potential column lists)
                if ',' in line and len(line.split(',')) >= 3:
                    # Check if this looks like a column list
                    parts = [p.strip().strip('[]`"\'') for p in line.split(',')]
                    if all(re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', part) for part in parts[:5]):
                        headers.extend(parts)
                        print(f"📋 Found potential column list: {parts[:10]}")
                
                # Look for key-value patterns that might indicate field names
                kv_pattern = r'(\w+)\s*[:=]\s*'
                matches = re.findall(kv_pattern, line)
                if matches:
                    headers.extend(matches)
            
            # Common business field names to look for
            business_fields = ['id', 'name', 'email', 'phone', 'address', 'date', 'amount', 'price', 'quantity', 'status']
            found_business_fields = []
            content_lower = content.lower()
            
            for field in business_fields:
                if field in content_lower:
                    found_business_fields.append(field)
            
            if found_business_fields:
                headers.extend(found_business_fields)
                print(f"💼 Found business field indicators: {found_business_fields}")
                
        except Exception as e:
            print(f"⚠️ Generic header extraction failed: {e}")
        
        return list(set(headers))[:20]  # Limit to 20 headers

# Create global instance
universal_parser = UniversalDataParser() 