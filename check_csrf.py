import requests

# Get the login page and extract CSRF token
session = requests.Session()
response = session.get('http://localhost:5000/admin/login')

print(f"Status: {response.status_code}")
print(f"\nSearching for CSRF token in response...")

# Look for csrf_token in the response
if 'csrf_token' in response.text:
    print("Found 'csrf_token' in response")
    # Extract the token value
    import re
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', response.text)
    if match:
        csrf_token = match.group(1)
        print(f"CSRF Token: {csrf_token}")
    else:
        print("Could not extract CSRF token value")
else:
    print("No CSRF token found in response")
    
# Check if there's an error
if 'jinja2.exceptions' in response.text or 'TemplateError' in response.text:
    print("\nTemplate error detected!")
    print(response.text[:500])