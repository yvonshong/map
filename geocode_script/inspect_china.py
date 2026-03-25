import json

with open('data/china_compliant.json', 'r') as f:
    data = json.load(f)

print(f"Type: {data.get('type')}")
print(f"Feature count: {len(data.get('features', []))}")
for f in data.get('features', [])[:5]:
    print(f"Name: {f['properties'].get('name')}, Type: {f['geometry']['type']}")
