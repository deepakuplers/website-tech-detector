class TechAnalyzer {
    constructor() {
        this.initializeElements();
        this.attachEventListeners();
    }

    initializeElements() {
        // Form elements
        this.analyzeForm = document.getElementById('analyzeForm');
        this.urlInput = document.getElementById('urlInput');
        this.analyzeBtn = document.getElementById('analyzeBtn');
        
        // Section elements
        this.searchSection = document.getElementById('searchSection');
        this.loadingSection = document.getElementById('loadingSection');
        this.resultsSection = document.getElementById('resultsSection');
        this.errorSection = document.getElementById('errorSection');
        
        // Results elements
        this.analyzedUrl = document.getElementById('analyzedUrl');
        this.statusBadge = document.getElementById('statusBadge');
        this.resultsGrid = document.getElementById('resultsGrid');
        this.metaInfo = document.getElementById('metaInfo');
        this.headersInfo = document.getElementById('headersInfo');
        
        // Button elements
        this.newAnalysisBtn = document.getElementById('newAnalysisBtn');
        this.retryBtn = document.getElementById('retryBtn');
        
        // Loading elements
        this.loadingText = document.getElementById('loadingText');
        
        // Error elements
        this.errorMessage = document.getElementById('errorMessage');
        
        // Example links
        this.exampleLinks = document.querySelectorAll('.example-link');
    }

    attachEventListeners() {
        // Form submission
        this.analyzeForm.addEventListener('submit', (e) => this.handleAnalyze(e));
        
        // Button clicks
        this.newAnalysisBtn.addEventListener('click', () => this.showSearchSection());
        this.retryBtn.addEventListener('click', () => this.showSearchSection());
        
        // Example links
        this.exampleLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                const url = e.target.getAttribute('data-url');
                this.urlInput.value = url;
                this.handleAnalyze(e);
            });
        });

        // Enter key on input
        this.urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleAnalyze(e);
            }
        });
    }

    async handleAnalyze(e) {
        e.preventDefault();
        
        const url = this.urlInput.value.trim();
        if (!url) {
            this.showError('Please enter a valid URL');
            return;
        }

        this.showLoadingSection();
        this.startLoadingAnimation();

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            });

            const result = await response.json();
            
            if (result.success) {
                this.showResults(result);
            } else {
                this.showError(result.error || 'Analysis failed. Please try again.');
            }
        } catch (error) {
            console.error('Analysis error:', error);
            this.showError('Network error. Please check your connection and try again.');
        }
    }

    showSearchSection() {
        this.hideAllSections();
        this.searchSection.classList.remove('hidden');
        this.urlInput.focus();
    }

    showLoadingSection() {
        this.hideAllSections();
        this.loadingSection.classList.remove('hidden');
    }

    showResults(result) {
        this.hideAllSections();
        this.resultsSection.classList.remove('hidden');
        
        // Set URL and status
        this.analyzedUrl.textContent = result.url;
        this.statusBadge.textContent = `Status: ${result.status_code || 'Success'}`;
        this.statusBadge.className = 'status-badge';
        
        // Generate results grid
        this.generateResultsGrid(result.categories);
        
        // Generate meta info
        if (result.meta_info && Object.keys(result.meta_info).length > 0) {
            this.generateMetaInfo(result.meta_info);
        } else {
            this.metaInfo.style.display = 'none';
        }
        
        // Generate headers info
        this.generateHeadersInfo(result.headers);
        
        // Scroll to results
        this.resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    showError(message) {
        this.hideAllSections();
        this.errorSection.classList.remove('hidden');
        this.errorMessage.textContent = message;
    }

    hideAllSections() {
        this.searchSection.classList.add('hidden');
        this.loadingSection.classList.add('hidden');
        this.resultsSection.classList.add('hidden');
        this.errorSection.classList.add('hidden');
    }

    startLoadingAnimation() {
        const messages = [
            'Scanning for technologies...',
            'Analyzing HTTP headers...',
            'Checking HTML content...',
            'Testing common paths...',
            'Detecting frameworks...',
            'Finalizing results...'
        ];
        
        let messageIndex = 0;
        const messageInterval = setInterval(() => {
            if (this.loadingSection.classList.contains('hidden')) {
                clearInterval(messageInterval);
                return;
            }
            
            this.loadingText.textContent = messages[messageIndex];
            messageIndex = (messageIndex + 1) % messages.length;
        }, 800);
    }

    generateResultsGrid(categories) {
        if (!categories || Object.keys(categories).length === 0) {
            this.resultsGrid.innerHTML = `
                <div class="category-card">
                    <div class="category-header">
                        <div class="category-icon other-icon">
                            <i class="fas fa-question"></i>
                        </div>
                        <h3 class="category-title">No Technologies Detected</h3>
                    </div>
                    <p>We couldn't detect any specific technologies for this website. This might be due to heavy customization or privacy measures.</p>
                </div>
            `;
            return;
        }

        const categoryIcons = {
            'CMS & Platforms': 'fas fa-cogs cms-icon',
            'E-commerce': 'fas fa-shopping-cart ecommerce-icon',
            'JavaScript Frameworks': 'fab fa-js-square framework-icon',
            'CSS Frameworks': 'fas fa-paint-brush css-icon',
            'JavaScript Libraries': 'fas fa-book js-icon',
            'Other Technologies': 'fas fa-tools other-icon'
        };

        let html = '';
        
        for (const [categoryName, technologies] of Object.entries(categories)) {
            const iconClass = categoryIcons[categoryName] || 'fas fa-cog other-icon';
            const [iconName, colorClass] = iconClass.split(' ').slice(-2);
            
            html += `
                <div class="category-card">
                    <div class="category-header">
                        <div class="category-icon ${colorClass}">
                            <i class="${iconClass.split(' ').slice(0, -1).join(' ')}"></i>
                        </div>
                        <h3 class="category-title">${categoryName}</h3>
                    </div>
                    <ul class="tech-list">
            `;
            
            technologies.forEach(tech => {
                html += `
                    <li class="tech-item">
                        <span class="tech-name">${tech.name}</span>
                        <span class="tech-method">${tech.method}</span>
                    </li>
                `;
            });
            
            html += `
                    </ul>
                </div>
            `;
        }
        
        this.resultsGrid.innerHTML = html;
    }

    generateMetaInfo(metaInfo) {
        let html = `
            <h4>
                <i class="fas fa-info-circle"></i>
                Meta Information
            </h4>
        `;
        
        for (const [key, value] of Object.entries(metaInfo)) {
            html += `
                <div class="info-item">
                    <span class="info-label">${key}</span>
                    <span class="info-value">${value}</span>
                </div>
            `;
        }
        
        this.metaInfo.innerHTML = html;
        this.metaInfo.style.display = 'block';
    }

    generateHeadersInfo(headers) {
        let html = `
            <h4>
                <i class="fas fa-server"></i>
                HTTP Headers
            </h4>
        `;
        
        const importantHeaders = ['server', 'x-powered-by', 'x-framework', 'content-type', 'x-generator'];
        const filteredHeaders = {};
        
        // First, add important headers
        importantHeaders.forEach(header => {
            if (headers[header]) {
                filteredHeaders[header] = headers[header];
            }
        });
        
        // Add any other interesting headers
        Object.keys(headers).forEach(header => {
            const lowerHeader = header.toLowerCase();
            if (!importantHeaders.includes(lowerHeader) && 
                (lowerHeader.startsWith('x-') || 
                 ['vary', 'cache-control', 'expires'].includes(lowerHeader))) {
                filteredHeaders[header] = headers[header];
            }
        });
        
        if (Object.keys(filteredHeaders).length === 0) {
            html += '<p>No significant headers detected.</p>';
        } else {
            Object.entries(filteredHeaders).forEach(([key, value]) => {
                html += `
                    <div class="info-item">
                        <span class="info-label">${key}</span>
                        <span class="info-value">${value}</span>
                    </div>
                `;
            });
        }
        
        this.headersInfo.innerHTML = html;
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TechAnalyzer();
});

// Add some utility functions
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        // Could add a toast notification here
        console.log('Copied to clipboard:', text);
    });
}

function formatUrl(url) {
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        return 'https://' + url;
    }
    return url;
}