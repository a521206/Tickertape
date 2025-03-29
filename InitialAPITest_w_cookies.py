import requests
import json

def get_stock_scorecard(stock_code, cookies=None, csrf_token=None):
    """
    Fetches the stock scorecard from the Tickertape API for a given stock code.

    Args:
        stock_code (str): The stock code (e.g., "KAC").
        cookies (dict, optional): Dictionary of cookies to include in the request. Defaults to None.
        csrf_token (str, optional): The CSRF token to include in the request header. Defaults to None.

    Returns:
        dict: The JSON response from the API, or None if an error occurred.
    """
    url = f"https://analyze.api.tickertape.in/stocks/scorecard/{stock_code}"
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en,te;q=0.9,hi;q=0.8",
        "accept-version": "<redacted>", # Replace with actual value if you know it.
        "origin": "https://www.tickertape.in",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    }
    
    if csrf_token:
        headers["x-csrf-token"] = csrf_token

    try:
        response = requests.get(url, headers=headers, cookies=cookies)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        print(f"Response content: {response.text}")
        return None


# --- Example Usage ---
# Replace with your actual cookies and csrf token

# Cookies from Tickertape domain
my_cookies = {
    "AMP_MKTG_d9d4ec74fa": "JTdCJTdE",
    "AMP_d9d4ec74fa": "JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjIwNWFmZjFjZS02MjcxLTQ5NTktODBiNS02NTM3NDdiZGVmYzYlMjIlMkMlMjJ1c2VySWQlMjIlM0ElMjI2MTA1MGFmOGJlMTFlZjE3MTYyN2JhYjklMjIlMkMlMjJzZXNzaW9uSWQlMjIlM0ExNzMxMjE3NjAyNzExJTJDJTIyb3B0T3V0JTIyJTNBZmFsc2UlMkMlMjJsYXN0RXZlbnRUaW1lJTIyJTNBMTczMTIxNzYwMjcxOCUyQyUyMmxhc3RFdmVudElkJTIyJTNBMTQ2NSU3RA==",
    "_clck": "18pmpna%7C2%7Cfug%7C0%7C1666",
    "_clsk": "aai11w%7C1742717077463%7C1%7C1%7Ce.clarity.ms%2Fcollect",
    "_ga": "GA1.1.1613880991.1721830860",
    "_ga_4J2474SK8Y": "GS1.1.1742717077.226.1.1742717134.3.0.0",
    "_gcl_au": "1.1.1370083377.1737546348",
    "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiI2MTA1MGFmOGJlMTFlZjE3MTYyN2JhYjkiLCJjc3JmVG9rZW4iOiJhNzRiZmViNCIsInJlZnJlc2hUb2tlbiI6ImJkZTBlODE1LWEyMDYtNDFjYy1hMDdhLTNmNmFjOGRhYjZjY182NmI0M2M2NjQ4YmJkMzU4ZTZmNmE0OTUiLCJzdWJzSWQiOiJQMDAxMiIsImlhdCI6MTc0MjcxMDUwMywiZXhwIjoxNzQyNzk2OTAyfQ.o6kW2AiSZEbvnv0azP53OKQDRXXJlLFrA-Uxd9GvQQ4",
    "moe_uuid": "2119c1ba-d57a-490e-bf7c-c273b462ec9b",
    "scnm": "Vishal",
    "web-ad-61050af8be11ef171627bab9null": "true",
    "x-csrf-token-tickertape-prod": "a74bfeb4"
}

# CSRF Token from the jwt token
my_csrf_token = "a74bfeb4"

# Example usage
stock_data = get_stock_scorecard("KAC", cookies=my_cookies, csrf_token=my_csrf_token)

if stock_data:
    print(json.dumps(stock_data, indent=2))  # Pretty-print the JSON response