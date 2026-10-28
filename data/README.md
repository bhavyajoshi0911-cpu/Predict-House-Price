# King County House Sales Dataset (kc_house_data.csv)

## Overview
This directory contains the housing dataset used by **HomeValue AI**. The default benchmark dataset is the **King County House Sales Dataset** (Seattle and King County, Washington, USA), which contains real recorded home sales between May 2014 and May 2015.

## Schema & Feature Definitions

| Column Name | Data Type | Description | Unit / Range |
|-------------|-----------|-------------|--------------|
| `id` | String / Int | Unique identifier for each property sale transaction | System ID |
| `date` | String | Date the property was sold | YYYYMMDDT000000 |
| `price` | Float (Target) | Sale transaction price of the home | USD ($) |
| `bedrooms` | Integer | Total count of bedrooms in the property | 1 – 11 |
| `bathrooms` | Float | Number of bathrooms (where 0.5 = toilet/sink, 0.75 = shower, 1.0 = full bath) | 0.5 – 8.0 |
| `sqft_living` | Integer | Interior living space square footage | 290 – 13,540 sq ft |
| `sqft_lot` | Integer | Total parcel/land lot size square footage | 520 – 1,651,359 sq ft |
| `floors` | Float | Number of living floors / levels in the structure | 1.0 – 3.5 |
| `waterfront` | Binary (0/1) | Whether the property has a direct waterfront view / access | 0 = No, 1 = Yes |
| `view` | Integer | Evaluation score of the quality of the view | 0 (None) – 4 (Spectacular) |
| `condition` | Integer | Overall structural maintenance condition | 1 (Poor) – 5 (Excellent) |
| `grade` | Integer | Construction quality rating based on King County assessment system | 1 (Cabin/low) – 13 (Mansion/custom) |
| `sqft_above` | Integer | Living space above ground level | sq ft |
| `sqft_basement`| Integer | Living/storage space below ground level (0 if none) | sq ft |
| `yr_built` | Integer | Year the residential home was originally constructed | 1900 – 2015 |
| `yr_renovated`| Integer | Year the property was last remodeled (0 if never remodeled) | 0, 1934 – 2015 |
| `zipcode` | String / Int | 5-digit US Postal ZIP code in King County (e.g., 98178, 98004) | 70 King County ZIP codes |
| `lat` | Float | Latitude geographic coordinate | ~47.15 to 47.77 |
| `long` | Float | Longitude geographic coordinate | ~-122.5 to -121.31 |
| `sqft_living15`| Integer | Average interior living area of the 15 nearest neighbors in 2015 | sq ft |
| `sqft_lot15` | Integer | Average lot size of the 15 nearest neighbors in 2015 | sq ft |

## Real Market Data Integrity
- The initial baseline included in this repository contains real sales records from the official King County open data registry.
- To download or refresh the complete 21,613-row historical records from OpenML or GitHub, run:
  ```bash
  python ml/download_dataset.py
  ```
- Alternatively, you can upload any custom compatible CSV dataset using the **Dataset Explorer** tab in the HomeValue AI web dashboard.
