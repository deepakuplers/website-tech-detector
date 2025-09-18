#!/usr/bin/env python3
"""
Vercel-Compatible Flask Application for Website Technology Detector
Focused on CMS and E-commerce Platform Detection
"""

from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

app = Flask(__name__)

class CMSEcommerceDetector:
    def __init__(self):
        # Focused signatures for CMS and E-commerce platforms
        self.signatures = {
            # Content Management Systems
            'WordPress': {
                'admin_paths': ['/wp-admin/', '/wp-login.php'],
                'api_paths': ['/wp-json/wp/v2/', '/xmlrpc.php'],
                'html_patterns': [
                    r'/wp-content/themes/',
                    r'/wp-content/plugins/', 
                    r'wp_enqueue_script',
                    r'wp-block-'
                ],
                'meta_patterns': [r'<meta name="generator" content="WordPress'],
                'header_patterns': [r'X-Pingback.*xmlrpc\.php'],
                'js_patterns': [r'wp\.', r'wpAjax'],
                'css_patterns': [r'wp-block-', r'post-\d+', r'page-id-\d+']
            },
            
            'Drupal': {
                'admin_paths': ['/admin/', '/user/login'],
                'api_paths': ['/jsonapi/', '/rest/'],
                'html_patterns': [
                    r'/sites/default/files/',
                    r'/core/modules/',
                    r'data-drupal-selector',
                    r'drupal\.settings'
                ],
                'meta_patterns': [r'<meta name="generator" content="Drupal'],
                'header_patterns': [r'X-Drupal-Cache', r'X-Generator.*Drupal'],
                'js_patterns': [r'drupalSettings', r'Drupal\.behaviors']
            },
            
            'Joomla': {
                'admin_paths': ['/administrator/', '/component/'],
                'html_patterns': [
                    r'/media/jui/',
                    r'/templates/.*\.css',
                    r'joomla',
                    r'option=com_'
                ],
                'meta_patterns': [r'<meta name="generator" content="Joomla'],
                'js_patterns': [r'Joomla\.']
            },
            
            # E-commerce Platforms
            'Shopify': {
                'admin_paths': ['/admin/'],
                'api_paths': ['/cart.js', '/products.json', '/collections.json'],
                'html_patterns': [
                    r'cdn\.shopify\.com',
                    r'\.myshopify\.com',
                    r'Shopify\.theme',
                    r'/assets/shopify_'
                ],
                'header_patterns': [r'X-Shopify-Stage', r'server.*Shopify'],
                'js_patterns': [r'Shopify\.', r'ShopifyAPI']
            },
            
            'WooCommerce': {
                'html_patterns': [
                    r'woocommerce',
                    r'/wc-ajax/',
                    r'wc_single_product_params',
                    r'woocommerce-page'
                ],
                'css_patterns': [r'woocommerce-', r'wc-block-', r'product-'],
                'js_patterns': [r'wc_', r'woocommerce_params']
            },
            
            'Magento': {
                'admin_paths': ['/admin/', '/downloader/'],
                'api_paths': ['/rest/V1/', '/api/'],
                'html_patterns': [
                    r'/skin/frontend/',
                    r'/js/mage/',
                    r'Mage\.Cookies',
                    r'var/cache/mage'
                ],
                'js_patterns': [r'Mage\.', r'Magento']
            },
            
            'BigCommerce': {
                'html_patterns': [
                    r'cdn11\.bigcommerce\.com',
                    r'bigcommerce',
                    r'/bc-sf-filter/'
                ],
                'js_patterns': [r'BigCommerce']
            }
        }

    def analyze_website(self, url):
        """Analyze website for CMS and E-commerce platforms"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            headers = {
                'User-Agent': 'TechStack-Analyzer/1.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1',
                'Connection': 'keep-alive',
            }
            
            session = requests.Session()
            session.headers.update(headers)
            
            # Get main page
            response = session.get(url, timeout=10, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Run detection
            detected_platforms = {}
            
            for platform, patterns in self.signatures.items():
                score = 0
                detection_methods = []
                
                # Test admin paths (high confidence)
                if 'admin_paths' in patterns:
                    for path in patterns['admin_paths']:
                        if self._test_path(url, session, path):
                            score += 30
                            detection_methods.append(f"Admin path: {path}")
                
                # Test API paths (high confidence)
                if 'api_paths' in patterns:
                    for path in patterns['api_paths']:
                        if self._test_path(url, session, path):
                            score += 25
                            detection_methods.append(f"API endpoint: {path}")
                
                # Analyze HTML content
                if 'html_patterns' in patterns:
                    for pattern in patterns['html_patterns']:
                        if re.search(pattern, response.text, re.IGNORECASE):
                            score += 15
                            detection_methods.append(f"HTML pattern: {pattern}")
                
                # Check meta tags
                if 'meta_patterns' in patterns:
                    meta_content = str(soup.find_all('meta'))
                    for pattern in patterns['meta_patterns']:
                        if re.search(pattern, meta_content, re.IGNORECASE):
                            score += 20
                            detection_methods.append(f"Meta tag: generator")
                
                # Check headers
                if 'header_patterns' in patterns:
                    header_content = ' '.join([f"{k}: {v}" for k, v in response.headers.items()])
                    for pattern in patterns['header_patterns']:
                        if re.search(pattern, header_content, re.IGNORECASE):
                            score += 20
                            detection_methods.append(f"HTTP header")
                
                # Check JavaScript
                if 'js_patterns' in patterns:
                    scripts = soup.find_all('script')
                    script_content = ' '.join([script.get_text() or '' for script in scripts])
                    for pattern in patterns['js_patterns']:
                        if re.search(pattern, script_content):
                            score += 10
                            detection_methods.append(f"JavaScript: {pattern}")
                
                # Check CSS classes
                if 'css_patterns' in patterns:
                    all_classes = []
                    for element in soup.find_all(class_=True):
                        if isinstance(element.get('class'), list):
                            all_classes.extend(element.get('class'))
                        else:
                            all_classes.append(element.get('class'))
                    
                    class_string = ' '.join(all_classes)
                    for pattern in patterns['css_patterns']:
                        if re.search(pattern, class_string):
                            score += 10
                            detection_methods.append(f"CSS class: {pattern}")
                
                # If score is high enough, add to detected platforms
                if score >= 30:  # Minimum threshold
                    detected_platforms[platform] = {
                        'score': score,
                        'methods': detection_methods[:5]  # Top 5 detection methods
                    }
            
            # Categorize results
            result = self._categorize_results(detected_platforms, response.headers, url)
            result['success'] = True
            result['status_code'] = response.status_code
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'categories': {},
                'headers': {},
                'url': url
            }

    def _test_path(self, base_url, session, path):
        """Test if a specific path exists"""
        try:
            test_url = urljoin(base_url, path)
            response = session.head(test_url, timeout=5, allow_redirects=False)
            return response.status_code in [200, 301, 302, 403]
        except:
            return False

    def _categorize_results(self, detected_platforms, headers, url):
        """Categorize detected platforms"""
        categories = {}
        
        # CMS Platforms
        cms_platforms = ['WordPress', 'Drupal', 'Joomla', 'Ghost', 'Contentful']
        cms_found = []
        for platform in cms_platforms:
            if platform in detected_platforms:
                result = detected_platforms[platform]
                cms_found.append({
                    'name': platform,
                    'score': result['score'],
                    'methods': result['methods']
                })
        
        if cms_found:
            categories['Content Management Systems'] = sorted(cms_found, key=lambda x: x['score'], reverse=True)
        
        # E-commerce Platforms
        ecommerce_platforms = ['Shopify', 'WooCommerce', 'Magento', 'BigCommerce']
        ecommerce_found = []
        for platform in ecommerce_platforms:
            if platform in detected_platforms:
                result = detected_platforms[platform]
                ecommerce_found.append({
                    'name': platform,
                    'score': result['score'],
                    'methods': result['methods']
                })
        
        if ecommerce_found:
            categories['E-commerce Platforms'] = sorted(ecommerce_found, key=lambda x: x['score'], reverse=True)
        
        return {
            'categories': categories,
            'headers': dict(headers),
            'url': url,
            'total_detections': len(detected_platforms)
        }

# Initialize detector
detector = CMSEcommerceDetector()

@app.route('/')
def index():
    """Serve the main page"""
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>CMS & E-commerce Detector</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            .header { text-align: center; margin-bottom: 40px; }
            .form-group { margin-bottom: 20px; }
            input[type="text"] { width: 70%; padding: 10px; font-size: 16px; }
            button { padding: 10px 20px; font-size: 16px; background: #007bff; color: white; border: none; cursor: pointer; }
            .results { margin-top: 30px; }
            .category { background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px; }
            .platform { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
            .score { font-weight: bold; color: #28a745; }
            .methods { font-size: 14px; color: #666; margin-top: 10px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 CMS & E-commerce Platform Detector</h1>
            <p>Analyze any website to detect its content management system and e-commerce platform</p>
        </div>
        
        <div class="form-group">
            <input type="text" id="urlInput" placeholder="Enter website URL (e.g., example.com)" />
            <button onclick="analyzeWebsite()">Analyze</button>
        </div>
        
        <div id="results" class="results"></div>
        
        <script>
            async function analyzeWebsite() {
                const url = document.getElementById('urlInput').value.trim();
                if (!url) return alert('Please enter a URL');
                
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = '<p>Analyzing... Please wait.</p>';
                
                try {
                    const response = await fetch('/api/analyze', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url: url })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        displayResults(result);
                    } else {
                        resultsDiv.innerHTML = `<p style="color: red;">Error: ${result.error}</p>`;
                    }
                } catch (error) {
                    resultsDiv.innerHTML = `<p style="color: red;">Network error: ${error.message}</p>`;
                }
            }
            
            function displayResults(result) {
                const resultsDiv = document.getElementById('results');
                let html = `<h3>Analysis Results for: ${result.url}</h3>`;
                
                if (Object.keys(result.categories).length === 0) {
                    html += '<p>No CMS or E-commerce platforms detected.</p>';
                } else {
                    for (const [category, platforms] of Object.entries(result.categories)) {
                        html += `<div class="category">`;
                        html += `<h4>${category}</h4>`;
                        
                        platforms.forEach(platform => {
                            html += `<div class="platform">`;
                            html += `<strong>${platform.name}</strong> `;
                            html += `<span class="score">Score: ${platform.score}</span>`;
                            html += `<div class="methods">Detection methods: ${platform.methods.join(', ')}</div>`;
                            html += `</div>`;
                        });
                        
                        html += `</div>`;
                    }
                }
                
                resultsDiv.innerHTML = html;
            }
            
            // Allow Enter key to trigger analysis
            document.getElementById('urlInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') analyzeWebsite();
            });
        </script>
    </body>
    </html>
    '''

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """API endpoint for website analysis"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'})
        
        # Run analysis
        result = detector.analyze_website(url)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Server error: {str(e)}',
            'categories': {},
            'headers': {}
        })

# For Vercel
if __name__ == '__main__':
    app.run()