import json
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

print("Loading map data...")
# Load base world map
with open('data/countries.geojson', 'r') as f:
    world_data = json.load(f)

# Load compliant China map (with provinces)
with open('data/china_compliant.json', 'r') as f:
    china_data = json.load(f)

print("Processing China geometry...")
# Convert all China features to shapely geometries
china_shapes = []
for f in china_data.get('features', []):
    s = shape(f['geometry'])
    if s.is_valid:
        china_shapes.append(s)
    else:
        china_shapes.append(s.buffer(0))

# Create a single unified China polygon for subtraction
# This might be slow if high res, but necessary to cut India correctly
china_union = unary_union(china_shapes)

new_features = []
removed_count = 0
modified_count = 0

print("Processing world features...")
for f in world_data['features']:
    props = f.get('properties', {})
    name = props.get('name', '')
    
    # 1. Remove original China and Taiwan
    if name in ['China', 'Taiwan', 'Hong Kong', 'Macao']:
        removed_count += 1
        continue
    
    # 2. Fix India border (Southern Tibet / Aksai Chin)
    if name == 'India':
        print("Fixing India border (subtracting disputed areas)...")
        india_shape = shape(f['geometry'])
        if not india_shape.is_valid:
            india_shape = india_shape.buffer(0)
            
        # Subtract China from India
        try:
            fixed_india = india_shape.difference(china_union)
            
            # Update geometry
            f['geometry'] = mapping(fixed_india)
            modified_count += 1
        except Exception as e:
            print(f"Error filtering India: {e}")
            
    # 3. Fix other neighbors if needed (Tajikistan, etc) - optional but good
    # For now just India is the big visual one user noticed
            
    new_features.append(f)

print(f"Removed {removed_count} features. Modified {modified_count} features.")

# Add detailed China provinces
china_features = china_data.get('features', [])
new_features.extend(china_features)

# Create final feature collection
final_data = {
    "type": "FeatureCollection",
    "features": new_features
}

with open('data/world_borders_compliant.json', 'w') as f:
    json.dump(final_data, f)
    
print("Saved merged map to data/world_borders_compliant.json")
