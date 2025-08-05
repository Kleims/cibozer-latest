"""Static asset optimization and CDN configuration"""
import os
import hashlib
from flask import url_for as flask_url_for
from functools import wraps

class StaticOptimizer:
    """Handle static asset optimization"""
    
    def __init__(self, app=None):
        self.app = app
        self.asset_hashes = {}
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
        # Override url_for to add CDN support
        app.jinja_env.globals['url_for'] = self.cdn_url_for
        
        # Add cache busting
        if app.config.get('ENV') == 'production':
            self.generate_asset_hashes()
    
    def generate_asset_hashes(self):
        """Generate hashes for static files for cache busting"""
        static_folder = self.app.static_folder
        if not static_folder:
            return
        
        for root, dirs, files in os.walk(static_folder):
            for filename in files:
                if filename.endswith(('.js', '.css', '.jpg', '.png', '.gif')):
                    filepath = os.path.join(root, filename)
                    relative_path = os.path.relpath(filepath, static_folder)
                    
                    # Generate hash of file content
                    with open(filepath, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()[:8]
                    
                    self.asset_hashes[relative_path.replace('\\', '/')] = file_hash
    
    def cdn_url_for(self, endpoint, **values):
        """Custom url_for that supports CDN"""
        # Get the URL from Flask's url_for
        url = flask_url_for(endpoint, **values)
        
        # If it's a static file and we're in production, use CDN
        if endpoint == 'static' and self.app.config.get('USE_CDN'):
            cdn_base = self.app.config.get('CDN_URL', '')
            if cdn_base:
                # Add cache busting hash
                filename = values.get('filename', '')
                if filename in self.asset_hashes:
                    url = f"{cdn_base}/static/{filename}?v={self.asset_hashes[filename]}"
                else:
                    url = f"{cdn_base}/static/{filename}"
        
        return url

def optimize_images():
    """Optimize all images in static folder"""
    try:
        from PIL import Image
        import os
        
        static_folder = 'static'
        optimized = 0
        
        for root, dirs, files in os.walk(static_folder):
            for filename in files:
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    filepath = os.path.join(root, filename)
                    
                    # Open and optimize
                    img = Image.open(filepath)
                    
                    # Convert RGBA to RGB for JPEG
                    if img.mode == 'RGBA' and filename.lower().endswith(('.jpg', '.jpeg')):
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        rgb_img.paste(img, mask=img.split()[3])
                        img = rgb_img
                    
                    # Save optimized version
                    img.save(filepath, optimize=True, quality=85)
                    optimized += 1
        
        print(f"Optimized {optimized} images")
        
    except ImportError:
        print("Pillow not installed - skipping image optimization")

def generate_webp_versions():
    """Generate WebP versions of images"""
    try:
        from PIL import Image
        import os
        
        static_folder = 'static'
        generated = 0
        
        for root, dirs, files in os.walk(static_folder):
            for filename in files:
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    filepath = os.path.join(root, filename)
                    webp_path = os.path.splitext(filepath)[0] + '.webp'
                    
                    # Skip if WebP already exists
                    if os.path.exists(webp_path):
                        continue
                    
                    # Convert to WebP
                    img = Image.open(filepath)
                    img.save(webp_path, 'WEBP', quality=85)
                    generated += 1
        
        print(f"Generated {generated} WebP images")
        
    except ImportError:
        print("Pillow not installed - skipping WebP generation")

def minify_static_assets():
    """Minify CSS and JavaScript files"""
    try:
        import cssmin
        import jsmin
        import os
        
        static_folder = 'static'
        minified = 0
        
        # Minify CSS
        for root, dirs, files in os.walk(os.path.join(static_folder, 'css')):
            for filename in files:
                if filename.endswith('.css') and not filename.endswith('.min.css'):
                    filepath = os.path.join(root, filename)
                    min_path = os.path.splitext(filepath)[0] + '.min.css'
                    
                    with open(filepath, 'r') as f:
                        css_content = f.read()
                    
                    minified_css = cssmin.cssmin(css_content)
                    
                    with open(min_path, 'w') as f:
                        f.write(minified_css)
                    
                    minified += 1
        
        # Minify JavaScript
        for root, dirs, files in os.walk(os.path.join(static_folder, 'js')):
            for filename in files:
                if filename.endswith('.js') and not filename.endswith('.min.js'):
                    filepath = os.path.join(root, filename)
                    min_path = os.path.splitext(filepath)[0] + '.min.js'
                    
                    with open(filepath, 'r') as f:
                        js_content = f.read()
                    
                    minified_js = jsmin.jsmin(js_content)
                    
                    with open(min_path, 'w') as f:
                        f.write(minified_js)
                    
                    minified += 1
        
        print(f"Minified {minified} files")
        
    except ImportError:
        print("cssmin/jsmin not installed - skipping minification")

# Service worker for offline support
SERVICE_WORKER_JS = """
const CACHE_NAME = 'cibozer-v1';
const urlsToCache = [
  '/',
  '/static/css/style.min.css',
  '/static/js/cibozer-clean.min.js',
  '/static/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        // Cache hit - return response
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});

self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
"""

def create_service_worker():
    """Create service worker for offline support"""
    with open('static/sw.js', 'w') as f:
        f.write(SERVICE_WORKER_JS)
    print("Created service worker")

def create_manifest():
    """Create PWA manifest"""
    manifest = {
        "name": "Cibozer - AI Meal Planning",
        "short_name": "Cibozer",
        "description": "AI-powered meal planning for your lifestyle",
        "start_url": "/",
        "display": "standalone",
        "theme_color": "#007bff",
        "background_color": "#ffffff",
        "icons": [
            {
                "src": "/static/images/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/images/icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    
    import json
    with open('static/manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)
    print("Created PWA manifest")