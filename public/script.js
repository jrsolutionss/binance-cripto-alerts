// JavaScript for Crypto Alerts Dashboard
class CryptoDashboard {
    constructor() {
        this.data = {
            top100: [],
            marketSummary: {},
            crossovers: [],
            filteredData: []
        };
        
        this.autoRefresh = false;
        this.refreshInterval = null;
        this.currentSort = { column: 'rank', direction: 'asc' };
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.updateStatus('Initializing dashboard...', 'loading');
    }
    
    setupEventListeners() {
        // Search functionality
        document.getElementById('search-input').addEventListener('input', 
            this.debounce(this.handleSearch.bind(this), 300));
        document.getElementById('search-btn').addEventListener('click', this.handleSearch.bind(this));
        
        // Filters
        document.getElementById('filter-change').addEventListener('change', this.applyFilters.bind(this));
        document.getElementById('filter-crossover').addEventListener('change', this.applyFilters.bind(this));
        
        // Control buttons
        document.getElementById('refresh-btn').addEventListener('click', this.refreshData.bind(this));
        document.getElementById('auto-refresh-btn').addEventListener('click', this.toggleAutoRefresh.bind(this));
        
        // Modal controls
        const modal = document.getElementById('analysis-modal');
        document.querySelector('.close').addEventListener('click', () => {
            modal.style.display = 'none';
        });
        
        window.addEventListener('click', (event) => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
        
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });
        
        // Table sorting
        document.querySelectorAll('#crypto-table th').forEach((th, index) => {
            if (index > 0) { // Skip rank column
                th.style.cursor = 'pointer';
                th.addEventListener('click', () => this.sortTable(th.textContent.toLowerCase()));
            }
        });
    }
    
    async loadInitialData() {
        try {
            await Promise.all([
                this.fetchTop100(),
                this.fetchMarketSummary(),
                this.fetchCrossovers()
            ]);
            
            this.renderAll();
            this.updateStatus('Live - Data updated', 'success');
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.updateStatus('Error loading data', 'error');
        }
    }
    
    async refreshData() {
        this.updateStatus('Refreshing data...', 'loading');
        try {
            await this.loadInitialData();
        } catch (error) {
            this.updateStatus('Refresh failed', 'error');
        }
    }
    
    async fetchTop100() {
        const response = await fetch('/api/top100');
        const result = await response.json();
        if (result.success) {
            this.data.top100 = result.data;
            this.data.filteredData = [...this.data.top100];
        }
    }
    
    async fetchMarketSummary() {
        const response = await fetch('/api/market-summary');
        const result = await response.json();
        if (result.success) {
            this.data.marketSummary = result;
        }
    }
    
    async fetchCrossovers() {
        const response = await fetch('/api/crossovers?count=50');
        const result = await response.json();
        if (result.success) {
            this.data.crossovers = result.crossovers.all;
        }
    }
    
    renderAll() {
        this.renderMarketSummary();
        this.renderTable();
        this.renderCrossovers();
        this.renderTopMovers();
        this.updateLastUpdate();
    }
    
    renderMarketSummary() {
        const summary = this.data.marketSummary;
        
        if (summary.market_overview) {
            // Market strength
            document.getElementById('market-strength').textContent = 
                this.formatMarketStrength(summary.market_overview.market_strength);
            
            // Sentiment bars
            const sentiment = summary.market_overview.market_sentiment || {};
            this.updateProgressBar('ma20-progress', 'ma20-percent', sentiment.above_ma20_pct);
            this.updateProgressBar('ma50-progress', 'ma50-percent', sentiment.above_ma50_pct);
            this.updateProgressBar('ma200-progress', 'ma200-percent', sentiment.above_ma200_pct);
            
            // Market stats
            document.getElementById('avg-change').textContent = 
                this.formatPercentage(summary.market_overview.average_change_24h);
            document.getElementById('total-volume').textContent = 
                this.formatCurrency(summary.market_overview.total_volume_24h);
        }
        
        if (summary.crossover_analysis) {
            document.getElementById('golden-crosses').textContent = 
                summary.crossover_analysis.golden_crosses || 0;
            document.getElementById('death-crosses').textContent = 
                summary.crossover_analysis.death_crosses || 0;
            document.getElementById('total-crossovers').textContent = 
                summary.crossover_analysis.total_crossovers || 0;
        }
    }
    
    renderTable() {
        const tbody = document.getElementById('crypto-table-body');
        const loading = document.getElementById('table-loading');
        
        if (this.data.filteredData.length === 0) {
            loading.style.display = 'flex';
            tbody.innerHTML = '';
            return;
        }
        
        loading.style.display = 'none';
        tbody.innerHTML = this.data.filteredData.map(crypto => `
            <tr>
                <td>${crypto.rank}</td>
                <td class="symbol-cell">${crypto.symbol}</td>
                <td class="price-cell">$${this.formatNumber(crypto.price)}</td>
                <td class="${crypto.change_24h >= 0 ? 'change-positive' : 'change-negative'}">
                    ${this.formatPercentage(crypto.change_24h)}
                </td>
                <td>$${this.formatLargeNumber(crypto.quote_volume_24h)}</td>
                <td>
                    <div class="ma-indicators">
                        ${this.renderMAIndicators(crypto)}
                    </div>
                </td>
                <td>
                    <div class="crossover-badges">
                        ${this.renderCrossoverBadges(crypto)}
                    </div>
                </td>
                <td>
                    <button class="action-btn" onclick="dashboard.showAnalysis('${crypto.symbol}')">
                        Analyze
                    </button>
                </td>
            </tr>
        `).join('');
    }
    
    renderMAIndicators(crypto) {
        // This would need MA data from analysis endpoint
        // For now, show placeholder based on price trends
        const indicators = ['20', '50', '200'];
        return indicators.map(period => {
            const isAbove = Math.random() > 0.5; // Placeholder logic
            return `<span class="ma-indicator ${isAbove ? 'above' : 'below'}">${period}</span>`;
        }).join('');
    }
    
    renderCrossoverBadges(crypto) {
        const crossovers = this.data.crossovers.filter(c => c.symbol === crypto.symbol);
        return crossovers.slice(0, 2).map(crossover => `
            <span class="crossover-badge ${crossover.type === 'GOLDEN_CROSS' ? 'golden' : 'death'}">
                ${crossover.type === 'GOLDEN_CROSS' ? '🟢 Golden' : '🔴 Death'}
            </span>
        `).join('');
    }
    
    renderCrossovers() {
        const container = document.getElementById('crossovers-container');
        container.innerHTML = this.data.crossovers.slice(0, 12).map(crossover => `
            <div class="crossover-card">
                <div class="crossover-header">
                    <span class="crossover-symbol">${crossover.symbol}</span>
                    <span class="crossover-type ${crossover.type === 'GOLDEN_CROSS' ? 'golden' : 'death'}">
                        ${crossover.type === 'GOLDEN_CROSS' ? '🟢 Golden Cross' : '🔴 Death Cross'}
                    </span>
                </div>
                <div class="crossover-details">
                    <div><strong>${crossover.crossover_name}</strong></div>
                    <div>Fast MA: $${this.formatNumber(crossover.fast_ma_value)}</div>
                    <div>Slow MA: $${this.formatNumber(crossover.slow_ma_value)}</div>
                    <div>Signal Strength: ${this.formatPercentage(crossover.signal_strength)}</div>
                    <div>Time: ${new Date(crossover.timestamp).toLocaleString()}</div>
                </div>
            </div>
        `).join('');
    }
    
    renderTopMovers() {
        if (!this.data.marketSummary.top_movers) return;
        
        const gainersContainer = document.getElementById('top-gainers');
        const losersContainer = document.getElementById('top-losers');
        
        const gainers = this.data.marketSummary.top_movers.gainers || [];
        const losers = this.data.marketSummary.top_movers.losers || [];
        
        gainersContainer.innerHTML = gainers.map(gainer => `
            <div class="mover-item">
                <div>
                    <div class="mover-symbol">${gainer.symbol}</div>
                    <div style="font-size: 11px; color: var(--text-secondary);">
                        $${this.formatNumber(gainer.price)}
                    </div>
                </div>
                <div class="mover-change positive">+${this.formatPercentage(gainer.change_24h)}</div>
            </div>
        `).join('');
        
        losersContainer.innerHTML = losers.map(loser => `
            <div class="mover-item">
                <div>
                    <div class="mover-symbol">${loser.symbol}</div>
                    <div style="font-size: 11px; color: var(--text-secondary);">
                        $${this.formatNumber(loser.price)}
                    </div>
                </div>
                <div class="mover-change negative">${this.formatPercentage(loser.change_24h)}</div>
            </div>
        `).join('');
    }
    
    async showAnalysis(symbol) {
        const modal = document.getElementById('analysis-modal');
        const symbolEl = document.getElementById('modal-symbol');
        const contentEl = document.getElementById('analysis-content');
        
        symbolEl.textContent = symbol;
        contentEl.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading analysis...</p></div>';
        modal.style.display = 'block';
        
        try {
            const response = await fetch(`/api/analysis?symbol=${symbol}&days=100`);
            const result = await response.json();
            
            if (result.success) {
                this.renderAnalysisContent(result);
            } else {
                contentEl.innerHTML = `<p>Error loading analysis: ${result.message}</p>`;
            }
        } catch (error) {
            contentEl.innerHTML = `<p>Error loading analysis: ${error.message}</p>`;
        }
    }
    
    renderAnalysisContent(analysisData) {
        const contentEl = document.getElementById('analysis-content');
        const analysis = analysisData.analysis;
        const crossovers = analysisData.crossovers;
        
        // Show overview tab by default
        contentEl.innerHTML = `
            <div class="analysis-section">
                <h3>Current Price: $${this.formatNumber(analysis.current_price)}</h3>
                <p><strong>Data Points:</strong> ${analysis.data_points}</p>
                <p><strong>Last Updated:</strong> ${new Date(analysis.timestamp).toLocaleString()}</p>
                
                <h4>Moving Averages</h4>
                <div class="ma-summary">
                    ${Object.entries(analysis.moving_averages || {}).map(([key, ma]) => `
                        <div class="ma-row">
                            <strong>MA ${ma.period}:</strong>
                            SMA $${ma.sma_value ? this.formatNumber(ma.sma_value) : 'N/A'} |
                            EMA $${ma.ema_value ? this.formatNumber(ma.ema_value) : 'N/A'}
                            <span class="${ma.price_vs_sma === 'above' ? 'change-positive' : 'change-negative'}">
                                (Price is ${ma.price_vs_sma} SMA)
                            </span>
                        </div>
                    `).join('')}
                </div>
                
                <h4>Recent Crossovers</h4>
                <div class="crossovers-summary">
                    ${crossovers.length > 0 ? crossovers.map(crossover => `
                        <div class="crossover-item">
                            <span class="crossover-badge ${crossover.type === 'GOLDEN_CROSS' ? 'golden' : 'death'}">
                                ${crossover.type === 'GOLDEN_CROSS' ? '🟢 Golden Cross' : '🔴 Death Cross'}
                            </span>
                            <div>${crossover.crossover_name}</div>
                            <div>${new Date(crossover.timestamp).toLocaleDateString()}</div>
                        </div>
                    `).join('') : '<p>No recent crossovers detected.</p>'}
                </div>
            </div>
        `;
    }
    
    handleSearch() {
        const query = document.getElementById('search-input').value.toLowerCase();
        this.applyFilters(query);
    }
    
    applyFilters(searchQuery = null) {
        const search = searchQuery || document.getElementById('search-input').value.toLowerCase();
        const changeFilter = document.getElementById('filter-change').value;
        const crossoverFilter = document.getElementById('filter-crossover').value;
        
        this.data.filteredData = this.data.top100.filter(crypto => {
            // Search filter
            const matchesSearch = !search || 
                crypto.symbol.toLowerCase().includes(search) ||
                crypto.symbol.replace('USDT', '').toLowerCase().includes(search);
            
            // Change filter
            let matchesChange = true;
            if (changeFilter === 'positive') matchesChange = crypto.change_24h >= 0;
            if (changeFilter === 'negative') matchesChange = crypto.change_24h < 0;
            
            // Crossover filter (simplified - would need actual crossover data)
            let matchesCrossover = true;
            if (crossoverFilter) {
                const hasCrossover = this.data.crossovers.some(c => c.symbol === crypto.symbol);
                matchesCrossover = hasCrossover;
            }
            
            return matchesSearch && matchesChange && matchesCrossover;
        });
        
        this.renderTable();
    }
    
    sortTable(column) {
        if (this.currentSort.column === column) {
            this.currentSort.direction = this.currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            this.currentSort.column = column;
            this.currentSort.direction = 'asc';
        }
        
        this.data.filteredData.sort((a, b) => {
            let aVal = a[column];
            let bVal = b[column];
            
            // Handle different data types
            if (typeof aVal === 'string') {
                aVal = aVal.toLowerCase();
                bVal = bVal.toLowerCase();
            }
            
            if (this.currentSort.direction === 'asc') {
                return aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
            } else {
                return aVal > bVal ? -1 : aVal < bVal ? 1 : 0;
            }
        });
        
        this.renderTable();
    }
    
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // This would update content based on tab
        // For now, keeping the same content
    }
    
    toggleAutoRefresh() {
        const btn = document.getElementById('auto-refresh-btn');
        
        if (this.autoRefresh) {
            this.autoRefresh = false;
            clearInterval(this.refreshInterval);
            btn.textContent = '⏰ Auto: OFF';
            btn.classList.remove('active');
        } else {
            this.autoRefresh = true;
            this.refreshInterval = setInterval(() => this.refreshData(), 5 * 60 * 1000); // 5 minutes
            btn.textContent = '⏰ Auto: ON';
            btn.classList.add('active');
        }
    }
    
    updateProgressBar(progressId, percentId, value) {
        const progressBar = document.getElementById(progressId);
        const percentText = document.getElementById(percentId);
        
        if (progressBar && percentText) {
            progressBar.style.width = `${value}%`;
            percentText.textContent = `${Math.round(value)}%`;
        }
    }
    
    updateStatus(message, type) {
        const statusText = document.getElementById('status-text');
        const statusDot = document.getElementById('status-dot');
        
        statusText.textContent = message;
        
        // Reset classes
        statusDot.className = 'status-dot';
        
        switch (type) {
            case 'success':
                statusDot.style.background = 'var(--success-color)';
                break;
            case 'error':
                statusDot.style.background = 'var(--danger-color)';
                break;
            case 'loading':
                statusDot.style.background = 'var(--warning-color)';
                break;
        }
    }
    
    updateLastUpdate() {
        document.getElementById('last-update').textContent = 
            new Date().toLocaleTimeString();
    }
    
    // Utility methods
    formatNumber(num) {
        if (num >= 1) {
            return num.toFixed(2);
        } else {
            return num.toFixed(6);
        }
    }
    
    formatLargeNumber(num) {
        if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
        if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
        if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
        return num.toFixed(0);
    }
    
    formatPercentage(num) {
        return `${num >= 0 ? '+' : ''}${num.toFixed(2)}%`;
    }
    
    formatCurrency(num) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(num);
    }
    
    formatMarketStrength(strength) {
        const strengthMap = {
            'very_bullish': '🟢 Very Bullish',
            'bullish': '🟢 Bullish',
            'neutral': '🟡 Neutral',
            'bearish': '🔴 Bearish',
            'very_bearish': '🔴 Very Bearish'
        };
        return strengthMap[strength] || '🟡 Neutral';
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Initialize dashboard when page loads
let dashboard;
document.addEventListener('DOMContentLoaded', () => {
    dashboard = new CryptoDashboard();
});

// Make functions available globally for onclick handlers
window.dashboard = dashboard;