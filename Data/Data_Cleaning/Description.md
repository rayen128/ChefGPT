# Common and Noise Words

This folder contains two datasets, both derived from the `cleaned_name` column of the [NEVO Dataset](/DLiP-ChefGPT/data/Nutrition/). These datasets were used to analyze and improve the data matching process between the nutrition and flavor datasets.

## Common Words

The `common_words.csv` file lists the most frequently occurring words within the entire dataset. These words were extracted to identify recurring terms that could potentially clutter the `cleaned_name` column, which plays a critical role in the matching process.

## Noise Words

The `noise_words.csv` file is a subset of the `common_words.csv` dataset. It includes all the words that were removed from the NEVO Dataset to enhance the accuracy of the matching process. Additionally, the `added_matches` column in this file indicates the number of rows successfully matched after removing each word.
