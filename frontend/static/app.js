/**
 * Alpine.js component for iGaming News Aggregator
 */

function newsApp() {
    return {
        // State - Articles
        articles: [],
        sources: [],
        totalArticles: 0,
        selectedSource: '',
        limit: 20,
        offset: 0,

        // State - Digest
        digest: '',
        digestDate: '',
        digestArticleCount: 0,

        // State - View
        currentView: 'feed', // 'feed' or 'digest'

        // State - Search
        searchQuery: '',
        activeSearchQuery: '',
        isSearchActive: false,
        searchResultsCount: 0,
        loadingSearch: false,

        // Loading states
        loadingArticles: false,
        loadingFetch: false,
        loadingSummaries: false,
        loadingDigest: false,

        // Messages
        message: '',
        messageType: 'success', // 'success' or 'error'

        // API base URL - auto-detect
        apiUrl: window.location.origin + '/api',

        /**
         * Initialize the app
         */
        async init() {
            console.log('iGaming News Aggregator initialized');
            console.log('API URL:', this.apiUrl);
            await this.loadSources();
            await this.loadArticles();
        },

        /**
         * Load articles from API
         */
        async loadArticles() {
            this.loadingArticles = true;
            try {
                let url = `${this.apiUrl}/articles?limit=${this.limit}&offset=${this.offset}`;

                if (this.selectedSource) {
                    url += `&source=${encodeURIComponent(this.selectedSource)}`;
                }

                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                this.articles = data.articles || [];
                this.totalArticles = data.total || 0;

                console.log(`Loaded ${this.articles.length} articles`);
            } catch (error) {
                console.error('Error loading articles:', error);
                this.showMessage('Failed to load articles: ' + error.message, 'error');
            } finally {
                this.loadingArticles = false;
            }
        },

        /**
         * Load available sources
         */
        async loadSources() {
            try {
                const response = await fetch(`${this.apiUrl}/sources`);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();
                this.sources = data.sources || [];

                console.log(`Loaded ${this.sources.length} sources`);
            } catch (error) {
                console.error('Error loading sources:', error);
            }
        },

        /**
         * Fetch latest news from RSS feeds
         */
        async fetchNews() {
            this.loadingFetch = true;
            try {
                const response = await fetch(`${this.apiUrl}/fetch-news`, {
                    method: 'POST'
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();

                this.showMessage(
                    `Successfully fetched ${data.new_articles} new articles!`,
                    'success'
                );

                // Reload articles
                await this.loadArticles();
            } catch (error) {
                console.error('Error fetching news:', error);
                this.showMessage('Failed to fetch news: ' + error.message, 'error');
            } finally {
                this.loadingFetch = false;
            }
        },

        /**
         * Generate summaries for articles
         */
        async generateSummaries() {
            this.loadingSummaries = true;
            try {
                const response = await fetch(`${this.apiUrl}/generate-summaries`, {
                    method: 'POST'
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();

                this.showMessage(
                    `Successfully generated ${data.summaries_generated} summaries!`,
                    'success'
                );

                // Reload articles to show updated summaries
                await this.loadArticles();
            } catch (error) {
                console.error('Error generating summaries:', error);
                this.showMessage('Failed to generate summaries: ' + error.message, 'error');
            } finally {
                this.loadingSummaries = false;
            }
        },

        /**
         * Create daily digest
         */
        async createDigest() {
            this.loadingDigest = true;
            try {
                const response = await fetch(`${this.apiUrl}/create-digest`, {
                    method: 'POST'
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP ${response.status}`);
                }

                const data = await response.json();

                this.digest = data.digest;
                this.digestDate = this.formatDigestDate(data.digest_date);
                this.digestArticleCount = data.article_count;

                this.showMessage('Daily digest created successfully!', 'success');
            } catch (error) {
                console.error('Error creating digest:', error);
                this.showMessage('Failed to create digest: ' + error.message, 'error');
            } finally {
                this.loadingDigest = false;
            }
        },

        /**
         * Show message to user
         */
        showMessage(text, type = 'success') {
            this.message = text;
            this.messageType = type;

            // Auto-hide after 5 seconds
            setTimeout(() => {
                this.message = '';
            }, 5000);
        },

        /**
         * Format markdown-style text (convert **bold** to HTML)
         */
        formatMarkdown(text) {
            if (!text) return '';

            // Convert **bold** to <strong>bold</strong>
            return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        },

        /**
         * Get similarity badge class based on score
         */
        getSimilarityBadgeClass(score) {
            if (score >= 0.85) return 'bg-green-500 text-white'; // High match
            if (score >= 0.70) return 'bg-yellow-500 text-black'; // Medium match
            return 'bg-gray-400 text-white'; // Low match
        },

        /**
         * Format similarity score as percentage
         */
        formatSimilarityScore(score) {
            return Math.round(score * 100) + '% match';
        },

        /**
         * Format date for display (relative time)
         */
        formatDate(dateString) {
            if (!dateString) return 'No date';

            try {
                const date = new Date(dateString);
                const now = new Date();
                const diffMs = now - date;
                const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
                const diffDays = Math.floor(diffHours / 24);

                if (diffHours < 1) return 'Just now';
                if (diffHours < 24) return `${diffHours}h ago`;
                if (diffDays < 7) return `${diffDays}d ago`;

                return date.toLocaleDateString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
                });
            } catch (error) {
                return 'Invalid date';
            }
        },

        /**
         * Format digest date
         */
        formatDigestDate(dateString) {
            if (!dateString) return '';

            try {
                const date = new Date(dateString);
                return date.toLocaleDateString('en-US', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });
            } catch (error) {
                return dateString;
            }
        },

        /**
         * Format digest content (convert markdown-like formatting to HTML)
         */
        formatDigest(content) {
            if (!content) return '';

            // Simple formatting - convert markdown-style headers and bold text
            let formatted = content
                // Headers
                .replace(/## (.*?)(\n|$)/g, '<h2 class="text-lg font-bold mt-4 mb-2 text-gray-900">$1</h2>')
                .replace(/### (.*?)(\n|$)/g, '<h3 class="text-base font-semibold mt-3 mb-2 text-gray-800">$1</h3>')
                // Bold text
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                // Line breaks
                .replace(/\n\n/g, '</p><p class="mb-2">')
                .replace(/\n/g, '<br>');

            return '<p class="mb-2">' + formatted + '</p>';
        },

        /**
         * Format digest with category-colored borders
         */
        formatDigestWithCategories(content) {
            if (!content) return '';

            // Define category color mappings
            const categoryColors = {
                'regulation': 'border-l-4 border-blue-500 pl-4',
                'compliance': 'border-l-4 border-blue-500 pl-4',
                'merger': 'border-l-4 border-green-500 pl-4',
                'acquisition': 'border-l-4 border-green-500 pl-4',
                'partnership': 'border-l-4 border-green-500 pl-4',
                'deal': 'border-l-4 border-green-500 pl-4',
                'product': 'border-l-4 border-purple-500 pl-4',
                'launch': 'border-l-4 border-purple-500 pl-4',
                'market': 'border-l-4 border-orange-500 pl-4',
                'expansion': 'border-l-4 border-orange-500 pl-4',
            };

            // Split content by ## headers (main sections)
            let sections = content.split(/(?=##\s)/g);

            let formattedSections = sections.map(section => {
                if (!section.trim()) return '';

                // Determine border color based on section title
                let borderClass = 'border-l-4 border-gray-300 pl-4';
                const lowerSection = section.toLowerCase();

                for (const [keyword, colorClass] of Object.entries(categoryColors)) {
                    if (lowerSection.includes(keyword)) {
                        borderClass = colorClass;
                        break;
                    }
                }

                // Format the section
                let formatted = section
                    // H2 headers
                    .replace(/## (.*?)(\n|$)/g, '<h2 class="text-xl font-bold mb-3 text-black">$1</h2>')
                    // H3 headers
                    .replace(/### (.*?)(\n|$)/g, '<h3 class="text-base font-semibold mt-3 mb-2 text-gray-800">$1</h3>')
                    // Bold text
                    .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>')
                    // Bullet points
                    .replace(/^- (.*?)$/gm, '<li class="ml-4">$1</li>')
                    // Paragraphs
                    .replace(/\n\n/g, '</p><p class="mb-3 text-gray-700 text-sm leading-relaxed">')
                    .replace(/\n/g, '<br>');

                // Wrap in section div with border
                return `<div class="${borderClass} mb-6"><p class="mb-3 text-gray-700 text-sm leading-relaxed">${formatted}</p></div>`;
            });

            return formattedSections.join('');
        },

        /**
         * Pagination - next page
         */
        nextPage() {
            this.offset += this.limit;
            this.loadArticles();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        },

        /**
         * Pagination - previous page
         */
        previousPage() {
            if (this.offset > 0) {
                this.offset = Math.max(0, this.offset - this.limit);
                this.loadArticles();
                window.scrollTo({ top: 0, behavior: 'smooth' });
            }
        },

        /**
         * Perform semantic search
         */
        async performSearch() {
            const query = this.searchQuery.trim();

            if (!query) {
                this.showMessage('Please enter a search query', 'error');
                return;
            }

            this.loadingSearch = true;

            try {
                const response = await fetch(`${this.apiUrl}/search`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        query: query,
                        limit: 20
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();

                // Update articles with search results
                this.articles = data.results || [];
                this.totalArticles = data.count || 0;
                this.isSearchActive = true;
                this.activeSearchQuery = query;
                this.searchResultsCount = data.count || 0;

                console.log(`Search completed: ${this.searchResultsCount} results`);

                if (this.searchResultsCount === 0) {
                    const message = data.message || `No results found for "${query}"`;
                    this.showMessage(message, 'error');
                }

            } catch (error) {
                console.error('Error during search:', error);
                this.showMessage('Search failed: ' + error.message, 'error');
            } finally {
                this.loadingSearch = false;
            }
        },

        /**
         * Clear search and return to normal view
         */
        clearSearch() {
            this.searchQuery = '';
            this.activeSearchQuery = '';
            this.isSearchActive = false;
            this.searchResultsCount = 0;
            this.offset = 0;

            // Reload normal articles
            this.loadArticles();
        }
    };
}
