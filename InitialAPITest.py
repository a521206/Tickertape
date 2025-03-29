import requests
import json
from tickertape_api import get_stock_scorecard, pretty_print_scorecard

# Cookies for Tickertape API authentication
my_cookies = {
    "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2MTA1MGFmOGJlMTFlZjE3MTYyN2JhYjkiLCJjc3JmVG9rZW4iOiJhNzRiZmViNCIsInJlZnJlc2hUb2tlbiI6ImJkZTBlODE1LWEyMDYtNDFjYy1hMDdhLTNmNmFjOGRhYjZjY182NmI0M2M2NjQ4YmJkMzU4ZTZmNmE0OTUiLCJzdWJzSWQiOiJQMDAxMiIsImlhdCI6MTc0MjcxMDUwMywiZXhwIjoxNzQyNzk2OTAyfQ.o6kW2AiSZEbvnv0azP53OKQDRXXJlLFrA-Uxd9GvQQ4"
}

# CSRF token for API authentication
my_csrf_token = "a74bfeb4"

def main():
    """
    Main execution function to demonstrate stock scorecard retrieval and display.
    """
    # Fetch and display scorecard for a specific stock
    stock_data = get_stock_scorecard("ONGC", cookies=my_cookies, csrf_token=my_csrf_token, verbose=True)

    if stock_data:
        pretty_print_scorecard(stock_data)

if __name__ == "__main__":
    main()