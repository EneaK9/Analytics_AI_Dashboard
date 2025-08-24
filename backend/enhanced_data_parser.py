"""
Enhanced Data Parser with Multi-Format Support
Simplified version that works with existing database structure
"""

import pandas as pd
import json
import io
import chardet
import xml.etree.ElementTree as ET
import logging
from typing import Dict, Any, List, Union, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ParsedDataResult:
    """Result of data parsing with standardized format"""
    data: List[Dict[str, Any]]
    format_type: str
    columns: List[Dict[str, Any]]
    total_records: int
    data_quality_score: float
    data_types: Dict[str, str]
    sample_data: List[Dict[str, Any]]
    insights: List[str]

try:
    import pyarrow.parquet as pq
    import pyarrow as pa
    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False

try:
    import fastavro
    AVRO_AVAILABLE = True
except ImportError:
    AVRO_AVAILABLE = False

class EnhancedDataParser:
    """Enhanced data parser supporting multiple formats"""
    
    def __init__(self):
        self.supported_formats = {
            'json': ['.json'],
            'csv': ['.csv'],
            'tsv': ['.tsv', '.tab'],
            'excel': ['.xlsx', '.xls'],
            'xml': ['.xml'],
            'yaml': ['.yaml', '.yml'],
            'parquet': ['.parquet'],
            'avro': ['.avro']
        }
        
        # Security settings
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        self.allowed_mime_types = {
            'application/json',
            'text/csv',
            'text/tab-separated-values',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'application/xml',
            'text/xml',
            'application/x-yaml',
            'text/yaml',
            'application/octet-stream'  # For parquet/avro
        }

    def detect_file_type(self, file_content: bytes, filename: str = "") -> str:
        """Detect file type using multiple methods"""
        try:
            # Method 1: Use filetype library (Windows compatible)
            kind = filetype.guess(file_content)
            if kind:
                if kind.extension in ['json']:
                    return 'json'
                elif kind.extension in ['csv']:
                    return 'csv'
                elif kind.extension in ['xlsx', 'xls']:
                    return 'excel'
                elif kind.extension in ['xml']:
                    return 'xml'
            
            # Method 2: Check file extension
            if filename:
                file_ext = Path(filename).suffix.lower()
                for format_name, extensions in self.supported_formats.items():
                    if file_ext in extensions:
                        return format_name
            
            # Method 3: Content analysis for text-based formats
            try:
                text_content = file_content.decode('utf-8')
                
                # Try JSON
                try:
                    json.loads(text_content)
                    return 'json'
                except:
                    pass
                
                # Try YAML
                try:
                    yaml.safe_load(text_content)
                    if text_content.strip().startswith(('---', '%YAML')):
                        return 'yaml'
                except:
                    pass
                
                # Try XML
                try:
                    ET.fromstring(text_content)
                    return 'xml'
                except:
                    pass
                
                # Check for CSV patterns
                if ',' in text_content and '\n' in text_content:
                    return 'csv'
                
                # Check for TSV patterns
                if '\t' in text_content and '\n' in text_content:
                    return 'tsv'
                    
            except UnicodeDecodeError:
                pass
            
            return 'unknown'
            
        except Exception as e:
            print(f"Error detecting file type: {e}")
            return 'unknown'

    def detect_encoding(self, file_content: bytes) -> str:
        """Detect file encoding"""
        try:
            result = chardet.detect(file_content)
            return result.get('encoding', 'utf-8') or 'utf-8'
        except:
            return 'utf-8'

    def parse_data(self, file_content: bytes, filename: str, data_format: str = None) -> ParsedDataResult:
        """
        Parse data from various formats and ALWAYS return standardized JSON structure
         NEW: All formats converted to JSON for uniform processing
        """
        try:
            if data_format:
                format_type = data_format.lower()
            else:
                format_type = self._detect_format(file_content, filename)
            
            logger.info(f" Parsing {format_type.upper()} data from {filename}")
            
            # Parse based on format
            if format_type == 'json':
                data, columns_info = self._parse_json(file_content)
            elif format_type == 'csv':
                data, columns_info = self._parse_csv(file_content)
            elif format_type == 'xml':
                data, columns_info = self._parse_xml(file_content)
            elif format_type == 'excel':
                data, columns_info = self._parse_excel(file_content)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            
            #  CRITICAL: Convert ALL data to standardized JSON format
            standardized_data = self._standardize_to_json(data, columns_info, format_type)
            logger.info(f" Converted {format_type.upper()} to JSON: {len(standardized_data)} records")
            
            # Analyze the standardized JSON data 
            data_analysis = self._analyze_standardized_data(standardized_data, columns_info)
            
            return ParsedDataResult(
                data=standardized_data,  # ← Always JSON now!
                format_type=format_type,
                columns=columns_info,
                total_records=len(standardized_data),
                data_quality_score=data_analysis['quality_score'],
                data_types=data_analysis['data_types'],
                sample_data=standardized_data[:5],  # First 5 records as sample
                insights=data_analysis.get('insights', [])
            )
            
        except Exception as e:
            logger.error(f" Error parsing {filename}: {str(e)}")
            raise ValueError(f"Failed to parse data: {str(e)}")
    
    def _standardize_to_json(self, data: List[Dict], columns_info: List[Dict], source_format: str) -> List[Dict]:
        """
         NEW: Convert ALL formats to standardized JSON structure
        This ensures uniform processing regardless of source format
        """
        try:
            standardized_records = []
            
            logger.info(f" Standardizing {len(data)} records from {source_format.upper()} to JSON...")
            
            for i, record in enumerate(data):
                try:
                    # Ensure record is a dictionary
                    if not isinstance(record, dict):
                        logger.warning(f"  Record {i} is not a dict: {type(record)}, converting...")
                        if isinstance(record, (list, tuple)):
                            # Convert list/tuple to dict using column names
                            record_dict = {}
                            for j, value in enumerate(record):
                                col_name = columns_info[j]['name'] if j < len(columns_info) else f'column_{j}'
                                record_dict[col_name] = value
                            record = record_dict
                        else:
                            # Convert other types to string and create single-column record
                            record = {'value': str(record)}
                    
                    # Clean and validate each field
                    clean_record = {}
                    for key, value in record.items():
                        # Clean field names (remove special chars, spaces)
                        clean_key = str(key).strip().replace(' ', '_').replace('-', '_')
                        clean_key = ''.join(c for c in clean_key if c.isalnum() or c == '_')
                        
                        # Standardize values
                        if pd.isna(value) or value is None:
                            clean_value = None
                        elif isinstance(value, (int, float)):
                            clean_value = value
                        elif isinstance(value, str):
                            clean_value = value.strip()
                            # Try to convert numeric strings
                            if clean_value.replace('.', '').replace('-', '').isdigit():
                                try:
                                    clean_value = float(clean_value) if '.' in clean_value else int(clean_value)
                                except:
                                    pass  # Keep as string
                        elif isinstance(value, (list, dict)):
                            # Convert complex types to JSON string
                            clean_value = json.dumps(value)
                        else:
                            clean_value = str(value)
                        
                        clean_record[clean_key] = clean_value
                    
                    # Add metadata for traceability
                    clean_record['_source_format'] = source_format
                    clean_record['_record_index'] = i
                    
                    standardized_records.append(clean_record)
                    
                except Exception as record_error:
                    logger.warning(f"  Failed to standardize record {i}: {record_error}")
                    continue
            
            logger.info(f" Successfully standardized {len(standardized_records)}/{len(data)} records to JSON")
            return standardized_records
            
        except Exception as e:
            logger.error(f" Failed to standardize data to JSON: {e}")
            raise ValueError(f"Data standardization failed: {e}")
    
    def _analyze_standardized_data(self, standardized_data: List[Dict], columns_info: List[Dict]) -> Dict:
        """
         NEW: Analyze the standardized JSON data uniformly
        """
        try:
            if not standardized_data:
                return {
                    'quality_score': 0.0,
                    'data_types': {},
                    'insights': ['No data to analyze']
                }
            
            # Analyze data types and quality
            data_types = {}
            column_stats = {}
            
            # Analyze each column
            for col_info in columns_info:
                col_name = col_info['name']
                values = [record.get(col_name) for record in standardized_data if col_name in record]
                non_null_values = [v for v in values if v is not None]
                
                if not non_null_values:
                    data_types[col_name] = 'null'
                    column_stats[col_name] = {'completeness': 0.0, 'type': 'null'}
                    continue
                
                # Determine dominant type
                type_counts = {}
                for value in non_null_values:
                    value_type = type(value).__name__
                    type_counts[value_type] = type_counts.get(value_type, 0) + 1
                
                dominant_type = max(type_counts.keys(), key=lambda k: type_counts[k])
                data_types[col_name] = dominant_type
                
                completeness = len(non_null_values) / len(standardized_data)
                column_stats[col_name] = {
                    'completeness': completeness,
                    'type': dominant_type,
                    'unique_values': len(set(str(v) for v in non_null_values)),
                    'sample_values': list(set(str(v) for v in non_null_values[:10]))
                }
            
            # Calculate overall quality score
            avg_completeness = sum(stats['completeness'] for stats in column_stats.values()) / len(column_stats)
            type_consistency = len([t for t in data_types.values() if t in ['int', 'float', 'str']]) / len(data_types)
            
            quality_score = (avg_completeness * 0.6 + type_consistency * 0.4) * 100
            
            insights = [
                f"Standardized {len(standardized_data)} records to JSON format",
                f"Data completeness: {avg_completeness:.1%}",
                f"Type consistency: {type_consistency:.1%}",
                f"Quality score: {quality_score:.1f}/100"
            ]
            
            return {
                'quality_score': round(quality_score, 2),
                'data_types': data_types,
                'column_stats': column_stats,
                'insights': insights
            }
            
        except Exception as e:
            logger.error(f" Failed to analyze standardized data: {e}")
            return {
                'quality_score': 50.0,
                'data_types': {},
                'insights': [f'Analysis failed: {str(e)}']
            }

    def _parse_json(self, file_content: bytes) -> tuple[List[Dict], List[Dict]]:
        """Parse JSON data and return (data, columns_info) tuple"""
        try:
            encoding = self.detect_encoding(file_content)
            json_str = file_content.decode(encoding)
            
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f" JSON decode error: {e}")
                raise ValueError(f"Invalid JSON format: {e}")
            
            # Handle different JSON structures
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                if 'data' in data:
                    records = data['data'] if isinstance(data['data'], list) else [data['data']]
                elif 'records' in data:
                    records = data['records'] if isinstance(data['records'], list) else [data['records']]
                else:
                    records = [data]
            else:
                records = [{'value': data}]
            
            # Extract column information
            columns_info = []
            if records:
                sample_record = records[0]
                for key in sample_record.keys():
                    columns_info.append({
                        'name': key,
                        'type': type(sample_record[key]).__name__,
                        'nullable': any(record.get(key) is None for record in records[:100])
                    })
            
            logger.info(f" JSON parsed: {len(records)} records, {len(columns_info)} columns")
            return records, columns_info
            
        except Exception as e:
            logger.error(f" JSON parsing failed: {e}")
            raise ValueError(f"Failed to parse JSON: {e}")

    def _parse_csv(self, file_content: bytes) -> tuple[List[Dict], List[Dict]]:
        """Parse CSV data and return (data, columns_info) tuple"""
        try:
            encoding = self.detect_encoding(file_content)
            csv_str = file_content.decode(encoding)
            
            # Try different delimiters
            delimiters = [',', ';', '\t', '|']
            best_delimiter = ','
            max_columns = 0
            
            for delimiter in delimiters:
                try:
                    sample = csv_str.split('\n')[0]
                    columns = len(sample.split(delimiter))
                    if columns > max_columns:
                        max_columns = columns
                        best_delimiter = delimiter
                except:
                    continue
            
            # Read CSV with pandas
            from io import StringIO
            df = pd.read_csv(StringIO(csv_str), delimiter=best_delimiter, encoding=encoding)
            
            # Convert to records
            records = df.to_dict('records')
            
            # Extract column information
            columns_info = []
            for col_name, dtype in df.dtypes.items():
                columns_info.append({
                    'name': str(col_name),
                    'type': str(dtype),
                    'nullable': df[col_name].isnull().any()
                })
            
            logger.info(f" CSV parsed: {len(records)} records, {len(columns_info)} columns")
            return records, columns_info
            
        except Exception as e:
            logger.error(f" CSV parsing failed: {e}")
            raise ValueError(f"Failed to parse CSV: {e}")

    def _enhance_csv_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enhance CSV data type detection to match JSON quality"""
        for col in df.columns:
            # Skip if already numeric
            if pd.api.types.is_numeric_dtype(df[col]):
                continue
                
            # Try to convert to numeric
            try:
                # Handle common number formats
                cleaned = df[col].astype(str).str.replace(',', '').str.replace('$', '').str.replace('%', '')
                numeric_series = pd.to_numeric(cleaned, errors='coerce')
                
                # If more than 80% of values convert successfully, use numeric type
                if numeric_series.notna().sum() / len(df) > 0.8:
                    df[col] = numeric_series
                    continue
            except:
                pass
            
            # Try to convert to datetime
            try:
                datetime_series = pd.to_datetime(df[col], errors='coerce')
                
                # If more than 70% of values convert successfully, use datetime type
                if datetime_series.notna().sum() / len(df) > 0.7:
                    df[col] = datetime_series
                    continue
            except:
                pass
            
            # Try to convert to boolean
            try:
                bool_values = df[col].astype(str).str.lower()
                if bool_values.isin(['true', 'false', '1', '0', 'yes', 'no']).sum() / len(df) > 0.9:
                    df[col] = bool_values.map({
                        'true': True, 'false': False, '1': True, '0': False,
                        'yes': True, 'no': False
                    })
                    continue
            except:
                pass
        
        return df

    def _parse_tsv(self, file_content: bytes, encoding: str) -> Dict[str, Any]:
        """Parse TSV data"""
        try:
            text = file_content.decode(encoding)
            df = pd.read_csv(io.StringIO(text), sep='\t')
            
            return {
                'success': True,
                'data': df,
                'format': 'tsv',
                'rows': len(df),
                'columns': len(df.columns),
                'quality_score': self._calculate_quality_score(df)
            }
        except Exception as e:
            raise ValueError(f"TSV parsing error: {e}")

    def _parse_excel(self, file_content: bytes) -> tuple[List[Dict], List[Dict]]:
        """Parse Excel data and return (data, columns_info) tuple"""
        try:
            from io import BytesIO
            df = pd.read_excel(BytesIO(file_content), engine='openpyxl')
            
            # Convert to records
            records = df.to_dict('records')
            
            # Extract column information
            columns_info = []
            for col_name, dtype in df.dtypes.items():
                columns_info.append({
                    'name': str(col_name),
                    'type': str(dtype),
                    'nullable': df[col_name].isnull().any()
                })
            
            logger.info(f" Excel parsed: {len(records)} records, {len(columns_info)} columns")
            return records, columns_info
            
        except Exception as e:
            logger.error(f" Excel parsing failed: {e}")
            raise ValueError(f"Failed to parse Excel: {e}")

    def _detect_format(self, file_content: bytes, filename: str) -> str:
        """Detect file format from content and filename"""
        filename_lower = filename.lower()
        
        # Check by extension first
        if filename_lower.endswith('.json'):
            return 'json'
        elif filename_lower.endswith('.csv'):
            return 'csv'
        elif filename_lower.endswith('.xml'):
            return 'xml'
        elif filename_lower.endswith(('.xlsx', '.xls')):
            return 'excel'
        
        # Try to detect by content
        try:
            content_str = file_content.decode('utf-8')[:1000]  # First 1000 chars
            
            if content_str.strip().startswith('{') or content_str.strip().startswith('['):
                return 'json'
            elif content_str.strip().startswith('<'):
                return 'xml'
            elif ',' in content_str and '\n' in content_str:
                return 'csv'
        except:
            pass
        
        # Default fallback
        return 'csv'

    def _parse_yaml(self, file_content: bytes, encoding: str) -> Dict[str, Any]:
        """Parse YAML data"""
        try:
            text = file_content.decode(encoding)
            data = yaml.safe_load(text)
            
            # Convert to DataFrame
            if isinstance(data, list) and data and isinstance(data[0], dict):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                df = pd.DataFrame({'value': [data]})
            
            return {
                'success': True,
                'data': df,
                'format': 'yaml',
                'rows': len(df),
                'columns': len(df.columns),
                'quality_score': self._calculate_quality_score(df)
            }
        except Exception as e:
            raise ValueError(f"YAML parsing error: {e}")

    def _parse_parquet(self, file_content: bytes) -> Dict[str, Any]:
        """Parse Parquet data"""
        try:
            if not PARQUET_AVAILABLE:
                raise ValueError("Parquet support not available. Install pyarrow.")
            
            df = pd.read_parquet(io.BytesIO(file_content))
            
            return {
                'success': True,
                'data': df,
                'format': 'parquet',
                'rows': len(df),
                'columns': len(df.columns),
                'quality_score': self._calculate_quality_score(df)
            }
        except Exception as e:
            raise ValueError(f"Parquet parsing error: {e}")

    def _parse_avro(self, file_content: bytes) -> Dict[str, Any]:
        """Parse Avro data"""
        try:
            if not AVRO_AVAILABLE:
                raise ValueError("Avro support not available. Install fastavro.")
            
            data = []
            with io.BytesIO(file_content) as fo:
                avro_reader = fastavro.reader(fo)
                for record in avro_reader:
                    data.append(record)
            
            df = pd.DataFrame(data) if data else pd.DataFrame()
            
            return {
                'success': True,
                'data': df,
                'format': 'avro',
                'rows': len(df),
                'columns': len(df.columns),
                'quality_score': self._calculate_quality_score(df)
            }
        except Exception as e:
            raise ValueError(f"Avro parsing error: {e}")

    def _calculate_quality_score(self, df: pd.DataFrame) -> float:
        """Calculate enhanced data quality score"""
        try:
            if df.empty:
                return 0.0
            
            # Calculate completeness (non-null values)
            completeness = (df.count().sum()) / (df.shape[0] * df.shape[1])
            
            # Calculate data type consistency (prefer numeric and datetime types)
            numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
            datetime_cols = len(df.select_dtypes(include=['datetime', 'datetimetz']).columns)
            total_cols = len(df.columns)
            
            type_quality = (numeric_cols + datetime_cols) / total_cols if total_cols > 0 else 0
            
            # Calculate uniqueness (avoid too many duplicates)
            uniqueness_scores = []
            for col in df.columns:
                unique_ratio = df[col].nunique() / len(df)
                # Good uniqueness is between 0.1 and 0.9 (not all same, not all different)
                if 0.1 <= unique_ratio <= 0.9:
                    uniqueness_scores.append(1.0)
                elif unique_ratio < 0.1:
                    uniqueness_scores.append(0.5)  # Too repetitive
                else:
                    uniqueness_scores.append(0.8)  # Very unique (still good)
            
            uniqueness = sum(uniqueness_scores) / len(uniqueness_scores) if uniqueness_scores else 0.5
            
            # Calculate structural quality (good column names, reasonable data size)
            structure_quality = 1.0
            
            # Penalize very short column names or numbers-only names
            for col in df.columns:
                if len(str(col)) < 2 or str(col).isdigit():
                    structure_quality -= 0.1
            
            structure_quality = max(0.3, structure_quality)
            
            # Overall weighted quality score
            quality_score = (
                completeness * 0.4 +      # 40% weight on completeness
                type_quality * 0.3 +      # 30% weight on data types
                uniqueness * 0.2 +        # 20% weight on uniqueness
                structure_quality * 0.1   # 10% weight on structure
            )
            
            return round(min(1.0, quality_score), 2)
        except:
            return 0.5  # Default score

    def get_supported_formats(self) -> List[str]:
        """Get list of supported formats"""
        formats = list(self.supported_formats.keys())
        if not PARQUET_AVAILABLE:
            formats = [f for f in formats if f != 'parquet']
        if not AVRO_AVAILABLE:
            formats = [f for f in formats if f != 'avro']
        return formats

# Global instance
enhanced_parser = EnhancedDataParser() 