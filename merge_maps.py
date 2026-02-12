import json
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

print("Loading map data...")
# Load base world map
with open('data/countries.geojson', 'r') as f:
    world_data = json.load(f)

# Load compliant China map (with provinces)
# Load compliant China map (with provinces)
with open('data/china_compliant.json', 'r') as f:
    china_data = json.load(f)

# Load Japan prefectures
print("Loading Japan data...")
with open('data/japan.geojson', 'r') as f:
    japan_data = json.load(f)

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
    
    # 1. Remove original China, Taiwan, and Japan (and other conflicting regions)
    if name in ['China', 'Taiwan', 'Hong Kong', 'Macao', 'Japan']:
        removed_count += 1
        print(f"Removing low-res feature: {name}")
        continue
    
    # Extra safety check for variations like "People's Republic of China" if they existed
    if 'China' in name and name != 'China':
         print(f"Removing potential China variant: {name}")
         removed_count += 1
         continue
    
    # 2. Fix India border (Southern Tibet / Aksai Chin) AND other neighbors
    # List of countries that might overlap with China's compliant borders
    CHINA_NEIGHBORS = [
        'India', 'Mongolia', 'Russia', 'North Korea', 'Vietnam', 'Laos', 
        'Myanmar', 'Burma', 'Bhutan', 'Nepal', 'Pakistan', 'Afghanistan',
        'Tajikistan', 'Kyrgyzstan', 'Kazakhstan'
    ]
    
    if name in CHINA_NEIGHBORS:
        print(f"Fixing border for neighbor: {name}...")
        try:
            neighbor_shape = shape(f['geometry'])
            if not neighbor_shape.is_valid:
                neighbor_shape = neighbor_shape.buffer(0)
            
            # Subtract China from Neighbor
            fixed_shape = neighbor_shape.difference(china_union)
            
            # Update geometry
            f['geometry'] = mapping(fixed_shape)
            modified_count += 1
        except Exception as e:
            print(f"Error filtering {name}: {e}")
            
    # 3. Fix other neighbors if needed (Tajikistan, etc) - optional but good
    # For now just India is the big visual one user noticed
            
    new_features.append(f)

print(f"Removed {removed_count} features. Modified {modified_count} features.")

# Add detailed China provinces
china_features = china_data.get('features', [])
print(f"Adding {len(china_features)} features from China map.")
new_features.extend(china_features)

# Add detailed Japan prefectures
japan_features = japan_data.get('features', [])
print(f"Adding {len(japan_features)} features from Japan map.")
new_features.extend(japan_features)

# Create final feature collection
# Optimize: Simplify geometries to reduce file size
print("Simplifying geometries for performance...")
simplified_features = []
SIMPLIFICATION_TOLERANCE = 0.005 # degrees, approx 500m

for f in new_features:
    try:
        s = shape(f['geometry'])
        # Simplify preserving topology
        simplified_s = s.simplify(SIMPLIFICATION_TOLERANCE, preserve_topology=True)
        
        # Round coordinates to 4 decimal places to save character space
        # shapely.mapping returns dict, we can't easily round inside without custom func
        # But simplify is the big win.
        f['geometry'] = mapping(simplified_s)
        simplified_features.append(f)
    except Exception as e:
        print(f"Error simplifying feature: {e}")
        simplified_features.append(f) # Keep original if simplify fails

final_data = {
    "type": "FeatureCollection",
    "features": simplified_features
}

with open('data/world_borders_compliant.json', 'w') as f:
    json.dump(final_data, f)
    
print("Saved merged map to data/world_borders_compliant.json")
