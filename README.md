# Palm Beach County Property Appraiser Data Extractor

A comprehensive Python toolkit for automating property searches and data extraction from the Palm Beach County Property Appraiser (PAPA) website.

## Features

### 🔍 Property Search Automation (`pbc_property_search.py`)
- Automated form filling for property searches
- Configurable search parameters (municipality, square footage, property type)
- Handles complex form interactions and dropdowns
- Anti-bot protection compatibility

### 🏠 Intelligent Data Extractor (`property_results_extractor.py`)
- **Smart Structure Detection**: Automatically detects tables, containers, or text-based results
- **Multiple Format Support**: Handles various result page layouts gracefully
- **Comprehensive Data Extraction**:
  - Property Address
  - Owner Name  
  - Property Value/Assessment
  - Square Footage
  - Property Type
  - Parcel ID/Account Number
  - Sale Information (price, date)
  - Year Built, Lot Size, Bedrooms, Bathrooms
  - Municipality, Zoning, Tax Information
  - And more...
- **Pagination Handling**: Automatically processes multiple result pages
- **Export Options**: CSV and JSON formats with timestamps
- **Error Handling**: Robust error handling and logging
- **Browser Session Management**: Connects to existing browser or opens new one
- **User-Friendly Interface**: Clear instructions and progress feedback

## Installation

### Quick Setup

1. **Clone or download the project**
2. **Install dependencies**:
   ```bash
   python3 install_dependencies.py
   ```
   
   Or manually:
   ```bash
   pip install -r requirements.txt
   ```

3. **Ensure Chrome and ChromeDriver are installed**:
   - **macOS**: `brew install chromedriver`
   - **Ubuntu**: `sudo apt install chromium-chromedriver`
   - **Windows**: Download from [ChromeDriver](https://chromedriver.chromium.org/)

### Manual Dependencies

```bash
pip install selenium>=4.15.0 beautifulsoup4>=4.12.0 lxml>=4.9.0
```

## Usage

### Method 1: Complete Automation

1. **Run the search script**:
   ```bash
   python3 pbc_property_search.py
   ```
   - This will open a browser and fill out the search form
   - Manually click "Search" when prompted
   - Leave the browser open with results

2. **Run the extractor**:
   ```bash
   python3 property_results_extractor.py
   ```
   - The script will connect to your existing browser session
   - Follow the prompts to extract data
   - Data will be saved to timestamped CSV and JSON files

### Method 2: Manual Search + Extraction

1. **Manually perform your search**:
   - Go to [Palm Beach County Property Appraiser](https://pbcpao.gov/)
   - Perform your property search
   - Navigate to results page

2. **Run the extractor**:
   ```bash
   python3 property_results_extractor.py
   ```
   - Choose to open a new browser or provide the results URL
   - The script will extract data from your results

## Output Files

The extractor creates timestamped files:

- **CSV File**: `palm_beach_properties_YYYYMMDD_HHMMSS.csv`
  - Ready for Excel, Google Sheets, or database import
  - All property fields as columns
  - UTF-8 encoded for international characters

- **JSON File**: `palm_beach_properties_YYYYMMDD_HHMMSS.json`
  - Structured data backup
  - Programmatically accessible
  - Preserves data types and nested information

- **Log File**: `property_extractor_YYYYMMDD.log`
  - Detailed extraction logs
  - Error messages and debugging info
  - Performance metrics

## Extracted Data Fields

| Field | Description |
|-------|-------------|
| `property_address` | Full property address |
| `owner_name` | Property owner/taxpayer name |
| `property_value` | Assessed/appraised value |
| `assessed_value` | Assessed value for taxes |
| `market_value` | Market value estimate |
| `square_footage` | Building square footage |
| `property_type` | Property classification |
| `parcel_id` | Parcel/account number |
| `sale_price` | Most recent sale price |
| `sale_date` | Most recent sale date |
| `year_built` | Construction year |
| `lot_size` | Lot/land size |
| `bedrooms` | Number of bedrooms |
| `bathrooms` | Number of bathrooms |
| `municipality` | City/municipality |
| `zoning` | Zoning classification |
| `tax_amount` | Annual tax amount |
| `record_url` | Link to detailed record |

## Advanced Features

### Debug Mode
Enable detailed logging and debugging:
```bash
python3 property_results_extractor.py
# Answer 'y' when asked about debug mode
```

### Pagination Support
The extractor automatically:
- Detects paginated results
- Processes all pages sequentially
- Combines data from multiple pages
- Handles up to 50 pages (configurable)

### Structure Detection
The script intelligently handles:
- **Table-based results**: Extracts from HTML tables
- **Container-based results**: Parses div/section containers
- **Text-based results**: Uses pattern matching for unstructured data
- **Mixed formats**: Adapts to different page layouts

### Error Recovery
- Continues extraction if individual records fail
- Logs all errors for troubleshooting
- Provides fallback extraction methods
- Graceful handling of missing data

## Configuration Options

### Search Parameters (in `pbc_property_search.py`)
Modify the search parameters by editing the script:
- Property type (Commercial, Residential, etc.)
- Municipality selection
- Square footage ranges
- Date ranges for sales
- Other search criteria

### Extraction Settings (in `property_results_extractor.py`)
- `debug_mode`: Enable detailed logging
- `headless`: Run browser in background
- Page timeout settings
- Maximum pages to process
- Field extraction patterns

## Troubleshooting

### Common Issues

1. **ChromeDriver not found**:
   ```bash
   # Install ChromeDriver
   brew install chromedriver  # macOS
   sudo apt install chromium-chromedriver  # Ubuntu
   ```

2. **No data extracted**:
   - Verify you're on a results page
   - Check that results are visible
   - Try refreshing the page
   - Enable debug mode for detailed logs

3. **Browser connection issues**:
   - Close existing Chrome instances
   - Run with new browser session
   - Check for Chrome updates

4. **Permission errors**:
   ```bash
   chmod +x property_results_extractor.py
   chmod +x pbc_property_search.py
   ```

### Debug Information

Enable debug mode for detailed information:
- Page structure analysis
- Element detection logs
- Extraction attempt details
- Error stack traces

## File Structure

```
papa-rain/
├── property_results_extractor.py  # Main extraction script
├── pbc_property_search.py         # Search automation
├── smart_csv_extractor.py         # Legacy extractor
├── install_dependencies.py        # Setup helper
├── requirements.txt               # Python dependencies
├── setup.py                       # Package setup
└── README.md                      # This file
```

## Requirements

- **Python 3.7+**
- **Google Chrome** browser
- **ChromeDriver** (compatible with Chrome version)
- **Internet connection**
- **Selenium 4.15+**
- **BeautifulSoup 4.12+**

## Legal and Ethical Use

This tool is designed for legitimate property research purposes:
- Real estate analysis
- Market research
- Academic studies
- Personal property research

**Please use responsibly**:
- Respect the website's terms of service
- Don't overload the server with requests
- Use reasonable delays between operations
- Consider the website's resources

## Support

For issues or questions:
1. Check the log files for detailed error information
2. Enable debug mode for more information
3. Verify all dependencies are installed correctly
4. Ensure Chrome and ChromeDriver versions are compatible

## License

This project is provided as-is for educational and legitimate research purposes.
