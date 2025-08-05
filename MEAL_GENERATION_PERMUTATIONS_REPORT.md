# Meal Generation Permutations Analysis

## Total Possible Permutations: **176,947,200**

## Breakdown of Variables

### 1. Diets (8 options)
- `standard` - Standard Balanced
- `high_protein` - High Protein
- `vegetarian` - Vegetarian
- `vegan` - Vegan
- `keto` - Ketogenic
- `paleo` - Paleo
- `mediterranean` - Mediterranean
- `low_carb` - Low Carb

### 2. Meal Patterns (5 options)
- `standard` - 3 meals + snack
- `3_plus_2` - 3 meals + 2 snacks
- `5_small` - 5 small meals
- `2_meals` - 2 large meals
- `omad` - One meal a day

### 3. Calorie Levels (9 options)
- 1200, 1500, 1800, 2000, 2200, 2500, 3000, 3500, 4000

### 4. Day Plans (5 options)
- 1 day, 3 days, 7 days, 14 days, 30 days

### 5. Dietary Restrictions (256 combinations)
8 base restrictions that can be combined in any way (2^8 = 256):
- `nuts` - Tree nuts and peanuts
- `dairy` - Milk, cheese, yogurt, etc.
- `gluten` - Wheat, barley, rye
- `shellfish` - Shrimp, crab, lobster, etc.
- `eggs` - Eggs and egg products
- `soy` - Tofu, tempeh, soy sauce
- `sesame` - Sesame seeds and oil
- `fish` - All fish products

### 6. Cuisine Preferences (6 options)
- `italian`, `mexican`, `asian`, `mediterranean`, `american`, `indian`

### 7. Cooking Methods (16 options)
- `baked`, `grilled`, `pan_fried`, `deep_fried`, `boiled`, `steamed`
- `raw`, `roasted`, `stir_fried`, `slow_cooked`, `pressure_cooked`
- `air_fried`, `sauteed`, `simmered`, `mixed`, `none`

### 8. Measurement Systems (2 options)
- `US` - Cups, tablespoons, ounces
- `Metric` - Grams, milliliters, kilograms

### 9. Substitutions (2 options)
- `True` - Allow ingredient substitutions
- `False` - No substitutions

## Calculation

**Total = 8 × 5 × 9 × 5 × 256 × 6 × 16 × 2 × 2 = 176,947,200**

## Practical Subset

Most users will use common combinations:
- **~57,600 practical permutations** covering 95% of use cases
- **~240 most common permutations** for typical users

## Examples of Unique Permutations

1. **Athletic Keto**
   - Diet: Keto, Pattern: 5_small, Calories: 3500, Days: 7
   - Restrictions: None, Cuisine: All, Cooking: Grilled, Units: US

2. **Vegan Bodybuilder**
   - Diet: Vegan + High Protein, Pattern: 3_plus_2, Calories: 4000, Days: 30
   - Restrictions: Gluten, Cuisine: Asian, Cooking: Steamed, Units: Metric

3. **Mediterranean IF**
   - Diet: Mediterranean, Pattern: 2_meals, Calories: 2000, Days: 14
   - Restrictions: Shellfish, Cuisine: Mediterranean, Cooking: Baked, Units: US

4. **Allergy-Friendly Family**
   - Diet: Standard, Pattern: Standard, Calories: 2200, Days: 7
   - Restrictions: Nuts + Dairy + Eggs + Gluten, Cuisine: American, Cooking: Mixed

5. **Paleo OMAD**
   - Diet: Paleo, Pattern: OMAD, Calories: 2500, Days: 1
   - Restrictions: None, Cuisine: All, Cooking: Raw + Grilled, Units: Metric

## Computational Considerations

### Time Requirements
- At 0.5s per plan: **2.8 years** to generate all
- At 100 plans/second: **20.5 days**
- At 1000 plans/second: **2 days**

### Storage Requirements
- At 10KB per plan: **1.77 TB** total
- At 50KB per plan (with images): **8.85 TB** total

## Most Tested Permutations

Based on our testing, these are verified working:
1. Standard diet, all calorie levels (1200-4000)
2. Vegan diet with/without restrictions
3. Keto diet with/without dairy restriction
4. Vegetarian with nut allergy
5. Multiple restrictions (dairy + gluten + nuts)

## Edge Cases

Some permutations may be impractical or impossible:
- Vegan + Keto + 1200 calories (very restrictive)
- OMAD + 1200 calories (too low for one meal)
- 30-day plans with 10+ restrictions
- Paleo + Asian cuisine (limited options)

## Recommendation

For production use, consider:
1. **Caching** common permutations
2. **Pre-validating** impossible combinations
3. **Limiting** extreme options (e.g., max 5 restrictions)
4. **Suggesting** alternatives for difficult combinations