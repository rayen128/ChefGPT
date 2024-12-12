'''
After generating/picking a list of stop words to remove (saved in stop_words.csv),
this scripts creates a csv file called "NEVO_Joined",  
linking the nutrition to the NEVO dataset. 
'''

import pandas as pd
import json
from rapidfuzz import process, fuzz  # type: ignore
from helper_functions.helper_merge import find_frequent_words, clean_name, write_common_words_to_csv, clean_nutrition_df
import numpy as np
import string


nutrition_file = 'NEVO2023_8.0.csv'
flavour_json = 'flavourDB2.json'

# Load nutrition dataset
nutrition_df = pd.read_csv(nutrition_file, sep='|')

# Remove unnecessary columns
columns_to_remove = [
    'NEVO-versie/NEVO-version',             # NEVO versie
    'Voedingsmiddelgroep',                  # In het Nederlands
    'Voedingsmiddelnaam/Dutch food name',   # In het Nederlands
    'Synoniem'                              # In het Nederlands
]

nutrition_df.drop(columns_to_remove, inplace=True, axis=1)

# Convert flavour data from JSON -> Panda
with open(flavour_json) as file:
    flavour_data = json.load(file)

# Save only relevant info
flavour_df = pd.DataFrame(flavour_data,
                          columns=['category',
                                   'entity_id',
                                   'category_readable',
                                   'entity_alias_basket',
                                   'entity_alias_readable',
                                   'natural_source_name',
                                   'entity_alias', 'entity_alias_synonyms'
                                   ])

# flavourdf has multiple name columns
name_columns = [
    'entity_alias_basket',
    'entity_alias_readable',
    'entity_alias',
    'entity_alias_synonyms'
]


### Data Cleaning ###

# Create 'cleaned_name' column
clean_nutrition_df(nutrition_df, flavour_df, name_columns)

stop_words = pd.read_csv('stop_words.csv')['stop_word']
stop_words = stop_words[:40]


# Use helper function to remove stopwords
nutrition_df['cleaned_name'] = nutrition_df['Engelse naam/Food name'].apply(
    lambda x: clean_name(x, stop_words))


### Fuzzy search ###

# Create a list to store the top matches
top_matches = []

# Iterate through each cleaned_name in nutrition_df
for idx, cleaned_name in enumerate(nutrition_df['cleaned_name']):

    # Loop over all flavour_df columns
    for name_column in name_columns:
        # Get the top_n matches from flavour_df[name_column]
        matches = process.extract(
            cleaned_name,
            flavour_df[name_column].tolist(),
            limit=3,
            scorer=fuzz.ratio
        )
        # Add the results to the list (including indexes from flavour_df)
        for match, score, match_index in matches:
            top_matches.append({
                'nutrition_index': idx,
                'nutrition_name': cleaned_name,
                'flavour_index': match_index,
                'flavour_name': match,
                'fuzz_score': score,
                'name_column': name_column
            })

# Convert the results to a DataFrame for further analysis
top_matches_df = pd.DataFrame(top_matches)

# Transform the `top_matches_df` into a wide format

# Sort matches by nutrition_index and fuzz_score (descending)
top_matches_df = top_matches_df.sort_values(
    by=['nutrition_index', 'fuzz_score'], ascending=[True, False]
)

# Keep only the top 3 matches per nutrition_index
top_matches_df = top_matches_df.groupby('nutrition_index').head(3)

# Pivot the DataFrame to make it wide - With help of ChatGPT
top_matches_wide_df = top_matches_df.assign(rank=top_matches_df.groupby('nutrition_index').cumcount() + 1) \
    .pivot(index='nutrition_index', columns='rank') \
    .reset_index()

# Flatten the MultiIndex columns - With help of ChatGPT
top_matches_wide_df.columns = ['_'.join(map(str, col)).strip('_')
                               for col in top_matches_wide_df.columns]

### Fuzzy Matching ###

# Create a copy
top_matches_wide_df_copy = top_matches_wide_df.copy()

# Condition 1: Perfect matches (at least 1 fuzzy-score is 100)
perfect_scores_df = top_matches_wide_df[
    (top_matches_wide_df['fuzz_score_1'] == 100) |
    (top_matches_wide_df['fuzz_score_2'] == 100) |
    (top_matches_wide_df['fuzz_score_3'] == 100)
].copy()  # Copy to avoid warning

# Determine which flavour_index corresponds to the perfect score
perfect_scores_df.loc[:, 'flavour_index'] = np.select(
    condlist=[
        perfect_scores_df['fuzz_score_1'] == 100,
        perfect_scores_df['fuzz_score_2'] == 100,
        perfect_scores_df['fuzz_score_3'] == 100
    ],
    choicelist=[
        perfect_scores_df['flavour_index_1'],
        perfect_scores_df['flavour_index_2'],
        perfect_scores_df['flavour_index_3']
    ],
    default=None  # No perfect match found
)

# Create the DataFrame with nutrition_index and corresponding flavour_index (we'll use this for the next condition)
result_df = perfect_scores_df[['nutrition_index', 'flavour_index']]

# Remove the rows from the original df
top_matches_wide_df = top_matches_wide_df[~top_matches_wide_df['nutrition_index'].isin(
    perfect_scores_df['nutrition_index'])]

# Condition 2: Clear match (= top 3 matches from same flavour-row & fuzz_scores are not 0)
same_flavour_row_df = top_matches_wide_df[
    (top_matches_wide_df['flavour_index_1'] == top_matches_wide_df['flavour_index_2']) &
    (top_matches_wide_df['flavour_index_2'] == top_matches_wide_df['flavour_index_3']) &
    (top_matches_wide_df['fuzz_score_1'] > 80) &
    (top_matches_wide_df['fuzz_score_2'] > 80) &
    (top_matches_wide_df['fuzz_score_3'] > 80)
].copy()

same_flavour_row_extracted = same_flavour_row_df[[
    'nutrition_index', 'flavour_index_1']]

# Rename flavour_index
same_flavour_row_extracted = same_flavour_row_extracted.rename(
    columns={'flavour_index_1': 'flavour_index'})

# Add to results
result_df = pd.concat(
    [result_df, same_flavour_row_extracted])

top_matches_wide_df = top_matches_wide_df[~top_matches_wide_df['nutrition_index'].isin(
    same_flavour_row_extracted['nutrition_index'])]

## Condition 3: Any fuzz_score is greater than a certain threshold ##
threshold = 90

fuzz_score_filtered_df = top_matches_wide_df[
    (top_matches_wide_df['fuzz_score_1'] > threshold) |
    (top_matches_wide_df['fuzz_score_2'] > threshold) |
    (top_matches_wide_df['fuzz_score_3'] > threshold)
].copy()

fuzz_score_filtered_df.loc[:, 'flavour_index'] = np.select(
    condlist=[
        fuzz_score_filtered_df['fuzz_score_1'] > threshold,
        fuzz_score_filtered_df['fuzz_score_2'] > threshold,
        fuzz_score_filtered_df['fuzz_score_3'] > threshold
    ],
    choicelist=[
        fuzz_score_filtered_df['flavour_index_1'],
        fuzz_score_filtered_df['flavour_index_2'],
        fuzz_score_filtered_df['flavour_index_3']
    ],
    default=None  # No fuzz-score above threshold
)

fuzz_score_extracted = fuzz_score_filtered_df[[
    'nutrition_index', 'flavour_index']]

result_df = pd.concat([result_df, fuzz_score_extracted], ignore_index=True)


# Merge nutrition_df with result_df on 'NEVO-code' and 'nutrition_index'
nutrition_df = nutrition_df.merge(result_df[['nutrition_index', 'flavour_index']],
                                  left_on='NEVO-code',
                                  right_on='nutrition_index',
                                  how='left')


# Also save the corresponding 'entity_name' from the flavour_df
nutrition_df = nutrition_df.merge(flavour_df[['entity_id', 'entity_alias_readable']],
                                  left_on='flavour_index',
                                  right_on='entity_id',
                                  how='left') \
    .rename(columns={'entity_alias_readable': 'flavour_name'})

# Drop the extra 'entity_id' column
nutrition_df.drop(columns=['entity_id'], inplace=True)


print(f"Amount of matches: {result_df.shape[0]}")

# Check the updated nutrition_df
print(nutrition_df.head())


nutrition_df.to_csv("NEVO_Joined.csv", index=False)
