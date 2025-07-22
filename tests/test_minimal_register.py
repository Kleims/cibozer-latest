import requests
from datetime import datetime

# Test with curl-like request
url = "http://localhost:5001/register"
data = {
    "email": f"test_{datetime.now().timestamp()}@example.com",
    "password": "TestPass123",  # Simple password without special chars
    "password_confirm": "TestPass123",
    "full_name": "Test User"
}

response = requests.post(url, data=data)
print(f"Status: {response.status_code}")

# Save response for inspection
with open("register_response.html", "w", encoding="utf-8") as f:
    f.write(response.text)
    
print("Response saved to register_response.html")