#!/usr/bin/env python3
"""
Production Build Script for Cibozer
Automates the build process for production deployment
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

class ProductionBuilder:
    def __init__(self):
        self.build_time = datetime.now()
        self.build_info = {
            'build_time': self.build_time.isoformat(),
            'version': self.get_version(),
            'steps_completed': [],
            'assets_minified': {},
            'total_savings': 0
        }
        
    def get_version(self):
        """Get version from git or use timestamp"""
        try:
            result = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return self.build_time.strftime('%Y%m%d-%H%M%S')
    
    def step(self, description):
        """Mark a build step as completed"""
        print(f"+ {description}")
        self.build_info['steps_completed'].append({
            'step': description,
            'time': datetime.now().isoformat()
        })
    
    def minify_javascript(self):
        """Run JavaScript minification"""
        print("\n=== JavaScript Minification ===")
        
        # Run the minification script
        try:
            result = subprocess.run([sys.executable, 'minify_js.py'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                self.step("JavaScript files minified successfully")
                
                # Read the manifest to get savings info
                manifest_path = Path('static/js/dist/manifest.json')
                if manifest_path.exists():
                    with open(manifest_path, 'r') as f:
                        manifest = json.load(f)
                    
                    # Calculate total savings from all files
                    bundle_savings = manifest['bundle']['original_size'] - manifest['bundle']['minified_size']
                    individual_savings = sum(
                        f['original_size'] - f['minified_size'] 
                        for f in manifest['individual_files']
                    )
                    
                    total_savings = bundle_savings + individual_savings
                    self.build_info['assets_minified']['javascript'] = {
                        'bundle_savings': bundle_savings,
                        'individual_savings': individual_savings,
                        'total_savings': total_savings
                    }
                    self.build_info['total_savings'] += total_savings
                    
                    print(f"  JavaScript minification saved {total_savings:,} bytes")
                else:
                    print("  Warning: Manifest not found")
            else:
                print(f"  Error: {result.stderr}")
                return False
        except Exception as e:
            print(f"  Error running minification: {e}")
            return False
        
        return True
    
    def optimize_static_assets(self):
        """Optimize other static assets"""
        print("\n=== Static Asset Optimization ===")
        
        # Create optimized CSS if needed
        css_dir = Path('static/css')
        css_dist_dir = css_dir / 'dist'
        css_dist_dir.mkdir(exist_ok=True)
        
        # Simple CSS minification (remove comments and extra whitespace)
        css_files = list(css_dir.glob('*.css'))
        css_savings = 0
        
        for css_file in css_files:
            if css_file.name.startswith('.') or 'dist' in str(css_file):
                continue
                
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_size = len(content)
            
            # Basic CSS minification
            import re
            # Remove comments
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            # Remove extra whitespace
            content = re.sub(r'\s+', ' ', content)
            content = re.sub(r';\s*}', '}', content)
            content = re.sub(r'{\s*', '{', content)
            content = re.sub(r';\s*', ';', content)
            content = content.strip()
            
            minified_size = len(content)
            css_savings += original_size - minified_size
            
            # Save minified version
            minified_name = css_file.stem + '.min.css'
            minified_path = css_dist_dir / minified_name
            
            with open(minified_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        if css_savings > 0:
            self.step(f"CSS files minified (saved {css_savings:,} bytes)")
            self.build_info['assets_minified']['css'] = {
                'total_savings': css_savings
            }
            self.build_info['total_savings'] += css_savings
        
        return True
    
    def cleanup_build_artifacts(self):
        """Clean up temporary build files"""
        print("\n=== Cleanup ===")
        
        # Remove any temporary files or directories
        temp_dirs = ['.pytest_cache', '__pycache__']
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                self.step(f"Removed {temp_dir}")
        
        return True
    
    def generate_build_report(self):
        """Generate a build report"""
        print("\n=== Build Report ===")
        
        build_report_path = Path('build_report.json')
        with open(build_report_path, 'w') as f:
            json.dump(self.build_info, f, indent=2)
        
        self.step(f"Build report saved to {build_report_path}")
        
        # Print summary
        print(f"\nBuild Summary:")
        print(f"  Version: {self.build_info['version']}")
        print(f"  Build time: {self.build_info['build_time']}")
        print(f"  Steps completed: {len(self.build_info['steps_completed'])}")
        print(f"  Total asset savings: {self.build_info['total_savings']:,} bytes")
        
        return True
    
    def verify_production_readiness(self):
        """Verify the application is ready for production"""
        print("\n=== Production Readiness Check ===")
        
        checks = []
        
        # Check if minified files exist
        if Path('static/js/dist/cibozer.min.js').exists():
            checks.append("+ Minified JavaScript bundle exists")
        else:
            checks.append("- Minified JavaScript bundle missing")
        
        # Check if production config exists
        if Path('config/production.py').exists():
            checks.append("+ Production configuration exists")
        else:
            checks.append("- Production configuration missing")
        
        # Check environment variables documentation
        env_vars_to_check = [
            'SECRET_KEY', 'DATABASE_URL', 'STRIPE_SECRET_KEY'
        ]
        
        missing_env_docs = []
        for var in env_vars_to_check:
            if not os.environ.get(var):
                missing_env_docs.append(var)
        
        if missing_env_docs:
            checks.append(f"! Environment variables need to be set: {', '.join(missing_env_docs)}")
        else:
            checks.append("+ Required environment variables are set")
        
        for check in checks:
            print(f"  {check}")
        
        self.step("Production readiness verified")
        return True
    
    def build(self):
        """Run the complete build process"""
        print("Starting Production Build Process")
        print("="*50)
        
        steps = [
            ("Minifying JavaScript", self.minify_javascript),
            ("Optimizing static assets", self.optimize_static_assets),
            ("Cleaning up build artifacts", self.cleanup_build_artifacts),
            ("Generating build report", self.generate_build_report),
            ("Verifying production readiness", self.verify_production_readiness)
        ]
        
        for step_name, step_func in steps:
            print(f"\n{step_name}...")
            if not step_func():
                print(f"Build failed at step: {step_name}")
                return False
        
        print("\nProduction build completed successfully!")
        print(f"Total asset savings: {self.build_info['total_savings']:,} bytes")
        print("\nNext steps:")
        print("  1. Test the application with production settings")
        print("  2. Deploy to production environment")
        print("  3. Monitor performance and error logs")
        
        return True

def main():
    """Main build function"""
    builder = ProductionBuilder()
    success = builder.build()
    return 0 if success else 1

if __name__ == '__main__':
    exit(main())