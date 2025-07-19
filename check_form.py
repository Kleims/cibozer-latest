import re

with open('templates/create.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all form field names
pattern = r'name="([^"]+)"'
matches = re.findall(pattern, content)

print("Form field names found in create.html:")
for name in matches:
    if name != 'csrf_token':
        print(f"  - {name}")

# Check for old field names
if 'diet_type' in content:
    print("\n⚠️  WARNING: Found old field name 'diet_type'")
if 'pattern' in content:
    print("⚠️  WARNING: Found old field name 'pattern'")

# Check for new field names
if 'name="diet"' in content:
    print("\n✅ Found correct field name 'diet'")
if 'name="meal_structure"' in content:
    print("✅ Found correct field name 'meal_structure'")