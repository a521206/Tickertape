import asyncio
import aiohttp
import requests
import pandas as pd

from tickertape_api import extract_scorecard_summary_csv, DEFAULT_HEADERS, create_screener_payload, export_to_file
from config import my_cookies

url = "https://api.tickertape.in/screener/query"

API_BASE_URL = "https://analyze.api.tickertape.in/stocks/scorecard"


def fetch_screener_data(url):
    """
    Fetch stock screener data from Tickertape API.

    Args:
        url (str): API endpoint URL

    Returns:
        dict: API response data or None
    """
    payload = create_screener_payload()
    
    try:
        response = requests.post(url, headers=DEFAULT_HEADERS, cookies=my_cookies, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching screener data: {e}")
        return None

async def fetch_scorecard_async(session, sid):
    """
    Asynchronously fetch stock scorecard.

    Args:
        session (aiohttp.ClientSession): Async HTTP session
        sid (str): Stock ID

    Returns:
        tuple: Stock ID and scorecard data
    """
    try:
        async with session.get(
            f"{API_BASE_URL}/{sid}", 
            headers=DEFAULT_HEADERS,
            cookies={
                "jwt": my_cookies['jwt']
            }
        ) as response:
            if response.status == 200:
                scorecard = await response.json()
                return sid, scorecard
            else:
                print(f"Error fetching scorecard for {sid}: HTTP {response.status}")
                return sid, None
    except Exception as e:
        print(f"Error fetching scorecard for {sid}: {e}")
        return sid, None

async def process_stock_data_async(data):
    """
    Process stock data asynchronously.

    Args:
        data (dict): Stock data from Tickertape API

    Returns:
        tuple: Export data and error tracking
    """
    errors = {
        'scorecard_fetch_errors': 0,
        'scorecard_parse_errors': 0
    }
    export_data = []

    async with aiohttp.ClientSession() as session:
        # Prepare tasks for async scorecard fetching
        scorecard_tasks = [
            fetch_scorecard_async(session, stock_data['sid']) 
            for stock_data in data['data']['results']
        ]
        
        # Wait for all scorecard tasks to complete
        scorecard_results = await asyncio.gather(*scorecard_tasks)
        
        # Create a mapping of sid to scorecard
        scorecard_map = {sid: scorecard for sid, scorecard in scorecard_results}

        for stock_data in data['data']['results']:
            info = stock_data['stock']['info']
            ratios = stock_data['stock']['advancedRatios']
            
            # Get scorecard from map
            scorecard = scorecard_map.get(stock_data['sid'])
            
            try:
                scorecard_summary = extract_scorecard_summary_csv(scorecard) if scorecard else {}
            except Exception as e:
                print(f"Error parsing scorecard for {stock_data['sid']}: {e}")
                errors['scorecard_parse_errors'] += 1
                scorecard_summary = {}
            
            # Prepare stock entry
            stock_entry = {
                'Company Name': info['name'],
                'Ticker': info['ticker'],
                'Sector': info.get('sector', 'N/A'),
                'Sub-Sector': ratios.get('subindustry', 'N/A'),
                'PE Ratio': ratios.get('apef', 0),
                'Last Price': ratios.get('lastPrice', 0),
                'Market Cap (Cr)': ratios.get('mrktCapf', 0),
                'MF Holding Change (6M)': ratios.get('chMutHldng6M', 0),
                'MF Holding Change (3M)': ratios.get('instown3', 0),
                'FII Holding Change (6M)': ratios.get('forInstHldng6M', 0),
                'FII Holding Change (3M)': ratios.get('forInstHldng3M', 0),
                'EBITDA': ratios.get('incEbi', 0),
                '1Y Return vs Nifty (%)': ratios.get('12mpctN', 0),
                '1Y Forward EBITDA Growth (%)': ratios.get('estAvg', 0),
                'Valuation Score': scorecard_summary.get('Valuation_Score', 'N/A'),
                'Performance Score': scorecard_summary.get('Performance_Score', 'N/A'),
                'Profitability Score': scorecard_summary.get('Profitability_Score', 'N/A'),
                'Growth Score': scorecard_summary.get('Growth_Score', 'N/A'),
                'Entry Point Score': scorecard_summary.get('Entry_Point_Score', 'N/A'),
                'Red Flags Score': scorecard_summary.get('Red_Flags_Score', 'N/A')
            }
            
            export_data.append(stock_entry)
    
    return export_data, errors

def identify_top_holding_changes(export_data):
    """
    Identify top stocks based on holding changes and mark them in the dataset.

    Args:
        export_data (list): List of stock entries

    Returns:
        tuple: Modified export_data and top holding change details
    """
    # Convert export_data to DataFrame for easier analysis
    df = pd.DataFrame(export_data)
    
    # Define holding change columns
    holding_columns = [
        'MF Holding Change (6M)', 
        'MF Holding Change (3M)', 
        'FII Holding Change (6M)', 
        'FII Holding Change (3M)'
    ]
    
    # Initialize results dictionary
    top_20_results = {}
    top_20_per_column = {}
    
    # Add new columns to track top holding changes
    for column in holding_columns:
        # Sort in descending order and get top 20
        top_20 = df.nlargest(20, column)[['Company Name', 'Ticker', column]]
        top_20_results[column] = top_20.to_dict('records')
        top_20_per_column[column] = set(top_20[column].values)
        
    # Identify stocks in top 20 for all 4 columns
    all_top_20_stocks = df[
        (df['MF Holding Change (6M)'].isin(top_20_per_column['MF Holding Change (6M)'])) &
        (df['MF Holding Change (3M)'].isin(top_20_per_column['MF Holding Change (3M)'])) &
        (df['FII Holding Change (6M)'].isin(top_20_per_column['FII Holding Change (6M)'])) &
        (df['FII Holding Change (3M)'].isin(top_20_per_column['FII Holding Change (3M)']))
    ]
    
    # Add a column to mark stocks in top 20 for all columns
    df['Top 20 All Columns'] = df.apply(
        lambda row: 'Yes' if (
            row['MF Holding Change (6M)'] in top_20_per_column['MF Holding Change (6M)'] and
            row['MF Holding Change (3M)'] in top_20_per_column['MF Holding Change (3M)'] and
            row['FII Holding Change (6M)'] in top_20_per_column['FII Holding Change (6M)'] and
            row['FII Holding Change (3M)'] in top_20_per_column['FII Holding Change (3M)']
        ) else 'No', 
        axis=1
    )
    
    # Print stocks in top 20 for all columns
    print("\nStocks in Top 20 for All Holding Change Columns:")
    top_all_columns = all_top_20_stocks[['Company Name', 'Ticker']]
    for _, stock in top_all_columns.iterrows():
        print(f"{stock['Company Name']} ({stock['Ticker']})")
    
    # Convert back to list of dictionaries
    modified_export_data = df.to_dict('records')
    
    return modified_export_data, top_20_results

def main():
    """
    Main function to fetch and export stock screener data with scorecards.
    """
    data = fetch_screener_data(url)
    if not data:
        print("Failed to fetch screener data")
        return
    
    # Run async processing
    export_data, errors = asyncio.run(process_stock_data_async(data))
    
    # Identify top holding change stocks and modify export data
    export_data, top_holding_changes = identify_top_holding_changes(export_data)
    
    # Export to file
    export_to_file(export_data)
    
    print(f"\nTotal stocks found: {len(export_data)}")
    print(f"Scorecard Fetch Errors: {errors['scorecard_fetch_errors']}")
    print(f"Scorecard Parse Errors: {errors['scorecard_parse_errors']}")

if __name__ == "__main__":
    main()