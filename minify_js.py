#!/usr/bin/env python3
"""
JavaScript Minification and Bundling Script for Cibozer
Combines and minifies JavaScript files for production deployment
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

class JavaScriptMinifier:
    def __init__(self):
        self.base_dir = Path('static/js')
        self.output_dir = Path('static/js/dist')
        self.output_dir.mkdir(exist_ok=True)
        
        # Files to bundle together (in load order)
        self.production_bundle = [
            'error-handling.js',
            'touch-gestures.js', 
            'keyboard-navigation.js',
            'cibozer-clean.js'
        ]
        
        self.stats = {
            'files_processed': 0,
            'original_size': 0,
            'minified_size': 0,
            'compression_ratio': 0
        }
    
    def minify_javascript(self, js_content):
        """
        Simple JavaScript minification
        Removes comments, whitespace, and unnecessary characters
        """
        # Remove single-line comments (// comments)
        js_content = re.sub(r'//.*$', '', js_content, flags=re.MULTILINE)
        
        # Remove multi-line comments (/* comments */)
        js_content = re.sub(r'/\*[\s\S]*?\*/', '', js_content)
        
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in js_content.split('\n')]
        
        # Remove empty lines
        lines = [line for line in lines if line]
        
        # Join lines and compress spaces
        minified = ' '.join(lines)
        
        # Remove spaces around operators and punctuation
        patterns = [
            (r'\s*([{}();,:])\s*', r'\1'),  # Remove spaces around {}();,:
            (r'\s*([=!<>+\-*/&|^%])\s*', r'\1'),  # Remove spaces around operators
            (r'\s+', ' '),  # Compress multiple spaces to single space
            (r';\s*}', '}'),  # Remove semicolon before closing brace
        ]
        
        for pattern, replacement in patterns:
            minified = re.sub(pattern, replacement, minified)
        
        return minified.strip()
    
    def create_bundle(self, files, output_name):
        """Create a minified bundle from multiple JavaScript files"""
        print(f"Creating bundle: {output_name}")
        
        combined_content = []
        combined_content.append(f"/* Cibozer JavaScript Bundle - Generated {datetime.now().isoformat()} */")
        
        total_original_size = 0
        
        for filename in files:
            file_path = self.base_dir / filename
            if not file_path.exists():
                print(f"  Warning: {filename} not found, skipping")
                continue
                
            print(f"  Adding {filename}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_size = len(content)
            total_original_size += original_size
            
            # Add file separator comment
            combined_content.append(f"\n/* === {filename} === */")
            combined_content.append(content)
        
        # Combine all content
        full_content = '\n'.join(combined_content)
        
        # Minify the combined content
        minified_content = self.minify_javascript(full_content)
        minified_size = len(minified_content)
        
        # Save minified bundle
        output_path = self.output_dir / output_name
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(minified_content)
        
        # Update stats
        self.stats['files_processed'] += len(files)
        self.stats['original_size'] += total_original_size
        self.stats['minified_size'] += minified_size
        
        compression_ratio = ((total_original_size - minified_size) / total_original_size) * 100
        
        print(f"  Bundle created: {output_name}")
        print(f"  Original: {total_original_size:,} bytes")
        print(f"  Minified: {minified_size:,} bytes")
        print(f"  Saved: {compression_ratio:.1f}%")
        
        return {
            'filename': output_name,
            'original_size': total_original_size,
            'minified_size': minified_size,
            'compression_ratio': compression_ratio,
            'files_included': files
        }
    
    def minify_individual_file(self, filename):
        """Minify a single JavaScript file"""
        file_path = self.base_dir / filename
        if not file_path.exists():
            print(f"File not found: {filename}")
            return None
        
        print(f"Minifying: {filename}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_size = len(content)
        minified_content = self.minify_javascript(content)
        minified_size = len(minified_content)
        
        # Create minified filename
        name_parts = filename.rsplit('.', 1)
        minified_name = f"{name_parts[0]}.min.js"
        
        # Save minified file
        output_path = self.output_dir / minified_name
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(minified_content)
        
        compression_ratio = ((original_size - minified_size) / original_size) * 100
        
        print(f"  Created: {minified_name}")
        print(f"  {original_size:,} -> {minified_size:,} bytes ({compression_ratio:.1f}% smaller)")
        
        return {
            'original': filename,
            'minified': minified_name,
            'original_size': original_size,
            'minified_size': minified_size,
            'compression_ratio': compression_ratio
        }
    
    def create_production_bundle(self):
        """Create the main production bundle"""
        return self.create_bundle(self.production_bundle, 'cibozer.min.js')
    
    def generate_manifest(self, bundle_info, individual_files):
        """Generate a manifest file with minification details"""
        manifest = {
            'generated_at': datetime.now().isoformat(),
            'bundle': bundle_info,
            'individual_files': individual_files,
            'total_stats': self.stats
        }
        
        manifest_path = self.output_dir / 'manifest.json'
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"Manifest created: {manifest_path}")
        return manifest
    
    def process_all(self):
        """Process all JavaScript files"""
        print("Starting JavaScript Minification Process")
        print("=" * 50)
        
        # Create production bundle
        bundle_info = self.create_production_bundle()
        
        print("\n" + "=" * 50)
        
        # Minify other individual files that aren't in the bundle
        all_js_files = [f.name for f in self.base_dir.glob('*.js')]
        other_files = [f for f in all_js_files if f not in self.production_bundle]
        
        individual_files = []
        for filename in other_files:
            if filename.startswith('.') or filename.endswith('.min.js'):
                continue  # Skip hidden files and already minified files
            
            result = self.minify_individual_file(filename)
            if result:
                individual_files.append(result)
        
        print("\n" + "=" * 50)
        
        # Calculate total stats
        if self.stats['original_size'] > 0:
            self.stats['compression_ratio'] = ((self.stats['original_size'] - self.stats['minified_size']) / self.stats['original_size']) * 100
        
        # Generate manifest
        manifest = self.generate_manifest(bundle_info, individual_files)
        
        # Print summary
        print("\nMINIFICATION SUMMARY")
        print("=" * 50)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Original size: {self.stats['original_size']:,} bytes")
        print(f"Minified size: {self.stats['minified_size']:,} bytes")
        print(f"Total savings: {self.stats['compression_ratio']:.1f}%")
        print(f"Space saved: {self.stats['original_size'] - self.stats['minified_size']:,} bytes")
        
        return manifest

def main():
    """Main function"""
    minifier = JavaScriptMinifier()
    manifest = minifier.process_all()
    
    print("\nJavaScript minification complete!")
    print(f"Output directory: {minifier.output_dir}")
    print("Update your templates to use the minified files for production")
    
    return 0

if __name__ == '__main__':
    exit(main())