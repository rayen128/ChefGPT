# ChefGPT - References Overview

This document contains a comprehensive list of references, libraries, datasets, and resources used in the development of ChefGPT.

## Libraries and Tools

1. **[RapidFuzz - Fuzzy Search & Matching](https://github.com/rapidfuzz/RapidFuzz)**  
  Library used for fuzzy search and matching on multiple occasions throughout the project.

2. **[Levenshtein Distance (RapidFuzz)](https://medium.com/analytics-vidhya/fuzzy-matching-in-python-2def168dee4a)**  
  A blog article explaining the Levenshtein Distance, the algorithm used by RapidFuzz for fuzzy string matching.

3. **[TensorFlow](https://www.tensorflow.org/)**  
  Open-source machine learning framework used for building and training deep learning models in ChefGPT.

4. **[NumPy](https://numpy.org/)**  
  Essential library for numerical computing in Python, used for array manipulation and scientific computing tasks in the project.

5. **[Pandas](https://pandas.pydata.org/)**  
  Powerful data analysis and manipulation library used for handling structured data, such as the datasets used in ChefGPT.

## Datasets and APIs

6. **[FlavorDB](https://cosylab.iiitd.edu.in/flavordb2/#)**  
  Website from which we scraped flavour pairings for recipe generation.

7. **[USDA Food Database](https://fdc.nal.usda.gov/)**  
  A nutritional database used for referencing food nutritional values.

8. **[Recipe Box](https://github.com/rtlee9/recipe-box)**  
  Recipe dataset used as the basis for the training data in ChefGPT.

9. **[FoodBaseBERT-NER](https://huggingface.co/Dizex/FoodBaseBERT-NER)**  
  Pre-trained model used for extracting ingredients for the training data.

## Articles and Research

10. **[PubMed - Article 1 Regarding Nutrition](https://pubmed.ncbi.nlm.nih.gov/15107010/)**  
  Research article used for reference in the macro-nutrient splitting model.

11. **[Healthline - Article 2 Regarding Nutrition](https://www.healthline.com/nutrition/best-macronutrient-ratio?utm_source=chatgpt.com)**  
  Article used for insights into optimal macronutrient ratios for health and nutrition.

12. **[FlavourDB2 & Flavour Pairing Article](https://ift.onlinelibrary.wiley.com/doi/10.1111/1750-3841.17298?af=R)**
    Goel et al. (2024) describes what it means for ingredients to 'pair' and describes the database we used for this.

13. **[Article 1 - Reason Why Adam is good](https://www.quora.com/Why-is-the-Adam-optimization-algorithm-better-than-gradient-descent)**
    Post going over the positive things of the Adam-optimizer (compared to SGD).

14. **[Article 2 - Reason why Adam is good](https://www.kaggle.com/code/mukeshmanral/optimizers-fast-optimizers)**
    A Kaggle notebook going over multiple optimizers and explaining why Adam is the best.

15. **[Inspiration for Model Architecture](https://www.atmosera.com/blog/text-classification-with-neural-networks/)**
    This article is about the creation of a NN for text, it was used for inspiration.
