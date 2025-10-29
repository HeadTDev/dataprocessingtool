# Common Utilities Module

Shared utilities used across all data processing modules.

## Modules

### config.py
Centralized configuration management:
- `Config.DEFAULT_MULTIPLIER` - Default multiplier for merkantil processor (1.27)
- `Config.UPDATE_CHECK_TIMEOUT` - Auto-updater timeout (30 seconds)
- `Config.BUTTON_WIDTH/HEIGHT` - UI button dimensions
- `Config.FUZZY_MATCH_THRESHOLD` - Fuzzy matching threshold (0.80)

### logging_setup.py
Logging configuration:
- `setup_logging(log_dir, log_level, module_name)` - Configure logging for modules

### validators.py
Input validation utilities:
- `FileValidator.validate_exists(path)` - Check file exists
- `FileValidator.validate_excel(path, required_columns)` - Validate Excel file structure
- `FileValidator.validate_pdf(path)` - Validate PDF file
- `FileValidator.validate_directory(path, create_if_missing)` - Validate directory

### file_utils.py
File operation utilities:
- `ensure_output_dir(base_path, subdir)` - Ensure output directory exists
- `safe_remove_dir(directory, ignore_errors)` - Safely remove directory
- `safe_remove_file(file_path, ignore_errors)` - Safely remove file

### number_formats.py
Number formatting for Hungarian and international formats:
- `parse_hungarian_number(value)` - Parse Hungarian format (1.234.567,89)
- `format_hungarian_number(value, decimals)` - Format to Hungarian
- `to_clean_float(cell)` - Smart parse any number format
- `format_amount(amount_str)` - Parse and format amount

## Usage Example

```python
from common import Config, setup_logging, FileValidator, parse_hungarian_number

# Setup logging
logger = setup_logging(module_name="my_module")

# Validate input
FileValidator.validate_excel("input.xlsx", required_columns=["Name", "Amount"])

# Parse Hungarian number
amount = parse_hungarian_number("1.234.567,89")  # Returns 1234567.89

# Use configuration
multiplier = Config.DEFAULT_MULTIPLIER
```
