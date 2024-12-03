import json
import requests

# Define the range of IDs
start_id = 1
end_id = 979

# Base URL
base_url = "https://cosylab.iiitd.edu.in/flavordb2/entities_json?id="

# Combined data
combined_data = []

# Fetch and combine data
for entity_id in range(start_id, end_id + 1):

    print(f"Getting ID= {entity_id}")

    url = f"{base_url}{entity_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()
        combined_data.append(data)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for ID {entity_id}: {e}")
    except json.JSONDecodeError:
        print(f"Error decoding JSON for ID {entity_id}")

# Write combined data to a file
output_file = "combined_flavor_db.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(combined_data, f, indent=4)

print(f"Data successfully combined into {output_file}")
