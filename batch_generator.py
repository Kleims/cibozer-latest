# batch_generator.py - Unified Cibozer batch video generator

import os
import sys
import time
from datetime import datetime
from typing import Dict
from cibozer import CibozerVideoGenerator
import json
import random

def main():
    """Main function to run batch generation of Cibozer videos"""
    print("\n" + "="*80)
    print("🎬 CIBOZER BATCH VIDEO GENERATOR v1.0")
    print("="*80)
    print("\nThis system generates Cibozer optimization videos showing:")
    print("  • Real-time meal plan optimization")
    print("  • Algorithm convergence visualization")
    print("  • Actual nutrition data from 250+ ingredients")
    print("  • Both longform and shorts versions")
    
    print("\n" + "-"*80)
    print("SELECT MODE:")
    print("[1] Single Video Test (1 longform + 1 shorts)")
    print("[2] Small Batch (5 video sets)")
    print("[3] Medium Batch (20 video sets)")
    print("[4] Large Batch (50 video sets)")
    print("[5] Custom Parameters")
    print("[6] Generate from Existing Meal Plans")
    
    while True:
        try:
            choice = int(input("\nEnter choice (1-6): "))
            if 1 <= choice <= 6:
                break
            else:
                print("Invalid choice. Please try again.")
        except ValueError:
            print("Please enter a number.")
    
    start_time = time.time()
    generator = CibozerVideoGenerator()
    
    if choice == 1:
        # Single test video
        print("\n" + "="*60)
        print("🧪 SINGLE VIDEO TEST MODE")
        print("="*60)
        
        print("\nGenerating test video...")
        generator.generate_video(
            diet_type="vegan",
            calories=2000,
            macro_goal="high protein",
            meal_structure="3+2",
            output_path="./cibozer_output"
        )
        
    elif choice == 2:
        # Small batch
        print("\n" + "="*60)
        print("📦 SMALL BATCH MODE (5 videos)")
        print("="*60)
        
        generate_batch(generator, 5)
        
    elif choice == 3:
        # Medium batch
        print("\n" + "="*60)
        print("📦 MEDIUM BATCH MODE (20 videos)")
        print("="*60)
        
        generate_batch(generator, 20)
        
    elif choice == 4:
        # Large batch
        print("\n" + "="*60)
        print("📦 LARGE BATCH MODE (50 videos)")
        print("="*60)
        
        confirm = input("\n⚠️  This will generate 100 video files (50 longform + 50 shorts). Continue? (y/n): ")
        if confirm.lower() != 'y':
            print("Cancelled.")
            return
        
        generate_batch(generator, 50)
        
    elif choice == 5:
        # Custom parameters
        print("\n" + "="*60)
        print("⚙️  CUSTOM PARAMETERS MODE")
        print("="*60)
        
        params = get_custom_parameters(generator)
        
        print(f"\n📊 Generating video for custom parameters...")
        generator.generate_video(
            diet_type=params['diet'],
            calories=params['calories'],
            macro_goal=params['macro'],
            meal_structure=params['structure'],
            output_path="./cibozer_output"
        )
        
    elif choice == 6:
        # Generate from existing meal plans
        print("\n" + "="*60)
        print("📄 GENERATE FROM EXISTING MEAL PLANS")
        print("="*60)
        
        generate_from_meal_plans(generator)
    
    # Calculate elapsed time
    elapsed = time.time() - start_time
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)
    
    print(f"\n⏱️  Total time: {hours}h {minutes}m {seconds}s")
    
    # Final summary
    print("\n" + "="*80)
    print("📊 GENERATION SUMMARY")
    print("="*80)
    
    if os.path.exists("cibozer_output"):
        import glob
        videos = len(glob.glob("cibozer_output/*.mp4"))
        metadata = len(glob.glob("cibozer_output/*_metadata.json"))
        plans = len(glob.glob("cibozer_output/*_plan.json"))
        
        print(f"Videos generated: {videos}")
        print(f"Metadata files: {metadata}")
        print(f"Meal plans: {plans}")
    
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n✨ Done!")


def generate_batch(generator: CibozerVideoGenerator, count: int):
    """Generate a batch of videos with smart parameter selection"""
    
    # Define smart combinations that work well
    good_combinations = [
        # High protein combinations
        ("omnivore", [2000, 2500, 3000], "high protein", ["3 meals", "3+2"]),
        ("vegetarian", [1800, 2000, 2200], "high protein", ["3+2", "5 small"]),
        ("vegan", [2000, 2200, 2500], "high protein", ["3+2", "5 small"]),
        
        # Keto combinations
        ("keto", [1500, 1800, 2000], "keto ratios", ["3 meals", "2 meals"]),
        ("low-carb", [1800, 2000, 2200], "keto ratios", ["3 meals", "2 meals"]),
        
        # Balanced combinations
        ("omnivore", [1800, 2000, 2200], "balanced", ["3 meals", "3+2"]),
        ("pescatarian", [1800, 2000, 2200], "balanced", ["3 meals", "3+2"]),
        ("vegetarian", [1800, 2000, 2200], "balanced", ["3 meals", "3+2"]),
        
        # Mediterranean
        ("pescatarian", [1800, 2000, 2200], "mediterranean", ["3 meals"]),
        ("vegetarian", [1800, 2000, 2200], "mediterranean", ["3 meals"]),
        
        # Special diets
        ("paleo", [2000, 2200, 2500], "high protein", ["3 meals", "2 meals"]),
        ("gluten-free", [1800, 2000, 2200], "balanced", ["3 meals", "3+2"]),
    ]
    
    generated = 0
    used_combinations = set()
    
    print(f"\nGenerating {count} video sets...")
    
    while generated < count:
        # Pick a random good combination
        diet_base, calorie_options, macro, structure_options = random.choice(good_combinations)
        
        # Pick specific values
        calories = random.choice(calorie_options)
        structure = random.choice(structure_options)
        
        # Create unique key
        combo_key = f"{diet_base}_{calories}_{macro}_{structure}"
        
        # Skip if already used
        if combo_key in used_combinations:
            continue
        
        used_combinations.add(combo_key)
        
        # Generate video
        print(f"\n[{generated + 1}/{count}] Generating: {diet_base} {calories}cal {macro} {structure}")
        
        try:
            generator.generate_video(
                diet_type=diet_base,
                calories=calories,
                macro_goal=macro,
                meal_structure=structure,
                output_path="./cibozer_output"
            )
            generated += 1
            print(f"✅ Success!")
            
        except Exception as e:
            print(f"❌ Failed: {e}")
            
        # Add a small delay to avoid overwhelming the system
        time.sleep(1)
    
    print(f"\n✅ Batch complete! Generated {generated} video sets.")


def get_custom_parameters(generator: CibozerVideoGenerator) -> Dict:
    """Get custom parameters from user"""
    
    # Diet type
    print("\n📋 SELECT DIET TYPE:")
    for i, diet in enumerate(generator.diet_types, 1):
        print(f"[{i}] {diet}")
    diet_idx = int(input("Choice: ")) - 1
    diet = generator.diet_types[diet_idx]
    
    # Calories
    print("\n🎯 SELECT CALORIE TARGET:")
    for i, cal in enumerate(generator.calorie_targets, 1):
        print(f"[{i}] {cal} calories")
    cal_idx = int(input("Choice: ")) - 1
    calories = generator.calorie_targets[cal_idx]
    
    # Macro goal
    print("\n💪 SELECT MACRO GOAL:")
    for i, macro in enumerate(generator.macro_goals, 1):
        print(f"[{i}] {macro}")
    macro_idx = int(input("Choice: ")) - 1
    macro = generator.macro_goals[macro_idx]
    
    # Meal structure
    print("\n🍽️  SELECT MEAL STRUCTURE:")
    for i, structure in enumerate(generator.meal_structures, 1):
        print(f"[{i}] {structure}")
    struct_idx = int(input("Choice: ")) - 1
    structure = generator.meal_structures[struct_idx]
    
    return {
        'diet': diet,
        'calories': calories,
        'macro': macro,
        'structure': structure
    }


def generate_from_meal_plans(generator: CibozerVideoGenerator):
    """Generate videos from existing meal plan files"""
    import glob
    
    if not os.path.exists("meal_plans"):
        print("\n❌ No meal_plans directory found!")
        print("Please generate meal plans first using the old system.")
        return
    
    # Find meal plan files
    plan_files = glob.glob("meal_plans/*.json")
    
    if not plan_files:
        print("\n❌ No meal plan files found!")
        return
    
    print(f"\nFound {len(plan_files)} meal plans.")
    
    # Parse filenames to extract parameters
    generated = 0
    for plan_file in plan_files[:10]:  # Limit to first 10
        try:
            # Extract parameters from filename
            # Example: plan_2000cal_vegan_all_standard.json
            basename = os.path.basename(plan_file)
            parts = basename.replace('.json', '').split('_')
            
            # Extract calories
            cal_part = [p for p in parts if 'cal' in p][0]
            calories = int(cal_part.replace('cal', ''))
            
            # Extract diet
            diet_map = {
                'standard': 'omnivore',
                'keto': 'keto',
                'vegan': 'vegan',
                'vegetarian': 'vegetarian',
                'paleo': 'paleo',
                'mediterranean': 'pescatarian',
                'carnivore': 'omnivore',
                'pescatarian': 'pescatarian'
            }
            diet = None
            for part in parts:
                if part in diet_map:
                    diet = diet_map[part]
                    break
            
            if not diet:
                diet = 'omnivore'  # Default
            
            # Determine macro goal based on diet
            macro_map = {
                'keto': 'keto ratios',
                'paleo': 'high protein',
                'carnivore': 'high protein',
                'vegan': 'balanced',
                'vegetarian': 'balanced',
                'standard': 'balanced',
                'mediterranean': 'mediterranean',
                'pescatarian': 'mediterranean'
            }
            macro = macro_map.get(diet, 'balanced')
            
            # Determine meal structure
            if '16_8_if' in basename:
                structure = '2 meals'
            elif 'omad' in basename:
                structure = 'OMAD'
            else:
                structure = '3 meals'
            
            print(f"\n[{generated + 1}] Converting: {basename}")
            print(f"  → {diet} {calories}cal {macro} {structure}")
            
            # Generate video
            generator.generate_video(
                diet_type=diet,
                calories=calories,
                macro_goal=macro,
                meal_structure=structure,
                output_path="./cibozer_output"
            )
            
            generated += 1
            
        except Exception as e:
            print(f"❌ Failed to process {plan_file}: {e}")
    
    print(f"\n✅ Generated {generated} videos from meal plans!")


def analyze_output():
    """Analyze generated videos and create summary report"""
    if not os.path.exists("cibozer_output"):
        print("No output directory found!")
        return
    
    import glob
    
    # Count files
    videos = glob.glob("cibozer_output/*.mp4")
    metadata_files = glob.glob("cibozer_output/*_metadata.json")
    
    # Analyze metadata
    stats = {
        'diets': {},
        'calories': {},
        'macros': {},
        'structures': {},
        'total_videos': len(videos),
        'longform': len([v for v in videos if not v.endswith('_shorts.mp4')]),
        'shorts': len([v for v in videos if v.endswith('_shorts.mp4')])
    }
    
    for metadata_file in metadata_files:
        with open(metadata_file, 'r') as f:
            data = json.load(f)
            params = data['parameters']
            
            # Count occurrences
            diet = params['diet_type']
            calories = params['calories']
            macro = params['macro_goal']
            structure = params['meal_structure']
            
            stats['diets'][diet] = stats['diets'].get(diet, 0) + 1
            stats['calories'][calories] = stats['calories'].get(calories, 0) + 1
            stats['macros'][macro] = stats['macros'].get(macro, 0) + 1
            stats['structures'][structure] = stats['structures'].get(structure, 0) + 1
    
    # Create report
    report = []
    report.append("\n" + "="*60)
    report.append("CIBOZER VIDEO GENERATION REPORT")
    report.append("="*60)
    report.append(f"\nTotal Videos: {stats['total_videos']}")
    report.append(f"  - Longform: {stats['longform']}")
    report.append(f"  - Shorts: {stats['shorts']}")
    
    report.append("\n\nDIET DISTRIBUTION:")
    for diet, count in sorted(stats['diets'].items(), key=lambda x: x[1], reverse=True):
        report.append(f"  {diet}: {count}")
    
    report.append("\n\nCALORIE TARGETS:")
    for cal, count in sorted(stats['calories'].items(), key=lambda x: x[0]):
        report.append(f"  {cal} cal: {count}")
    
    report.append("\n\nMACRO GOALS:")
    for macro, count in sorted(stats['macros'].items(), key=lambda x: x[1], reverse=True):
        report.append(f"  {macro}: {count}")
    
    report.append("\n\nMEAL STRUCTURES:")
    for structure, count in sorted(stats['structures'].items(), key=lambda x: x[1], reverse=True):
        report.append(f"  {structure}: {count}")
    
    # Save report
    report_text = '\n'.join(report)
    with open('cibozer_output/generation_report.txt', 'w') as f:
        f.write(report_text)
    
    print(report_text)
    print("\n📄 Report saved to: cibozer_output/generation_report.txt")


if __name__ == "__main__":
    try:
        main()
        
        # Optionally analyze output
        if os.path.exists("cibozer_output"):
            if input("\n\nGenerate analysis report? (y/n): ").lower() == 'y':
                analyze_output()
        
    except KeyboardInterrupt:
        print("\n\n👋 Program cancelled by user. Goodbye!")
    except Exception as e:
        print(f"\n\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()
        print("\nPlease check your setup and try again.")