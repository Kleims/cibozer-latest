import requests
from datetime import datetime

# Simple registration test
url = "http://localhost:5001/register"
data = {
    "email": f"test_{datetime.now().timestamp()}@example.com",
    "password": "TestPass123!",
    "password_confirm": "TestPass123!",
    "full_name": "Test User",
    "agree_terms": "on"
}

print("Sending registration request...")
response = requests.post(url, data=data)
print(f"Status: {response.status_code}")
print(f"Response length: {len(response.text)}")

# Check for error messages
if "error" in response.text.lower() or "exception" in response.text.lower():
    print("\nPossible error found in response")
    # Find error message in HTML
    import re
    error_match = re.search(r'<div[^>]*class="[^"]*alert[^"]*"[^>]*>(.*?)</div>', response.text, re.DOTALL)
    if error_match:
        print(f"Error message: {error_match.group(1).strip()}")