import math
import pandas as pd
import json
from collections import Counter
from itertools import combinations
import time

# Load datasets
combined_dataset_path = '/Users/adlemst/Desktop/BDS/DeepLiP/Project ChefGPT/Personal Folder/combined_flavour_nutrition.csv'
recipes_data_path = '/Users/adlemst/Desktop/BDS/DeepLiP/Project ChefGPT/Personal Folder/matched_recipe_data_with_limited_flavours.json'

combined_df = pd.read_csv(combined_dataset_path, low_memory=False)
with open(recipes_data_path, 'r') as file:
    recipes_data = json.load(file)

# Clean flavor data
def clean_flavours(flavour_string):
    if pd.isna(flavour_string):
        return set()
    return set(str(flavour_string).lower().split('@'))

combined_df['overlap_flavours_set'] = combined_df['overlap_flavours'].apply(clean_flavours)

# Nutrition columns
nutrition_columns = ['PROT (g)', 'FAT (g)', 'CHO (g)']
target_macros = {"protein": 30, "fat": 20, "carbohydrates": 50}

# Weights for loss components
W_FLAVOUR = 0.9  # Higher weight for flavor
W_NUTRITION = 0.1  # Lower weight for nutrition

# Precompute flavor pairing matrix
def calculate_flavor_pairing_matrix(recipes):
    flavor_counter = Counter()
    pairing_counter = Counter()
    for recipe in recipes:
        flavors = recipe['recipe_flavours']
        flavor_counter.update(flavors)
        pairing_counter.update(combinations(flavors, 2))
    # Convert counts to probabilities or scores
    return {
        pair: count / (flavor_counter[pair[0]] + flavor_counter[pair[1]] - count)
        for pair, count in pairing_counter.items() if count > 0
    }

pairing_matrix = calculate_flavor_pairing_matrix(recipes_data)

# Precompute flavor rarity
def calculate_flavor_rarity(recipes):
    flavor_counter = Counter(flavor for recipe in recipes for flavor in recipe['recipe_flavours'])
    return {flavor: 1 / (count + 1) for flavor, count in flavor_counter.items()}

flavor_rarity = calculate_flavor_rarity(recipes_data)

# Calculate ingredient flavor weight
def calculate_ingredient_weight(recipes, pairing_matrix):
    ingredient_flavor_weight = Counter()
    for recipe in recipes:
        flavors = recipe['recipe_flavours']
        for flavor in flavors:
            for ingredient in pairing_matrix:
                ingredient_flavor_weight[ingredient] += pairing_matrix.get((flavor, ingredient), 0)
    return ingredient_flavor_weight

ingredient_flavor_weight = calculate_ingredient_weight(recipes_data, pairing_matrix)

# Normalize scores
def normalize_scores(scores):
    min_score = min(scores)
    max_score = max(scores)
    return [(score - min_score) / (max_score - min_score) for score in scores]

# Flavor loss calculation with normalization and penalty
def calculate_flavor_loss_with_penalty(recipe_flavours, ingredient_flavours, pairing_matrix, ingredient_flavor_weight, flavor_rarity):
    if not recipe_flavours:
        return 1  # Maximum loss if no recipe flavors

    # Calculate overlap
    overlap = recipe_flavours & ingredient_flavours
    overlap_percentage = len(overlap) / len(recipe_flavours) if recipe_flavours else 0

    # Calculate pairing score
    pairing_score = sum(
        pairing_matrix.get((flavor, ing), 0) + pairing_matrix.get((ing, flavor), 0)
        for flavor in recipe_flavours for ing in ingredient_flavours
    )

    # Calculate rarity score
    rarity_score = sum(flavor_rarity.get(flavor, 0) for flavor in overlap)

    # Penalize common ingredients with high flavor weights
    penalty = sum(ingredient_flavor_weight.get(ing, 0) for ing in ingredient_flavours)

    # Combine scores with normalization
    total_score = overlap_percentage + pairing_score + rarity_score - penalty
    return max(1 - total_score, 0) 

# Nutrition loss calculation
def calculate_nutrition_loss(current_nutrition, ingredient_nutrition, target_macros):
    updated_nutrition = {
        key: current_nutrition.get(key, 0) + ingredient_nutrition.get(key, 0)
        for key in target_macros
    }
    total = sum(updated_nutrition.values())
    if total == 0:
        return float('inf')  
    deviation = sum(abs((updated_nutrition[key] / total * 100) - target_macros[key]) for key in target_macros)
    return deviation

for recipe in recipes_data:
    recipe_flavours = set(recipe['recipe_flavours'])
    matched_ingredients = recipe.get('matched_ingredients', [])
    current_nutrition = {"protein": 0, "fat": 0, "carbohydrates": 0}

    # Aggregate current nutrition
    for ing in matched_ingredients:
        if isinstance(ing, dict) and 'nutritional_info' in ing:
            current_nutrition["protein"] += ing['nutritional_info'].get("protein", 0)
            current_nutrition["fat"] += ing['nutritional_info'].get("fat", 0)
            current_nutrition["carbohydrates"] += ing['nutritional_info'].get("carbohydrates", 0)

    # Collect flavor and nutrition losses
    flavor_losses = []
    nutrition_losses = []

    for _, row in combined_df.iterrows():
        ingredient_name = row['clean_entity2']
        ingredient_flavours = row['overlap_flavours_set']

        # Skip already matched ingredients
        if ingredient_name in [ing['name'] if isinstance(ing, dict) else ing for ing in matched_ingredients]:
            continue

        # Calculate flavor loss
        flavor_loss = calculate_flavor_loss_with_penalty(
            recipe_flavours, ingredient_flavours, pairing_matrix, ingredient_flavor_weight, flavor_rarity
        )
        # Apply log transformation to flavor loss
        transformed_flavor_loss = math.log(max(flavor_loss, 1e-10) + 1)
        flavor_losses.append((ingredient_name, transformed_flavor_loss))

        # Extract nutritional info
        ingredient_nutrition = {
            "protein": float(str(row.get('PROT (g)', 0)).replace(',', '.')),
            "fat": float(str(row.get('FAT (g)', 0)).replace(',', '.')),
            "carbohydrates": float(str(row.get('CHO (g)', 0)).replace(',', '.'))
        }

        # Calculate nutrition loss
        nutrition_loss = calculate_nutrition_loss(current_nutrition, ingredient_nutrition, target_macros)
        # Apply log transformation to nutrition loss
        transformed_nutrition_loss = math.log(max(nutrition_loss, 1e-10) + 1)
        nutrition_losses.append((ingredient_name, transformed_nutrition_loss))

    # Find the best ingredient based on weighted total loss
    best_ingredient = None
    lowest_loss = float('inf')

    for (ingredient_name, transformed_flavor_loss), (_, transformed_nutrition_loss) in zip(flavor_losses, nutrition_losses):
        # Apply weights directly
        weighted_flavor_loss = W_FLAVOUR * transformed_flavor_loss
        weighted_nutrition_loss = W_NUTRITION * transformed_nutrition_loss
        total_loss = weighted_flavor_loss + weighted_nutrition_loss

        # Track the best ingredient
        if total_loss < lowest_loss:
            lowest_loss = total_loss
            best_ingredient = {
                "name": ingredient_name,
                "flavor_loss": round(weighted_flavor_loss, 10),
                "nutrition_loss": round(weighted_nutrition_loss, 10),
                "total_loss": round(total_loss, 10),
                "nutritional_info": {
                    "protein": ingredient_nutrition["protein"],
                    "fat": ingredient_nutrition["fat"],
                    "carbohydrates": ingredient_nutrition["carbohydrates"]
                }
            }

    # Add the best ingredient to the recipe
    recipe['best_target_ingredient'] = best_ingredient

# Save updated recipe data
output_path = '/Users/adlemst/Desktop/BDS/DeepLiP/Project ChefGPT/Personal Folder/updated_recipes_with_penalty.json'
with open(output_path, 'w') as json_file:
    json.dump(recipes_data, json_file, indent=4)

print(f"Updated recipe data with flavor penalties saved to {output_path}")
