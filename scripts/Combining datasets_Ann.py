import pandas as pd
import re

# Load the datasets
flavour_DB_path = 'chefgpt/resources/flavourDB2_molecules.csv'
nevo_path = 'chefgpt/resources/NEVO_Joined_cleaned.csv'

flavour_df = pd.read_csv(flavour_DB_path)
# Changed to use the cleaned NEVO dataset
nevo_df = pd.read_csv(nevo_path, sep=';')

# Clean columns for matching
flavour_df['clean_ingredient'] = flavour_df['ingredient'].apply(
    lambda x: re.sub(r'[^a-zA-Z0-9\s]', '', str(x).lower().strip()))
nevo_df['clean_flavour_name'] = nevo_df['flavour_name'].apply(
    lambda x: re.sub(r'[^a-zA-Z0-9\s]', '', str(x).lower().strip()))

# Rename 'flavour_index' to 'ID' and convert to string
nevo_df.rename(columns={'flavour_index': 'ID'}, inplace=True)
nevo_df['ID'] = nevo_df['ID'].dropna().astype(int).astype(str)

# Retain all columns and aggregate numeric values by 'clean_flavour_name' and 'ID'
non_numeric_columns = nevo_df.select_dtypes(exclude='number').columns
numeric_columns = nevo_df.select_dtypes(include='number').columns

# Aggregate numeric columns while keeping the first occurrence of non-numeric columns
nevo_df_grouped = (
    nevo_df.groupby(['clean_flavour_name', 'ID'], as_index=False)
    .agg({**{col: 'first' for col in non_numeric_columns}, **{col: 'mean' for col in numeric_columns}})
)

# Debugging: Check grouped NEVO data
print("Grouped NEVO DataFrame Sample:")
print(nevo_df_grouped.head())

# Merge the datasets
combined_df = pd.merge(
    flavour_df,
    nevo_df_grouped,
    how='inner',  # Use 'inner' to keep only rows with matches
    left_on='clean_ingredient',
    right_on='clean_flavour_name'
)

# Debugging: Verify merged dataset
print("Columns in Combined DataFrame:", combined_df.columns)

# Check for 'ID' column
if 'ID' not in combined_df.columns:
    print("Warning: 'ID' column not found in combined DataFrame. Verify column renaming and merging logic.")
else:
    print("Sample of Combined Dataset:")
    print(combined_df[['ingredient', 'clean_ingredient',
          'clean_flavour_name', 'ID']].head())

# restructure to put 'molecules' column at the end
molecules_column = combined_df.pop('molecule_list')
combined_df['molecule_list'] = molecules_column

# For debugging, the ingredients that are matched:
# nevo Food name and nevo flavour_name to df, but only

nevo_df_names = nevo_df[['Engelse naam/Food name', 'flavour_name']]
nevo_df_names.to_csv('chefgpt/resources/nevo_names.csv', index=False)

# Save the combined dataset to a CSV
output_path = 'chefgpt/resources/combined_flavour_nutrition.csv'
combined_df.to_csv(output_path, index=False)
print(f"Combined dataset saved to {output_path}")
