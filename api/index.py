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
    """Serve the beautiful professional UI"""
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TechStack Analyzer by Uplers/Mavlers</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
                overflow-x: hidden;
            }

            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 20px;
            }

            /* Header */
            .header {
                text-align: center;
                padding: 60px 0 40px;
                animation: fadeInDown 1s ease;
            }

            .logo {
                display: inline-flex;
                align-items: center;
                gap: 15px;
                margin-bottom: 20px;
            }

            .logo i {
                font-size: 48px;
                color: #FFD700;
                text-shadow: 0 4px 8px rgba(0,0,0,0.2);
                animation: pulse 2s infinite;
            }

            .logo h1 {
                font-size: 42px;
                font-weight: 700;
                color: white;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            }

            .tagline {
                font-size: 18px;
                color: rgba(255,255,255,0.9);
                font-weight: 400;
                max-width: 600px;
                margin: 0 auto;
            }

            /* Main Content */
            .main-content {
                animation: fadeInUp 1s ease 0.3s both;
            }

            .search-card {
                background: rgba(255,255,255,0.95);
                backdrop-filter: blur(20px);
                border-radius: 24px;
                padding: 50px;
                margin: 40px auto;
                max-width: 800px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.1);
                border: 1px solid rgba(255,255,255,0.2);
                transition: all 0.3s ease;
            }

            .search-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 30px 80px rgba(0,0,0,0.15);
            }

            .search-title {
                font-size: 32px;
                font-weight: 700;
                margin-bottom: 15px;
                color: #2d3748;
                text-align: center;
            }

            .search-subtitle {
                font-size: 16px;
                color: #718096;
                text-align: center;
                margin-bottom: 40px;
                line-height: 1.6;
            }

            .search-form {
                position: relative;
                margin-bottom: 40px;
            }

            .input-container {
                position: relative;
                display: flex;
                gap: 15px;
                align-items: stretch;
            }

            .input-wrapper {
                flex: 1;
                position: relative;
            }

            .input-icon {
                position: absolute;
                left: 20px;
                top: 50%;
                transform: translateY(-50%);
                color: #a0aec0;
                font-size: 18px;
                z-index: 2;
            }

            #urlInput {
                width: 100%;
                padding: 18px 20px 18px 55px;
                border: 2px solid #e2e8f0;
                border-radius: 16px;
                font-size: 16px;
                background: white;
                transition: all 0.3s ease;
                outline: none;
            }

            #urlInput:focus {
                border-color: #667eea;
                box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
                transform: translateY(-1px);
            }

            #urlInput::placeholder {
                color: #a0aec0;
            }

            .analyze-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 18px 32px;
                border-radius: 16px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                gap: 10px;
                white-space: nowrap;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }

            .analyze-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
            }

            .analyze-btn:active {
                transform: translateY(0);
            }

            .analyze-btn.loading {
                background: #a0aec0;
                cursor: not-allowed;
            }

            .analyze-btn.loading i {
                animation: spin 1s linear infinite;
            }

            /* Examples */
            .examples {
                text-align: center;
            }

            .examples-title {
                color: #4a5568;
                margin-bottom: 20px;
                font-weight: 500;
            }

            .example-links {
                display: flex;
                gap: 15px;
                justify-content: center;
                flex-wrap: wrap;
            }

            .example-link {
                background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
                color: #667eea;
                padding: 12px 20px;
                border-radius: 12px;
                cursor: pointer;
                transition: all 0.3s ease;
                font-weight: 500;
                border: 1px solid rgba(102, 126, 234, 0.1);
            }

            .example-link:hover {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                transform: translateY(-2px);
                box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
            }

            /* Results */
            .results {
                margin-top: 40px;
                opacity: 0;
                transform: translateY(20px);
                transition: all 0.5s ease;
            }

            .results.visible {
                opacity: 1;
                transform: translateY(0);
            }

            .results-header {
                background: rgba(255,255,255,0.95);
                backdrop-filter: blur(20px);
                border-radius: 20px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                border: 1px solid rgba(255,255,255,0.2);
            }

            .analyzed-url {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 15px;
                flex-wrap: wrap;
            }

            .url-info {
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .url-info i {
                color: #667eea;
                font-size: 20px;
            }

            .url-text {
                font-size: 18px;
                font-weight: 600;
                color: #2d3748;
                word-break: break-all;
            }

            .status-badge {
                background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 14px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 6px;
            }

            .new-analysis-btn {
                background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
                color: #667eea;
                border: 2px solid #e2e8f0;
                padding: 12px 24px;
                border-radius: 12px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                gap: 8px;
                margin-top: 20px;
            }

            .new-analysis-btn:hover {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-color: #667eea;
                transform: translateY(-2px);
            }

            /* Category Cards */
            .category-grid {
                display: grid;
                gap: 25px;
                margin-bottom: 30px;
            }

            .category-card {
                background: rgba(255,255,255,0.95);
                backdrop-filter: blur(20px);
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.08);
                border: 1px solid rgba(255,255,255,0.2);
                transition: all 0.3s ease;
                animation: slideInUp 0.6s ease forwards;
            }

            .category-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 20px 40px rgba(0,0,0,0.12);
            }

            .category-header {
                display: flex;
                align-items: center;
                gap: 15px;
                margin-bottom: 25px;
            }

            .category-icon {
                width: 50px;
                height: 50px;
                border-radius: 15px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 22px;
                color: white;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }

            .category-title {
                font-size: 22px;
                font-weight: 700;
                color: #2d3748;
                flex: 1;
            }

            .detection-count {
                background: #f7fafc;
                color: #4a5568;
                padding: 6px 12px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
            }

            .platform-list {
                space-y: 15px;
            }

            .platform-item {
                background: #f8fafc;
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 15px;
                border-left: 4px solid #667eea;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }

            .platform-item:hover {
                background: #f1f5f9;
                transform: translateX(5px);
            }

            .platform-item::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
                opacity: 0;
                transition: opacity 0.3s ease;
            }

            .platform-item:hover::before {
                opacity: 1;
            }

            .platform-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 12px;
                position: relative;
                z-index: 1;
            }

            .platform-name {
                font-size: 18px;
                font-weight: 700;
                color: #2d3748;
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .platform-name::before {
                content: '';
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                animation: pulse 2s infinite;
            }

            .confidence-badge {
                background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                color: white;
                padding: 6px 12px;
                border-radius: 10px;
                font-size: 12px;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 5px;
            }

            .detection-methods {
                position: relative;
                z-index: 1;
            }

            .methods-title {
                font-size: 14px;
                font-weight: 600;
                color: #4a5568;
                margin-bottom: 8px;
                display: flex;
                align-items: center;
                gap: 6px;
            }

            .methods-list {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }

            .method-tag {
                background: white;
                color: #4a5568;
                padding: 4px 8px;
                border-radius: 8px;
                font-size: 11px;
                font-weight: 500;
                border: 1px solid #e2e8f0;
            }

            /* Loading Animation */
            .loading-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(102, 126, 234, 0.9);
                backdrop-filter: blur(10px);
                display: none;
                align-items: center;
                justify-content: center;
                z-index: 1000;
            }

            .loading-content {
                text-align: center;
                color: white;
            }

            .loading-spinner {
                width: 60px;
                height: 60px;
                border: 4px solid rgba(255,255,255,0.3);
                border-top: 4px solid white;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }

            .loading-text {
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 10px;
            }

            .loading-subtitle {
                font-size: 14px;
                opacity: 0.8;
            }

            /* Animations */
            @keyframes fadeInDown {
                from {
                    opacity: 0;
                    transform: translateY(-30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(30px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            @keyframes slideInUp {
                from {
                    opacity: 0;
                    transform: translateY(40px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            /* Responsive */
            @media (max-width: 768px) {
                .header {
                    padding: 40px 0 30px;
                }
                
                .logo h1 {
                    font-size: 32px;
                }
                
                .search-card {
                    padding: 30px;
                    margin: 20px auto;
                }
                
                .input-container {
                    flex-direction: column;
                }
                
                .example-links {
                    flex-direction: column;
                    align-items: center;
                }
                
                .analyzed-url {
                    flex-direction: column;
                    text-align: center;
                }
            }
        </style>
    </head>
    <body>
        <!-- Loading Overlay -->
        <div class="loading-overlay" id="loadingOverlay">
            <div class="loading-content">
                <div class="loading-spinner"></div>
                <div class="loading-text">Analyzing Website...</div>
                <div class="loading-subtitle">Scanning for CMS and E-commerce platforms</div>
            </div>
        </div>

        <!-- Header -->
        <header class="header">
            <div class="container">
                <div class="logo">
                    <i class="fas fa-search-dollar"></i>
                    <h1>TechStack Analyzer by Uplers/Mavlers</h1>
                </div>
                <p class="tagline">Discover the technology stack behind any website</p>
            </div>
        </header>

        <!-- Main Content -->
        <main class="main-content">
            <div class="container">
                <!-- Search Section -->
                <div class="search-card">
                    <h2 class="search-title">Enter Website URL</h2>
                    <p class="search-subtitle">Analyze any website to discover its technology stack, CMS, frameworks, and more</p>
                    
                    <form class="search-form" onsubmit="return false;">
                        <div class="input-container">
                            <div class="input-wrapper">
                                <i class="fas fa-globe input-icon"></i>
                                <input type="text" id="urlInput" placeholder="Enter website URL (e.g., example.com)" />
                            </div>
                            <button type="button" class="analyze-btn" onclick="analyzeWebsite()" id="analyzeBtn">
                                <i class="fas fa-search"></i>
                                Analyze Website
                            </button>
                        </div>
                    </form>

                    <!-- Examples -->
                    <div class="examples">
                        <p class="examples-title">Try these examples:</p>
                        <div class="example-links">
                            <span class="example-link" onclick="setUrl('wordpress.org')">wordpress.org</span>
                            <span class="example-link" onclick="setUrl('shopify.com')">shopify.com</span>
                            <span class="example-link" onclick="setUrl('github.com')">github.com</span>
                            <span class="example-link" onclick="setUrl('netlify.com')">netlify.com</span>
                        </div>
                    </div>
                </div>

                <!-- Results Section -->
                <div class="results" id="resultsSection">
                    <!-- Results will be populated here -->
                </div>
            </div>
        </main>

        <script>
            async function analyzeWebsite() {
                const url = document.getElementById('urlInput').value.trim();
                if (!url) {
                    alert('Please enter a website URL');
                    return;
                }

                // Show loading
                showLoading();
                
                try {
                    const response = await fetch('/api/analyze', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ url: url })
                    });
                    
                    const result = await response.json();
                    
                    hideLoading();
                    
                    if (result.success) {
                        displayResults(result);
                    } else {
                        showError(result.error);
                    }
                } catch (error) {
                    hideLoading();
                    showError('Network error: ' + error.message);
                }
            }

            function showLoading() {
                document.getElementById('loadingOverlay').style.display = 'flex';
                const btn = document.getElementById('analyzeBtn');
                btn.classList.add('loading');
                btn.innerHTML = '<i class="fas fa-spinner"></i> Analyzing...';
                btn.disabled = true;
            }

            function hideLoading() {
                document.getElementById('loadingOverlay').style.display = 'none';
                const btn = document.getElementById('analyzeBtn');
                btn.classList.remove('loading');
                btn.innerHTML = '<i class="fas fa-search"></i> Analyze Website';
                btn.disabled = false;
            }

            function displayResults(result) {
                const resultsSection = document.getElementById('resultsSection');
                
                let html = `
                    <div class="results-header">
                        <div class="analyzed-url">
                            <div class="url-info">
                                <i class="fas fa-link"></i>
                                <span class="url-text">${result.url}</span>
                            </div>
                            <div class="status-badge">
                                <i class="fas fa-check-circle"></i>
                                Analysis Complete
                            </div>
                        </div>
                        <button class="new-analysis-btn" onclick="newAnalysis()">
                            <i class="fas fa-plus"></i>
                            Analyze New URL
                        </button>
                    </div>
                `;

                if (Object.keys(result.categories).length === 0) {
                    html += `
                        <div class="category-card">
                            <div class="category-header">
                                <div class="category-icon">
                                    <i class="fas fa-question"></i>
                                </div>
                                <h3 class="category-title">No Technologies Detected</h3>
                            </div>
                            <p style="color: #718096; line-height: 1.6;">
                                We couldn't detect any specific CMS or E-commerce platforms for this website. 
                                This might be due to custom development, heavy security measures, or the use of less common platforms.
                            </p>
                        </div>
                    `;
                } else {
                    html += '<div class="category-grid">';
                    
                    for (const [category, platforms] of Object.entries(result.categories)) {
                        const iconClass = getCategoryIcon(category);
                        
                        html += `
                            <div class="category-card">
                                <div class="category-header">
                                    <div class="category-icon">
                                        <i class="${iconClass}"></i>
                                    </div>
                                    <h3 class="category-title">${category}</h3>
                                    <span class="detection-count">${platforms.length} detected</span>
                                </div>
                                <div class="platform-list">
                        `;
                        
                        platforms.forEach(platform => {
                            html += `
                                <div class="platform-item">
                                    <div class="platform-header">
                                        <div class="platform-name">${platform.name}</div>
                                        <div class="confidence-badge">
                                            <i class="fas fa-shield-alt"></i>
                                            Detected
                                        </div>
                                    </div>
                                    <div class="detection-methods">
                                        <div class="methods-title">
                                            <i class="fas fa-search-plus"></i>
                                            Detection Methods:
                                        </div>
                                        <div class="methods-list">
                            `;
                            
                            platform.methods.forEach(method => {
                                html += `<span class="method-tag">${method}</span>`;
                            });
                            
                            html += `
                                        </div>
                                    </div>
                                </div>
                            `;
                        });
                        
                        html += `
                                </div>
                            </div>
                        `;
                    }
                    
                    html += '</div>';
                }

                resultsSection.innerHTML = html;
                resultsSection.classList.add('visible');
                
                // Smooth scroll to results
                resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }

            function getCategoryIcon(category) {
                const icons = {
                    'Content Management Systems': 'fas fa-cogs',
                    'E-commerce Platforms': 'fas fa-shopping-cart',
                    'JavaScript Frameworks': 'fab fa-js-square',
                    'CSS Frameworks': 'fas fa-paint-brush',
                    'JavaScript Libraries': 'fas fa-book',
                    'Other Technologies': 'fas fa-tools'
                };
                return icons[category] || 'fas fa-cog';
            }

            function showError(message) {
                const resultsSection = document.getElementById('resultsSection');
                resultsSection.innerHTML = `
                    <div class="category-card" style="text-align: center; border-left: 4px solid #e53e3e;">
                        <div class="category-header" style="justify-content: center;">
                            <div class="category-icon" style="background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%);">
                                <i class="fas fa-exclamation-triangle"></i>
                            </div>
                            <h3 class="category-title">Analysis Failed</h3>
                        </div>
                        <p style="color: #718096; margin-bottom: 20px;">${message}</p>
                        <button class="new-analysis-btn" onclick="newAnalysis()" style="margin: 0 auto;">
                            <i class="fas fa-redo"></i>
                            Try Again
                        </button>
                    </div>
                `;
                resultsSection.classList.add('visible');
            }

            function setUrl(url) {
                document.getElementById('urlInput').value = url;
                analyzeWebsite();
            }

            function newAnalysis() {
                document.getElementById('urlInput').value = '';
                document.getElementById('urlInput').focus();
                document.getElementById('resultsSection').classList.remove('visible');
            }

            // Enter key support
            document.getElementById('urlInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    analyzeWebsite();
                }
            });

            // Auto-focus on input
            document.getElementById('urlInput').focus();
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