import pandas as pd
import re

# Load the datasets
flavour_pairings_path = '/Users/adlemst/Desktop/BDS/DeepLiP/Project ChefGPT/Personal Folder/flavour_pairings_names.csv'
nevo_path = '/Users/adlemst/Desktop/BDS/DeepLiP/Project ChefGPT/Personal Folder/NEVO_Joined.csv'

flavour_df = pd.read_csv(flavour_pairings_path)
nevo_df = pd.read_csv(nevo_path)

# Clean columns for matching
flavour_df['clean_entity2'] = flavour_df['entity2'].apply(lambda x: re.sub(r'[^a-zA-Z0-9\s]', '', str(x).lower().strip()))
nevo_df['clean_flavour_name'] = nevo_df['flavour_name'].apply(lambda x: re.sub(r'[^a-zA-Z0-9\s]', '', str(x).lower().strip()))

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
    left_on='clean_entity2',
    right_on='clean_flavour_name'
)

# Remove the 'entity1' column
if 'entity1' in combined_df.columns:
    combined_df.drop(columns=['entity1'], inplace=True)

# Debugging: Verify merged dataset
print("Columns in Combined DataFrame:", combined_df.columns)

# Check for 'ID' column
if 'ID' not in combined_df.columns:
    print("Warning: 'ID' column not found in combined DataFrame. Verify column renaming and merging logic.")
else:
    print("Sample of Combined Dataset:")
    print(combined_df[['entity2', 'clean_entity2', 'clean_flavour_name', 'ID']].head())

# Save the combined dataset to a CSV
output_path = '/Users/adlemst/Desktop/BDS/DeepLiP/Project ChefGPT/Personal Folder/combined_flavour_nutrition.csv'
combined_df.to_csv(output_path, index=False)
print(f"Combined dataset saved to {output_path}")
