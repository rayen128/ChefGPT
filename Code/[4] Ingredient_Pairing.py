import math
import pandas as pd
import json
import numpy as np
from tqdm import tqdm #suggested by chat-gpt to get an indication of running time

# Load datasets
combined_dataset_path = 'chefgpt/resources/combined_flavour_nutrition.csv'
recipes_data_path = 'chefgpt/resources/matched_recipe_data_with_common_molecules.json'

combined_df = pd.read_csv(combined_dataset_path, low_memory=False) 
with open(recipes_data_path, 'r') as file:
    recipes_data = json.load(file)

# Created a function to get molecule list and applied it for a molecule df
def get_molecule_list(molecule_string):
    return set(molecule.strip() for molecule in molecule_string.split(','))


combined_df['molecule_set'] = combined_df['molecule_list'].apply(
    get_molecule_list)

# Nutrition columns and target macro nutrients, as well as a max deivaition score from the our target nutrient ratio
nutrition_columns = ['PROT (g)', 'FAT (g)', 'CHO (g)']
target_macros = {"protein": 30, "fat": 20, "carbohydrates": 50}
max_deviation = sum(target_macros.values())

# Weights for scoring components
W_MOLECULE = 0.5  # Weight for molecule overlap (This is useed for the calculation of the true target based on flavour and nutritional values)
W_NUTRITION = 0.5  # Weight for nutrition (This is useed for the calculation of the true target based on flavour and nutritional values)

# Function to calculate overlap between two sets of molecules of ingredients 
def calculate_molecule_overlap(molecules1, molecules2):
    overlap = molecules1.intersection(molecules2)
    return len(overlap) / len(molecules1.union(molecules2))

# Function to calculate average molecule overlap score for each ingredient and recipe ingredients -  with help 
def calculate_average_molecule_overlap(recipe_ingredients, new_ingredient_molecules, combined_df):
    overlaps = []
    for ing in recipe_ingredients:
        ing_name = ing['ingredient']
        ing_molecules = set(
            combined_df[combined_df['clean_ingredient'] == ing_name]['molecule_set'].iloc[0])
        overlap = calculate_molecule_overlap(
            ing_molecules, new_ingredient_molecules)
        overlaps.append(overlap)
    return np.mean(overlaps) if overlaps else 0

# Function to calculate molecule overlap loss
def calculate_molecule_overlap_loss(overlap_score):
    return 1 - overlap_score 


# Normalizd (nutrition) loss calculation
def calculate_normalized_nutrition_loss(current_nutrition, ingredient_nutrition, target_macros):
    updated_nutrition = {
        key: current_nutrition.get(key, 0) + ingredient_nutrition.get(key, 0)
        for key in target_macros
    }
    total = sum(updated_nutrition.values())
    if total == 0:
        return float('inf')
    deviation = sum(abs((updated_nutrition[key] / total * 100) - target_macros[key]) for key in target_macros)
    normalized_loss = deviation / max_deviation
    return normalized_loss


for recipe in tqdm(recipes_data, desc="Processing recipes"): #tqdm used due to long running time, in order to get an indication of how long this process would take - error handling aided by ChatGPT
    matched_ingredients = recipe.get('matched_ingredients', [])
    current_nutrition = {"protein": 0, "fat": 0, "carbohydrates": 0}
    for ing in matched_ingredients:
        if isinstance(ing, dict) and 'nutrition' in ing:
            current_nutrition["protein"] += float(
                ing['nutrition'].get("PROT (g)", "0"))
            current_nutrition["fat"] += float(
                ing['nutrition'].get("FAT (g)", "0"))
            current_nutrition["carbohydrates"] += float(
                ing['nutrition'].get("CHO (g)", "0"))

    best_ingredient = None
    lowest_total_loss = float('inf')
    for _, row in combined_df.iterrows():
        ingredient_name = row['clean_ingredient']
        ingredient_molecules = row['molecule_set']
        if ingredient_name in [ing['ingredient'] for ing in matched_ingredients]: # skipped already matched ingredients to reduce computation but also redundancy
            continue

        # Calculate average molecule overlap using function we made earlier
        molecule_overlap = calculate_average_molecule_overlap(
            matched_ingredients, ingredient_molecules, combined_df)

        # Consequentially calculate molecule overlap loss 
        molecule_loss = calculate_molecule_overlap_loss(molecule_overlap)

        # Calculate nutrition loss for each ingredient
        ingredient_nutrition = {
            "protein": float(str(row['PROT (g)']).replace(',', '.')),
            "fat": float(str(row['FAT (g)']).replace(',', '.')),
            "carbohydrates": float(str(row['CHO (g)']).replace(',', '.'))
        }
        nutrition_loss = calculate_normalized_nutrition_loss(
            current_nutrition, ingredient_nutrition, target_macros)

        # Apply a log transformation to both losses
        log_molecule_loss = math.log(max(molecule_loss, 1e-10) + 1)
        log_nutrition_loss = math.log(max(nutrition_loss, 1e-10) + 1)

        # Calculate total weighted loss using the logged losses
        total_loss = W_MOLECULE * log_molecule_loss + W_NUTRITION * log_nutrition_loss

        # Track the best ingredient through lowest total loss for each recipes' ingredients
        if total_loss < lowest_total_loss:
            lowest_total_loss = total_loss
            best_ingredient = {
                "name": ingredient_name,
                "ID": row['ID'],
                "molecule_loss": round(log_molecule_loss, 10),
                "nutrition_loss": round(log_nutrition_loss, 10),
                "total_loss": round(total_loss, 10),
                "nutritional_info": ingredient_nutrition,
                "molecules": list(ingredient_molecules)
            }

    # Add a best matching ingredient to the list of the recipe ingredients
    recipe['best_target_ingredient'] = best_ingredient

# Make a new json file containing lists (of lists) with the recipe data, as well as the new best matched ingredient and its loss
output_path = 'chefgpt/resources/updated_recipes_with_losses-huge.json'
with open(output_path, 'w') as json_file:
    json.dump(recipes_data, json_file, indent=4) #explanation on this was asked in chat-gpt
