import requests
import argparse
import sys
import json

def print_articles(articles):
    if not articles:
        print("    No articles to display.")
        return
    for i, art in enumerate(articles):
        print(f"    [{i+1}] {art.get('headline', 'No Headline')}")
        print(f"        Category: {art.get('category')}")
        print(f"        Audio: {'Available' if art.get('headline_hls_base_url') else 'Not processed'}")

def test_briefing(email, password, base_url="http://localhost:8000", show_raw=False):
    print(f"--- Testing Daily Briefing Endpoint ---")
    print(f"Base URL: {base_url}")
    print(f"Logging in as: {email}")

    # 1. Login to get token (including /api/v1 prefix)
    login_url = f"{base_url}/api/v1/auth/login"
    login_payload = {
        "email": email,
        "password": password
    }

    try:
        response = requests.post(login_url, json=login_payload)
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")
            print(response.text)
            return

        token_data = response.json()
        token = token_data.get("access_token")
        if not token:
            print("Access token not found in login response.")
            return

        print("Login successful.")

        # 2. Call Daily Briefing endpoint (including /api/v1 prefix)
        briefing_url = f"{base_url}/api/v1/news/briefing"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        # Test with defaults
        print("\nCalling /news/briefing (defaults)...")
        briefing_res = requests.get(briefing_url, headers=headers)
        
        if briefing_res.status_code == 200:
            data = briefing_res.json()
            print(f"Status: {briefing_res.status_code}")
            if show_raw:
                print("Raw Payload:")
                print(json.dumps(data, indent=2))
            else:
                print(f"Interests: {data.get('interests')}")
                print(f"Count: {data.get('count')}")
                print_articles(data.get("articles", []))
        else:
            print(f"Default briefing call failed: {briefing_res.status_code}")

        # 3. Test with specific interests
        print("\nCalling /news/briefing (custom categories)...")
        interest_params = {"interests": ["Tech", "Finance"]}
        custom_res = requests.get(briefing_url, headers=headers, params=interest_params)
        
        if custom_res.status_code == 200:
            data = custom_res.json()
            print(f"Status: {custom_res.status_code}")
            if show_raw:
                print("Raw Payload:")
                print(json.dumps(data, indent=2))
            else:
                print(f"Applied Interests: {data.get('interests')}")
                print(f"Articles Found: {data.get('count')}")
                print_articles(data.get("articles", []))
        else:
            print(f"Custom briefing call failed: {custom_res.status_code}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test HyPot News Daily Briefing Endpoint")
    parser.add_argument("--email", required=True, help="User email")
    parser.add_argument("--password", required=True, help="User password")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API")
    parser.add_argument("--raw", action="store_true", help="Print the complete raw JSON payload")

    args = parser.parse_args()
    test_briefing(args.email, args.password, args.url, args.raw)
