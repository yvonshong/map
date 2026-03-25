import json

with open('data/countries.geojson', 'r') as f:
    data = json.load(f)

print(f"Total features: {len(data['features'])}")
for f in data['features']:
    props = f.get('properties', {})
    name = props.get('name', 'Unknown')
    # Check for China, Taiwan, India (for border issues)
    if 'China' in name or 'Taiwan' in name or 'India' in name:
        print(f"Found: {name}, ID: {f.get('id')}, Type: {f['geometry']['type']}")
