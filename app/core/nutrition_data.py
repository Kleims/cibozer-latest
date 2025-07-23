"""Nutrition data and meal database."""

# Nutrition targets by diet type
NUTRITION_TARGETS = {
    'standard': {
        'protein': 0.25,  # 25% of calories
        'carbs': 0.45,    # 45% of calories
        'fat': 0.30       # 30% of calories
    },
    'keto': {
        'protein': 0.20,
        'carbs': 0.05,
        'fat': 0.75
    },
    'paleo': {
        'protein': 0.30,
        'carbs': 0.30,
        'fat': 0.40
    },
    'vegan': {
        'protein': 0.15,
        'carbs': 0.55,
        'fat': 0.30
    },
    'high-protein': {
        'protein': 0.40,
        'carbs': 0.35,
        'fat': 0.25
    }
}

# Sample meal database (in production, this would be a proper database)
MEAL_DATABASE = [
    # Breakfast meals
    {
        'name': 'Scrambled Eggs with Avocado Toast',
        'meal_types': ['breakfast'],
        'calories': 450,
        'macros': {'protein': 20, 'carbs': 35, 'fat': 25},
        'diet_types': ['standard', 'vegetarian'],
        'cuisine': 'american',
        'contains': ['eggs', 'gluten', 'dairy'],
        'ingredients': ['2 eggs', '1 slice whole grain bread', '1/2 avocado', '1 tbsp butter'],
        'prep_time': 10,
        'cook_time': 10
    },
    {
        'name': 'Greek Yogurt Parfait',
        'meal_types': ['breakfast', 'snack'],
        'calories': 350,
        'macros': {'protein': 20, 'carbs': 45, 'fat': 10},
        'diet_types': ['standard', 'vegetarian'],
        'cuisine': 'mediterranean',
        'contains': ['dairy'],
        'ingredients': ['1 cup Greek yogurt', '1/2 cup berries', '1/4 cup granola', '1 tbsp honey'],
        'prep_time': 5,
        'cook_time': 0
    },
    {
        'name': 'Keto Bacon and Eggs',
        'meal_types': ['breakfast'],
        'calories': 500,
        'macros': {'protein': 30, 'carbs': 5, 'fat': 40},
        'diet_types': ['keto', 'low-carb'],
        'cuisine': 'american',
        'contains': ['eggs', 'pork'],
        'ingredients': ['3 eggs', '4 strips bacon', '1 tbsp butter', 'Salt and pepper'],
        'prep_time': 5,
        'cook_time': 15
    },
    
    # Lunch meals
    {
        'name': 'Grilled Chicken Salad',
        'meal_types': ['lunch', 'dinner'],
        'calories': 400,
        'macros': {'protein': 35, 'carbs': 20, 'fat': 20},
        'diet_types': ['standard', 'paleo', 'low-carb', 'high-protein'],
        'cuisine': 'american',
        'contains': [],
        'ingredients': ['6 oz chicken breast', 'Mixed greens', 'Cherry tomatoes', 'Olive oil dressing'],
        'prep_time': 15,
        'cook_time': 20
    },
    {
        'name': 'Quinoa Buddha Bowl',
        'meal_types': ['lunch', 'dinner'],
        'calories': 450,
        'macros': {'protein': 15, 'carbs': 60, 'fat': 15},
        'diet_types': ['vegan', 'vegetarian'],
        'cuisine': 'fusion',
        'contains': [],
        'ingredients': ['1 cup quinoa', 'Roasted vegetables', 'Chickpeas', 'Tahini dressing'],
        'prep_time': 20,
        'cook_time': 30
    },
    
    # Dinner meals
    {
        'name': 'Grilled Salmon with Vegetables',
        'meal_types': ['dinner'],
        'calories': 550,
        'macros': {'protein': 40, 'carbs': 30, 'fat': 25},
        'diet_types': ['standard', 'paleo', 'mediterranean'],
        'cuisine': 'mediterranean',
        'contains': ['fish'],
        'ingredients': ['6 oz salmon', 'Asparagus', 'Sweet potato', 'Olive oil', 'Lemon'],
        'prep_time': 15,
        'cook_time': 25
    },
    {
        'name': 'Beef Stir-Fry',
        'meal_types': ['dinner'],
        'calories': 600,
        'macros': {'protein': 35, 'carbs': 45, 'fat': 25},
        'diet_types': ['standard', 'high-protein'],
        'cuisine': 'asian',
        'contains': ['soy'],
        'ingredients': ['6 oz beef', 'Mixed vegetables', 'Rice', 'Soy sauce', 'Ginger', 'Garlic'],
        'prep_time': 20,
        'cook_time': 15
    },
    
    # Snacks
    {
        'name': 'Protein Smoothie',
        'meal_types': ['snack'],
        'calories': 250,
        'macros': {'protein': 25, 'carbs': 20, 'fat': 8},
        'diet_types': ['standard', 'vegetarian', 'high-protein'],
        'cuisine': 'american',
        'contains': ['dairy'],
        'ingredients': ['Protein powder', 'Banana', 'Almond milk', 'Peanut butter'],
        'prep_time': 5,
        'cook_time': 0
    },
    {
        'name': 'Mixed Nuts and Fruit',
        'meal_types': ['snack'],
        'calories': 200,
        'macros': {'protein': 6, 'carbs': 20, 'fat': 12},
        'diet_types': ['standard', 'paleo', 'vegan'],
        'cuisine': 'international',
        'contains': ['nuts'],
        'ingredients': ['Almonds', 'Walnuts', 'Dried cranberries', 'Apple slices'],
        'prep_time': 2,
        'cook_time': 0
    }
]