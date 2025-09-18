#!/usr/bin/env python3
"""
Flask Web Application for Website Technology Detector
Professional UI for analyzing website technologies
"""

from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup
import re
import json
import time
from urllib.parse import urlparse, urljoin
import threading

app = Flask(__name__)

class WebTechDetector:
    def __init__(self):
        # Same comprehensive signatures as before but organized for web
        self.signatures = {
            'WordPress': {
                'headers': [r'wp-json', r'wordpress'],
                'html': [r'/wp-content/', r'/wp-includes/', r'/wp-admin/', r'wp-json', r'wp_enqueue_script', 
                        r'wp-embed', r'wpml-', r'woocommerce', r'wp-block-', r'has-text-align', 
                        r'wp-image-\d+', r'attachment-\d+', r'size-\w+', r'wp-caption'],
                'meta': [r'<meta name="generator" content="WordPress'],
                'paths': ['/wp-json/wp/v2/', '/wp-admin/', '/wp-login.php', '/xmlrpc.php'],
                'css_classes': [r'wp-', r'post-\d+', r'page-id-\d+', r'category-', r'tag-'],
                'js_vars': [r'wp\.', r'wpAjax', r'wc_', r'wordpress']
            },
            'Shopify': {
                'headers': [r'shopify'],
                'html': [r'cdn\.shopify\.com', r'shopify\.theme', r'/assets/shopify_', 
                        r'shopify-checkout', r'Shopify\.routes', r'shop\.myshopify\.com'],
                'paths': ['/cart.js', '/products.json', '/collections.json'],
                'css_classes': [r'shopify-'],
                'js_vars': [r'Shopify\.', r'ShopifyAPI']
            },
            'Drupal': {
                'headers': [r'drupal', r'x-drupal'],
                'html': [r'/sites/default/', r'/modules/', r'/themes/', r'drupal\.settings', 
                        r'drupal-ajax', r'/core/themes/', r'data-drupal-'],
                'meta': [r'<meta name="generator" content="Drupal'],
                'paths': ['/node/', '/admin/', '/user/login'],
                'css_classes': [r'drupal-', r'node-', r'field-'],
                'js_vars': [r'Drupal\.', r'drupalSettings']
            },
            'Next.js': {
                'headers': [r'next\.js', r'next'],
                'html': [r'_next/', r'__NEXT_DATA__', r'next\.js', r'nextjs', r'/_next/static/'],
                'js_vars': [r'__NEXT_', r'Next\.']
            },
            'React': {
                'html': [r'react\.js', r'data-reactroot', r'__REACT_DEVTOOLS_GLOBAL_HOOK__', 
                        r'react-dom', r'/static/js/.*\.js'],
                'js_vars': [r'React\.', r'ReactDOM\.']
            },
            'WooCommerce': {
                'html': [r'woocommerce', r'/wc-ajax/', r'wc-setup', r'wc-', r'shop_table', 
                        r'woocommerce-', r'product_cat-', r'wc_single_product'],
                'css_classes': [r'woocommerce', r'wc-', r'product-'],
                'js_vars': [r'wc_', r'woocommerce']
            },
            'Bootstrap': {
                'html': [r'bootstrap\.css', r'bootstrap\.min\.css'],
                'css_classes': [r'col-', r'btn', r'container', r'row']
            },
            'Tailwind CSS': {
                'html': [r'tailwindcss', r'tailwind\.css'],
                'css_classes': [r'flex', r'g-\w+', r'text-\w+', r'p-\d+', r'm-\d+']
            },
            'jQuery': {
                'html': [r'jquery', r'jQuery'],
                'js_vars': [r'\$\(', r'jQuery']
            }
        }

    def analyze_website_web(self, url):
        """Web-optimized analysis with progress tracking"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            session = requests.Session()
            session.headers.update(headers)
            
            response = session.get(url, timeout=15, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            detected_tech = {}
            
            # Run all detection methods
            detected_tech.update(self._analyze_headers(response.headers))
            detected_tech.update(self._analyze_html(response.text))
            detected_tech.update(self._analyze_meta_tags(soup))
            detected_tech.update(self._analyze_resources(soup))
            detected_tech.update(self._analyze_css_classes(soup))
            detected_tech.update(self._analyze_js_variables(soup))
            detected_tech.update(self._test_paths(url, session))
            
            # Categorize results
            result = self._categorize_results(detected_tech, response.headers, url)
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

    def _analyze_headers(self, headers):
        detected = {}
        for header_name, header_value in headers.items():
            header_lower = header_value.lower()
            for tech, patterns in self.signatures.items():
                if 'headers' in patterns:
                    for pattern in patterns['headers']:
                        if re.search(pattern, header_lower):
                            detected[tech] = f"HTTP header"
        return detected

    def _analyze_html(self, html_content):
        detected = {}
        for tech, patterns in self.signatures.items():
            if 'html' in patterns:
                for pattern in patterns['html']:
                    if re.search(pattern, html_content, re.IGNORECASE):
                        detected[tech] = "HTML content"
                        break
        return detected

    def _analyze_meta_tags(self, soup):
        detected = {}
        generator = soup.find('meta', attrs={'name': 'generator'})
        if generator and generator.get('content'):
            content = generator.get('content')
            detected['Generator Meta'] = content
            for tech, patterns in self.signatures.items():
                if 'meta' in patterns:
                    for pattern in patterns['meta']:
                        if re.search(pattern, f'<meta name="generator" content="{content}"', re.IGNORECASE):
                            detected[tech] = "Meta tag"
        return detected

    def _analyze_resources(self, soup):
        detected = {}
        resources = []
        for script in soup.find_all('script', src=True):
            resources.append(script.get('src'))
        for link in soup.find_all('link', href=True):
            resources.append(link.get('href'))
            
        for resource_url in resources:
            if resource_url:
                for tech, patterns in self.signatures.items():
                    if 'html' in patterns:
                        for pattern in patterns['html']:
                            if re.search(pattern, resource_url, re.IGNORECASE):
                                detected[tech] = "Resource URL"
                                break
        return detected

    def _analyze_css_classes(self, soup):
        detected = {}
        all_classes = []
        for element in soup.find_all(class_=True):
            if isinstance(element.get('class'), list):
                all_classes.extend(element.get('class'))
            else:
                all_classes.append(element.get('class'))
        
        class_string = ' '.join(all_classes)
        for tech, patterns in self.signatures.items():
            if 'css_classes' in patterns:
                for pattern in patterns['css_classes']:
                    if re.search(pattern, class_string):
                        detected[tech] = "CSS classes"
                        break
        return detected

    def _analyze_js_variables(self, soup):
        detected = {}
        scripts = soup.find_all('script')
        script_content = ' '.join([script.string or '' for script in scripts])
        
        for tech, patterns in self.signatures.items():
            if 'js_vars' in patterns:
                for pattern in patterns['js_vars']:
                    if re.search(pattern, script_content):
                        detected[tech] = "JavaScript"
                        break
        return detected

    def _test_paths(self, base_url, session):
        detected = {}
        for tech, patterns in self.signatures.items():
            if 'paths' in patterns:
                for path in patterns['paths']:
                    try:
                        test_url = urljoin(base_url, path)
                        response = session.head(test_url, timeout=5)
                        if response.status_code in [200, 301, 302, 403]:
                            detected[tech] = f"Path test"
                            break
                    except:
                        continue
        return detected

    def _categorize_results(self, detected_tech, headers, url):
        categories = {
            'CMS & Platforms': ['WordPress', 'Drupal', 'Joomla', 'Ghost', 'Contentful'],
            'E-commerce': ['Shopify', 'WooCommerce', 'Magento', 'BigCommerce'],
            'JavaScript Frameworks': ['Next.js', 'React', 'Vue.js', 'Angular'],
            'CSS Frameworks': ['Bootstrap', 'Tailwind CSS', 'Foundation'],
            'JavaScript Libraries': ['jQuery', 'D3.js', 'Chart.js'],
            'Other Technologies': []
        }
        
        result_categories = {}
        all_categorized = []
        
        for category_name, tech_list in categories.items():
            found_techs = []
            for tech in tech_list:
                if tech in detected_tech:
                    found_techs.append({
                        'name': tech,
                        'method': detected_tech[tech]
                    })
                    all_categorized.append(tech)
            
            if found_techs:
                result_categories[category_name] = found_techs
        
        # Add other detected technologies
        other_techs = []
        for tech, method in detected_tech.items():
            if tech not in all_categorized and not tech.endswith('Meta'):
                other_techs.append({
                    'name': tech,
                    'method': method
                })
        
        if other_techs:
            result_categories['Other Technologies'] = other_techs
        
        return {
            'categories': result_categories,
            'headers': dict(headers),
            'url': url,
            'meta_info': {k: v for k, v in detected_tech.items() if k.endswith('Meta')}
        }

# Initialize detector
detector = WebTechDetector()

@app.route('/')
def index():
    return render_template('index.html')

# ADD THIS NEW ROUTE
@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'})
        
        print(f"Analyzing URL: {url}")  # Debug print
        
        # Run analysis
        result = detector.analyze_website_web(url)
        
        print(f"Analysis result: {result}")  # Debug print
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in analyze route: {str(e)}")  # Debug print
        return jsonify({
            'success': False, 
            'error': f'Server error: {str(e)}',
            'categories': {},
            'headers': {}
        })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
