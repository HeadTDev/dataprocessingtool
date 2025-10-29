"""Number formatting utilities for Hungarian and international formats."""

from typing import Optional, Tuple


def parse_hungarian_number(value: str) -> float:
    """
    Parse a Hungarian-formatted number string to float.
    
    Hungarian format: 1.234.567,89 (period for thousands, comma for decimal)
    
    Args:
        value: Number string in Hungarian format
        
    Returns:
        Parsed float value
        
    Raises:
        ValueError: If the string cannot be parsed
    """
    if not value or not value.strip():
        return 0.0
    
    # Remove spaces and handle special characters
    clean = value.strip().replace(' ', '').replace('\xa0', '').replace('\u202f', '')
    
    # Convert Hungarian format to standard: remove thousand separators, replace decimal comma
    clean = clean.replace('.', '').replace(',', '.')
    
    try:
        return float(clean)
    except ValueError:
        raise ValueError(f"Cannot parse number: '{value}'")


def format_hungarian_number(value: float, decimals: int = 2) -> str:
    """
    Format a float as Hungarian-formatted number string.
    
    Args:
        value: Number to format
        decimals: Number of decimal places
        
    Returns:
        Formatted string (e.g., "1.234.567,89")
    """
    # Format with comma as decimal separator and period as thousands
    formatted = f"{value:,.{decimals}f}"
    # Swap comma and period
    result = formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
    return result


def to_clean_float(cell: str) -> Optional[float]:
    """
    Convert a cell value to float, handling various number formats.
    
    Tries to intelligently parse numbers in both Hungarian and international formats.
    
    Args:
        cell: Cell value as string
        
    Returns:
        Parsed float or None if cannot parse
    """
    if not cell or str(cell).strip() == "":
        return None
    
    s = str(cell).strip().replace(" ", "").replace('\xa0', '').replace('\u202f', '')
    
    # If no separators, try direct conversion
    if ',' not in s and '.' not in s:
        try:
            return float(s)
        except ValueError:
            return None
    
    # Try Hungarian format first (more periods than commas suggests thousand separator)
    if s.count('.') > s.count(','):
        try:
            return parse_hungarian_number(s)
        except ValueError:
            pass
    
    # Try international format (period as decimal)
    try:
        clean = s.replace(',', '')  # Remove thousand separators
        return float(clean)
    except ValueError:
        pass
    
    # Last resort: try Hungarian format
    try:
        return parse_hungarian_number(s)
    except ValueError:
        return None


def format_amount(amount_str: str) -> Tuple[Optional[float], str]:
    """
    Format an amount string to both numeric and formatted string.
    
    Args:
        amount_str: Amount as string in any format
        
    Returns:
        Tuple of (numeric_value, formatted_string)
    """
    if not amount_str:
        return None, ""
    
    try:
        num = to_clean_float(amount_str)
        if num is not None:
            # Return as international format: 1,234,567.89
            str_formatted = f"{num:,.2f}"
            return num, str_formatted
        else:
            return None, amount_str
    except Exception:
        return None, amount_str
