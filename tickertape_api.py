import requests
import json
from config import my_cookies, my_csrf_token
import datetime
import pandas as pd

# Configuration Constants
API_BASE_URL = "https://analyze.api.tickertape.in/stocks/scorecard"
DEFAULT_HEADERS = {
    "accept-version": "8.14.0",
    "x-csrf-token": my_csrf_token,
}


def get_stock_scorecard(sid, cookies=None, csrf_token=None, verbose=False):
    """
    Fetches the stock scorecard from the Tickertape API for a given stock sid.

    Args:
        sid (str): The stock's unique system ID.
        cookies (dict, optional): Dictionary of cookies to include in the request.
        csrf_token (str, optional): The CSRF token to include in the request header.
        verbose (bool, optional): Whether to print detailed request information.

    Returns:
        dict: The JSON response from the API, or None if an error occurred.
    """
    url = f"{API_BASE_URL}/{sid}"
    headers = DEFAULT_HEADERS.copy()
    
    if csrf_token:
        headers["x-csrf-token"] = csrf_token
    headers["accept-version"] = "<redacted>"  # Replace with actual value if known

    if verbose:
        print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, cookies=cookies)
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"Error fetching scorecard for {sid}: {e}")
        return None

def extract_scorecard_summary(scorecard_data):
    """
    Extract a summary of key metrics from the stock scorecard.

    Args:
        scorecard_data (dict): The scorecard data from the Tickertape API.

    Returns:
        dict: A dictionary of extracted scorecard summary metrics.
    """
    if not scorecard_data or not scorecard_data.get('data'):
        return {}

    summary = {}
    
    # Mapping of key categories to their desired summary keys
    category_mapping = {
        'Performance': {
            'key': 'Performance_Score',
            'score_key': 'Avg',
            'description_key': 'Performance_Description'
        },
        'Valuation': {
            'key': 'Valuation_Score',
            'score_key': 'High',
            'description_key': 'Valuation_Description'
        },
        'Growth': {
            'key': 'Growth_Score',
            'score_key': 'Avg_1',
            'description_key': 'Growth_Description'
        },
        'Profitability': {
            'key': 'Profitability_Score',
            'score_key': 'High_1',
            'description_key': 'Profitability_Description'
        },
        'Entry point': {
            'key': 'Entry_Point_Score',
            'score_key': 'Avg_2',
            'description_key': 'Entry_Point_Description'
        },
        'Red flags': {
            'key': 'Red_Flags_Score',
            'score_key': 'Avg_3',
            'description_key': 'Red_Flags_Description'
        }
    }

    for item in scorecard_data['data']:
        category = item.get('name', '')
        description = item.get('description', '')
        score_info = item.get('score', {})

        if category in category_mapping:
            mapping = category_mapping[category]
            
            # Add score
            if score_info and 'value' in score_info:
                summary[mapping['key']] = score_info['value']
                summary[mapping['description_key']] = description

            # Add sub-elements details if available
            if item.get('elements'):
                sub_scores = {}
                for element in item['elements']:
                    if element.get('display', False):
                        element_score = element.get('score', {})
                        element_title = element.get('title', 'Unnamed')
                        
                        if element_score and 'value' in element_score and 'max' in element_score:
                            sub_scores[f"{element_title}_Score"] = f"{element_score['value']}/{element_score['max']}"
                
                # Update summary with sub-scores
                summary.update(sub_scores)

    return summary

def extract_scorecard_summary_csv(scorecard_data):
    """
    Extract a simplified summary of key metrics from the stock scorecard.
    
    Args:
        scorecard_data (dict): The scorecard data from the Tickertape API.
    
    Returns:
        dict: A dictionary of simplified scorecard summary metrics.
    """
    # Default summary with 'N/A' values
    summary = {
        'Performance_Score': 'N/A', 'Valuation_Score': 'N/A', 
        'Growth_Score': 'N/A', 'Profitability_Score': 'N/A', 
        'Entry_Point_Score': 'N/A', 'Red_Flags_Score': 'N/A'
    }

    # Return default if no data
    if not scorecard_data or not scorecard_data.get('data'):
        return summary

    # Mapping of category names to summary keys
    category_map = {
        'Performance': 'Performance_Score',
        'Valuation': 'Valuation_Score',
        'Growth': 'Growth_Score',
        'Profitability': 'Profitability_Score',
        'Entry point': 'Entry_Point_Score',
        'Red flags': 'Red_Flags_Score'
    }

    try:
        # Process each item in the scorecard data
        for item in scorecard_data['data']:
            name = item.get('name', '')
            score = item.get('score', {})
            tag = item.get('tag', '')

            # Update summary if category exists in mapping
            if name in category_map:
                # Use score value for most categories
                if score and 'value' in score:
                    summary[category_map[name]] = score['value']
                
                # Use tag for Entry point and Red flags
                elif name in ['Entry point', 'Red flags']:
                    summary[category_map[name]] = tag

        return summary

    except Exception as e:
        print(f"Error extracting scorecard summary: {e}")
        return summary

def pretty_print_scorecard(scorecard_data):
    """
    Pretty print the stock scorecard in a more readable format.
    
    Args:
        scorecard_data (dict): The scorecard data from the Tickertape API.
    """
    if not scorecard_data or not scorecard_data.get('data'):
        print("No scorecard data available.")
        return

    for item in scorecard_data['data']:
        # Print main item details with score if available
        score_info = item.get('score', {})
        score_str = f" ({score_info.get('value', 'N/A')})" if score_info and score_info.get('value') is not None else ""
        
        print(f"{item['name']} ({item.get('tag', 'N/A')}){score_str} : {item.get('description', 'No description')}")
        
        # Handle elements for Entry Point and Red Flags
        if item.get('elements'):
            for element in item['elements']:
                if element.get('display', False):
                    # Add score for elements that have a score
                    element_score = element.get('score', {})
                    score_detail = f" ({element_score.get('value', 'N/A')}/{element_score.get('max', 10)})" if element_score and element_score.get('value') is not None else ""
                    
                    # Only print description if it's not None
                    description = element.get('description')
                    description_str = f": {description}" if description and description != 'None' else ""
                    
                    print(f"\t{element.get('title', 'Unnamed')}{score_detail}{description_str}")

def format_market_cap(market_cap):
    """
    Format market capitalization to a readable string.

    Args:
        market_cap (float): Market capitalization value.

    Returns:
        str: Formatted market capitalization.
    """
    if market_cap >= 100000:
        return f"{market_cap/100000:.2f} L Cr"
    elif market_cap >= 1000:
        return f"{market_cap/1000:.2f} Cr"
    else:
        return f"{market_cap:.2f} Cr"


def create_screener_payload():
    """
    Create payload for stock screener query.

    Returns:
        dict: Payload configuration for Tickertape API screener.
    """
    return {
        "match": {
            "chMutHldng6M": {"g": 0.1, "l": 18.25},
            "instown3": {"g": 0.1, "l": 9.17},
            "forInstHldng6M": {"g": 0.1, "l": 70.39},
            "forInstHldng3M": {"g": 0.1, "l": 70.39},
            "incEbi": {"g": 0.1, "l": 178677}
        },
        "project": [
            "subindustry", "mrktCapf", "lastPrice", "apef", 
            "chMutHldng6M", "instown3", 
            "forInstHldng6M", "forInstHldng3M", "incEbi", "12mpctN", "estAvg"
        ],
        "offset": 20,
        "count": 200,
        "sids": []
    }

def calculate_column_widths(df):
    """
    Calculate optimal column widths based on content.

    Args:
        df (pd.DataFrame): Input DataFrame

    Returns:
        list: Calculated column widths in pixels
    """
    # Start with header lengths
    column_widths = [len(str(col)) * 8 for col in df.columns]
    
    # Check content of each column
    for col_index, col in enumerate(df.columns):
        # Get max length of content in the column
        max_content_length = df[col].astype(str).map(len).max()
        
        # Adjust width based on content, with some padding
        column_widths[col_index] = max(
            column_widths[col_index], 
            max_content_length
        ) * 8  # Multiply by 8 to convert to approximate pixels
        
        # Cap maximum width to prevent extremely wide columns
        column_widths[col_index] = min(column_widths[col_index], 300)
    
    return column_widths

def export_to_file(export_data):
    """
    Export stock data to Excel file with advanced formatting and dynamic column sizing.

    Args:
        export_data (list): List of stock entries to export
    """
    if not export_data:
        print("No data to export.")
        return

    current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_filename = f'tickertape_screener_with_scores_{current_time}.xlsx'
    
    # Define column order with more descriptive names
    column_order = [
        'Company Name', 'Ticker', 'Sector', 'Sub-Sector', 
        'PE Ratio', 'Last Price', 'Market Cap (Cr)', 
        'MF Holding Change (6M)', 'MF Holding Change (3M)', 
        'FII Holding Change (6M)', 'FII Holding Change (3M)', 
        'EBITDA', '1Y Return vs Nifty (%)', '1Y Forward EBITDA Growth (%)',
        'Valuation Score', 'Performance Score', 
        'Profitability Score', 'Growth Score', 
        'Entry Point Score', 'Red Flags Score',
        'Top 20 All Columns'
    ]

    # Create DataFrame
    df = pd.DataFrame(export_data)[column_order]

    # Apply formatting to numeric columns
    numeric_columns = [
        'PE Ratio', 'Last Price', 'Market Cap (Cr)', 
        'MF Holding Change (6M)', 'MF Holding Change (3M)', 
        'FII Holding Change (6M)', 'FII Holding Change (3M)', 
        'EBITDA', '1Y Return vs Nifty (%)', '1Y Forward EBITDA Growth (%)'
    ]
    
    # Convert to numeric, replacing errors with NaN
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Create Excel writer
    with pd.ExcelWriter(excel_filename, engine='xlsxwriter') as writer:
        # Write DataFrame to Excel
        df.to_excel(writer, index=False, sheet_name='Stock Screener')
        
        # Get the xlsxwriter workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets['Stock Screener']
        
        # Define cell formats
        header_format = workbook.add_format({
            'bold': True, 
            'text_wrap': True,
            'valign': 'top', 
            'fg_color': '#D7E4BC', 
            'border': 1
        })
        
        number_format = workbook.add_format({'num_format': '0.00'})
        
        # Write the column headers with the defined format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Calculate and apply dynamic column widths
        column_widths = calculate_column_widths(df)
        for col_num, width in enumerate(column_widths):
            # Apply different formats based on column type
            if df.columns[col_num] in numeric_columns:
                worksheet.set_column_pixels(col_num, col_num, width, number_format)
            else:
                worksheet.set_column_pixels(col_num, col_num, width)
        
        # Add a filter
        worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
    
    print(f"Exported data to {excel_filename}")
    print(f"Total stocks exported: {len(df)}")