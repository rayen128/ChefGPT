import pandas as pd
import re
import json
from tqdm import tqdm
from rapidfuzz import process, fuzz
import numpy as np

# Load the combined dataset
combined_dataset_path = '/Users/adlemst/Desktop/BDS/DeepLiP/Project ChefGPT/Personal Folder/combined_flavour_nutrition.csv'
combined_df = pd.read_csv(combined_dataset_path, low_memory=False)  

# Debugging: Verify combined dataset columns
print("Columns in Combined Dataset:", combined_df.columns)

# Load the recipes dataset
recipe_path = '/Users/adlemst/Desktop/BDS/DeepLiP/Project ChefGPT/Personal Folder/recipes_raw/recipes_raw_nosource_fn.json'
with open(recipe_path, 'r') as file:
    recipes = json.load(file)

# Function to clean text
def clean_text(text):
    """Clean text by removing special characters and converting to lowercase."""
    return re.sub(r'[^a-zA-Z0-9\s]', '', str(text).lower().strip())

# Function to tokenize ingredients
def tokenize_ingredients(ingredients):
    """Tokenize and clean a list of ingredient strings."""
    tokens = []
    for ingredient in ingredients:
        cleaned = clean_text(ingredient)
        tokens.extend(cleaned.split())  
    return tokens

# Function to aggregate and find the top 20 overlap flavours
def aggregate_top_flavours(group):
    """Aggregate and find the top 20 most common overlap flavours for a group of rows."""
    all_flavours = []
    for overlap in group['overlap_flavours']:
        if pd.notna(overlap) and isinstance(overlap, str):
            all_flavours.extend(overlap.split('@'))
    flavour_counts = pd.Series(all_flavours).value_counts()
    return flavour_counts.index[:50].tolist()  # Return top 20 flavours

# Pre-aggregate overlap_flavours by clean_entity2
aggregated_flavours = combined_df.groupby('clean_entity2', group_keys=False).apply(aggregate_top_flavours).reset_index()
aggregated_flavours.columns = ['clean_entity2', 'aggregated_overlap_flavours']

# Merge the aggregated flavours back into the combined dataset
combined_df = pd.merge(combined_df, aggregated_flavours, on='clean_entity2', how='left')

# Limit the number of recipes to process based on a percentage
def get_sampled_recipes(recipes, percentage):
    """Get a sampled subset of the recipes based on a percentage."""
    num_recipes_to_process = max(1, int(percentage * len(recipes)))
    return {k: recipes[k] for k in list(recipes.keys())[:num_recipes_to_process]}

percentage_to_process = 0.0001  # Adjust this percentage as needed
sampled_recipes = get_sampled_recipes(recipes, percentage_to_process)

# Debugging: Print number of sampled recipes
print(f"Number of Sampled Recipes: {len(sampled_recipes)}")

# Process recipes
print("Processing recipes...")
recipe_data_list = []

# Columns to include in the nutritional information
nutrition_columns = ['ID', 'clean_entity2', 'PROT (g)', 'FAT (g)', 'CHO (g)']

for recipe_id, recipe_data in tqdm(sampled_recipes.items(), desc="Recipes"):
    recipe_name = recipe_data.get('title', recipe_id)
    ingredients = recipe_data.get('ingredients', [])
    tokenized_ingredients = tokenize_ingredients(ingredients)

    # Match ingredients to `clean_entity2` in the combined dataset
    matched_ingredients = []
    matched_ids = []
    nutritional_info = []
    recipe_flavours = []  # Aggregate all flavours for the recipe

    for token in tokenized_ingredients:
        match, score, _ = process.extractOne(token, combined_df['clean_entity2'], scorer=fuzz.ratio)
        if score >= 85:  # Threshold for a good match
            matched_ingredients.append(match)
            matched_row = combined_df[combined_df['clean_entity2'] == match].iloc[0]
            matched_ids.append(int(matched_row['ID']))  # Ensure ID is converted to Python int

            # Use the pre-aggregated overlap_flavours
            tokenized_flavours = matched_row['aggregated_overlap_flavours']

            # Add all overlap flavours to the recipe's flavour list
            if tokenized_flavours:  # Ensure it is not empty
                recipe_flavours.extend(tokenized_flavours)

            # Include selected nutritional values
            nutrition_data = matched_row[nutrition_columns].to_dict()
            nutritional_info.append({
                'ingredient': match,
                'ID': int(matched_row['ID']),  # Convert ID to int
                'nutrition': nutrition_data
            })

    # **Addition: Include recipe-level explicit flavours (if present)**
    explicit_recipe_flavours = recipe_data.get('flavours', [])
    recipe_flavours.extend(explicit_recipe_flavours)  # Add recipe-level flavours

    # Deduplicate matches and flavours
    matched_ingredients = list(set(matched_ingredients))
    matched_ids = list(set(matched_ids))
    recipe_flavours = list(set(recipe_flavours))  # Remove duplicates from the flavour list

    # Append data for each recipe
    recipe_data_list.append({
        'recipe_id': recipe_id,
        'recipe_name': recipe_name,
        'ingredients': ingredients,
        'matched_ingredients': matched_ingredients,
        'matched_ids': matched_ids,
        'nutritional_info': nutritional_info,
        'recipe_flavours': recipe_flavours  # Include the aggregated and explicit flavours in the output
    })

    # Debugging: Print processed recipe data
    print(f"Processed Data for Recipe {recipe_id}: {recipe_data_list[-1]}")

# Ensure all data is JSON-serializable
def make_json_serializable(data):
    """Convert data types to JSON-serializable formats."""
    if isinstance(data, (pd.DataFrame, pd.Series)):
        return data.to_dict()
    if isinstance(data, np.integer):
        return int(data)
    if isinstance(data, np.floating):
        return float(data)
    if isinstance(data, np.ndarray):
        return data.tolist()
    return data

recipe_data_list_serializable = json.loads(json.dumps(recipe_data_list, default=make_json_serializable))

# Save to JSON
output_path = '/Users/adlemst/Desktop/BDS/DeepLiP/Project ChefGPT/Personal Folder/matched_recipe_data_with_limited_flavours.json'
with open(output_path, 'w') as json_file:
    json.dump(recipe_data_list_serializable, json_file, indent=4)
print(f"Matched recipe data saved to {output_path}")
