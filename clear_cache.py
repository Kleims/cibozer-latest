import os
import shutil

print("Clearing all possible caches...")

# Clear Python cache
pycache_dirs = []
for root, dirs, files in os.walk('.'):
    if '__pycache__' in dirs:
        pycache_path = os.path.join(root, '__pycache__')
        pycache_dirs.append(pycache_path)

for pycache in pycache_dirs:
    try:
        shutil.rmtree(pycache)
        print(f"Deleted: {pycache}")
    except Exception as e:
        print(f"Could not delete {pycache}: {e}")

# Clear Flask cache
flask_cache_dirs = ['flask_cache', '.webassets-cache', 'instance/cache']
for cache_dir in flask_cache_dirs:
    if os.path.exists(cache_dir):
        try:
            shutil.rmtree(cache_dir)
            print(f"Deleted Flask cache: {cache_dir}")
        except Exception as e:
            print(f"Could not delete {cache_dir}: {e}")

# Clear any compiled templates
compiled_templates = []
for root, dirs, files in os.walk('templates'):
    for file in files:
        if file.endswith('.pyc') or file.endswith('.pyo'):
            compiled_templates.append(os.path.join(root, file))

for template in compiled_templates:
    try:
        os.remove(template)
        print(f"Deleted compiled template: {template}")
    except Exception as e:
        print(f"Could not delete {template}: {e}")

print("\nCache clearing complete!")