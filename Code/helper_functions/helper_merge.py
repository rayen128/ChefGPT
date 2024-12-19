"""
This file contains two functions for processing and analyzing text data:

1. `find_frequent_words`:
   - Takes a pandas Series containing text data and returns the most frequent words along with their counts.
   - Useful for identifying common terms in a dataset.

2. `clean_name`:
   - Takes a string and a list of words (stopwords) to remove, and returns the cleaned string.
   - Useful for cleaning text data by removing irrelevant words like common stopwords.

Both functions can be used in text analysis tasks, data cleaning, or feature engineering processes.
"""

from typing import List, Tuple
import pandas as pd
import string
from collections import Counter
import re


def find_frequent_words(column: pd.Series, top_n: int = 10) -> List[Tuple[str, int]]:
    """
    Finds the most frequent words in a pandas Series.

    Args:
        column (pd.Series): Column containing text data.
        top_n (int): Number of top words to return. Default is 10.

    Returns:
        List[Tuple[str, int]]: List of tuples with words and their frequencies.
    """

    word_counter = Counter(
        word.lower()
        for name in column
        for word in re.findall(r'\b\w+\b', name)
    )
    return word_counter.most_common(top_n)


def clean_name(name: str, removal_words: List[str]) -> str:
    """
    Removes specified (stop)words from a string.

    Args:
        name (str): The input string to be cleaned.
        stop_words (List[str]): A list of words to remove from the string.

    Returns:
        str: The cleaned string with stopwords removed.
    """
    # Create a regex pattern to match any stopword as a whole word
    # With help of ChatGPT
    pattern = r'\b(?:' + '|'.join(map(re.escape, removal_words)) + r')\b'

    # Replace stopwords with an empty string and strip whitespace
    return re.sub(pattern, '', name, flags=re.IGNORECASE).strip()


def write_common_words_to_csv(df, name='common_words.csv', n=1000):
    # Find the top most common (stop)words
    common_words = find_frequent_words(
        df['Engelse naam/Food name'], top_n=n)

    common_words_df = pd.DataFrame(common_words, columns=['Word', 'Frequency'])

    # Write the DataFrame to a CSV file
    common_words_df.to_csv('common_words.csv', index=False)


def clean_nutrition_df(nutrition_df: pd.DataFrame, flavour_df: pd.DataFrame, name_columns: List[str]) -> pd.DataFrame:
    """
    Cleans the nutrition DataFrame by standardizing text in specific columns and creating a cleaned version 
    of the 'Engelse naam/Food name' column.

    Parameters:
    ----------
    nutrition_df : pd.DataFrame
        A pandas DataFrame containing nutritional information, including a column named 
        'Engelse naam/Food name' which stores food names.

    Returns:
    -------
    pd.DataFrame
        A cleaned pandas DataFrame with the 'Engelse naam/Food name' column converted to lowercase and 
        a new 'cleaned_name' column with stopwords and punctuation removed.

    Notes:
    -----
    - The function modifies the `nutrition_df` DataFrame directly. If you want to avoid altering the original, 
      create a copy before passing it to the function.
    - Ensure the column 'Engelse naam/Food name' exists in the DataFrame before calling this function.
    - The `clean_name` helper function and `flavour_df` with `name_columns` must be defined elsewhere in the code.
    """

    # Convert specific columns to lowercase
    nutrition_df['Engelse naam/Food name'] = nutrition_df['Engelse naam/Food name'].str.lower()
    flavour_df[name_columns] = flavour_df[name_columns].apply(
        lambda col: col.str.lower()
    )

    # Use helper function to remove stopwords
    nutrition_df['cleaned_name'] = nutrition_df['Engelse naam/Food name'].apply(
        lambda x: clean_name(x, list(string.punctuation))
    )

    return nutrition_df
