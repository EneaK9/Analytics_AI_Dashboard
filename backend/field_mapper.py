#!/usr/bin/env python3
"""
Field Mapper Utility - Intelligent field name processing
Preserves original names while creating clean technical names for database/API use
"""

import re
from typing import Dict, Tuple, List
from dataclasses import dataclass

@dataclass
class FieldNameMapping:
    """Container for field name mappings"""
    original: str
    technical: str
    display: str

class SmartFieldMapper:
    """Intelligent field name mapper that creates clear, consistent field names"""
    
    def __init__(self):
        # Common business term mappings for better display names
        self.business_term_mappings = {
            'amt': 'Amount',
            'qty': 'Quantity', 
            'rev': 'Revenue',
            'cust': 'Customer',
            'prod': 'Product',
            'cat': 'Category',
            'desc': 'Description',
            'addr': 'Address',
            'num': 'Number',
            'pct': 'Percentage',
            'avg': 'Average',
            'min': 'Minimum',
            'max': 'Maximum',
            'std': 'Standard',
            'dev': 'Deviation'
        }
        
        # Currency and numeric indicators
        self.currency_indicators = ['$', '€', '£', '¥', 'usd', 'eur', 'gbp', 'amount', 'price', 'cost', 'revenue', 'sales']
        self.percentage_indicators = ['%', 'pct', 'percent', 'rate', 'ratio']
        self.date_indicators = ['date', 'time', 'created', 'updated', 'timestamp']
    
    def create_field_mapping(self, original_name: str) -> FieldNameMapping:
        """Create comprehensive field mapping from original name"""
        
        # Step 1: Create technical name (database-safe)
        technical_name = self._create_technical_name(original_name)
        
        # Step 2: Create display name (user-friendly)
        display_name = self._create_display_name(original_name, technical_name)
        
        return FieldNameMapping(
            original=original_name,
            technical=technical_name,
            display=display_name
        )
    
    def _create_technical_name(self, original: str) -> str:
        """Create clean, database-safe technical name"""
        if not original or not original.strip():
            return "unknown_field"
            
        # Start with the original name
        name = str(original).strip()
        
        # Remove special characters and brackets content
        name = re.sub(r'\([^)]*\)', '', name)  # Remove (content)
        name = re.sub(r'\[[^\]]*\]', '', name)  # Remove [content]
        name = re.sub(r'\{[^}]*\}', '', name)  # Remove {content}
        
        # Replace spaces and hyphens with underscores
        name = re.sub(r'[\s\-]+', '_', name)
        
        # Remove special characters but keep underscores and alphanumeric
        name = re.sub(r'[^\w]', '_', name)
        
        # Clean up multiple underscores
        name = re.sub(r'_+', '_', name)
        
        # Remove leading/trailing underscores
        name = name.strip('_')
        
        # Convert to lowercase
        name = name.lower()
        
        # Ensure it starts with a letter or underscore
        if name and not (name[0].isalpha() or name[0] == '_'):
            name = 'field_' + name
            
        # Handle empty result
        if not name:
            name = 'unknown_field'
            
        return name
    
    def _create_display_name(self, original: str, technical: str) -> str:
        """Create user-friendly display name"""
        
        # If original has mixed case and special chars, it's likely already formatted
        if self._is_well_formatted(original):
            return original.strip()
        
        # Start with technical name and make it readable
        display = technical.replace('_', ' ')
        
        # Title case each word
        words = display.split()
        formatted_words = []
        
        for word in words:
            # Check if it's a known business term
            if word.lower() in self.business_term_mappings:
                formatted_words.append(self.business_term_mappings[word.lower()])
            else:
                # Title case
                formatted_words.append(word.title())
        
        display = ' '.join(formatted_words)
        
        # Handle common abbreviations
        display = self._expand_abbreviations(display)
        
        return display
    
    def _is_well_formatted(self, text: str) -> bool:
        """Check if text is already well-formatted for display"""
        if not text:
            return False
            
        # Has mixed case and spaces/reasonable punctuation
        has_mixed_case = any(c.islower() for c in text) and any(c.isupper() for c in text)
        has_reasonable_structure = ' ' in text or len(text.split()) > 1
        
        return has_mixed_case and has_reasonable_structure
    
    def _expand_abbreviations(self, text: str) -> str:
        """Expand common abbreviations in display names"""
        
        abbreviation_map = {
            'Id': 'ID',
            'Url': 'URL',
            'Api': 'API',
            'Ui': 'UI',
            'Db': 'Database',
            'Qty': 'Quantity',
            'Amt': 'Amount',
            'Avg': 'Average',
            'Min': 'Minimum', 
            'Max': 'Maximum',
            'Std': 'Standard',
            'Dev': 'Deviation'
        }
        
        words = text.split()
        for i, word in enumerate(words):
            if word in abbreviation_map:
                words[i] = abbreviation_map[word]
                
        return ' '.join(words)
    
    def detect_field_format(self, field_name: str, sample_values: List[any] = None) -> str:
        """Detect the likely format/type of a field based on name and sample values"""
        
        field_lower = field_name.lower()
        
        # Check field name for indicators
        if any(indicator in field_lower for indicator in self.currency_indicators):
            return 'currency'
        elif any(indicator in field_lower for indicator in self.percentage_indicators):
            return 'percentage'
        elif any(indicator in field_lower for indicator in self.date_indicators):
            return 'date'
        
        # Check sample values if provided
        if sample_values:
            sample_values = [v for v in sample_values if v is not None][:5]  # Check first 5 non-null values
            
            for value in sample_values:
                str_value = str(value).strip()
                
                # Currency check
                if re.match(r'^\$?\d+\.?\d*$', str_value) or '$' in str_value:
                    return 'currency'
                    
                # Percentage check
                if '%' in str_value or (isinstance(value, (int, float)) and 0 <= value <= 100):
                    return 'percentage'
                    
                # Date check (basic)
                if re.match(r'\d{4}-\d{2}-\d{2}', str_value) or re.match(r'\d{2}/\d{2}/\d{4}', str_value):
                    return 'date'
        
        # Default to number for numeric fields, text otherwise
        if 'count' in field_lower or 'number' in field_lower or 'total' in field_lower:
            return 'number'
            
        return 'text'
    
    def create_field_mappings_from_data(self, data: List[Dict]) -> Dict[str, Dict[str, str]]:
        """Create field mappings from a dataset"""
        if not data:
            return {"original_fields": {}, "display_names": {}}
            
        # Get all field names from first record
        sample_record = data[0]
        original_fields = {}
        display_names = {}
        
        for original_field in sample_record.keys():
            if original_field.startswith('_'):  # Skip metadata fields
                continue
                
            mapping = self.create_field_mapping(original_field)
            original_fields[mapping.original] = mapping.technical
            display_names[mapping.technical] = mapping.display
            
        return {
            "original_fields": original_fields,
            "display_names": display_names
        }

# Global instance for easy import
field_mapper = SmartFieldMapper() 