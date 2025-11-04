/**
 * Alpine.js component for iGaming News Aggregator - Modern Card-Based Interface
 */

function newsApp() {
    return {
        // State - Articles
        articles: [],
        filteredArticles: [],
        breakingNews: [],
        totalArticles: 0,

        // State - Filters
        searchTerm: '',
        selectedCategory: 'all',

        // State - Modal
        selectedArticle: null,

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
            await this.loadArticles();
        },

        /**
         * Load articles from API
         */
        async loadArticles() {
            this.loadingArticles = true;
            try {
                const response = await fetch(`${this.apiUrl}/articles?limit=100&offset=0`);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                this.articles = data.articles || [];
                this.totalArticles = data.total || 0;

                // Apply filters
                this.filterArticles();

                console.log(`Loaded ${this.articles.length} articles`);
            } catch (error) {
                console.error('Error loading articles:', error);
                this.showMessage('Failed to load articles: ' + error.message, 'error');
            } finally {
                this.loadingArticles = false;
            }
        },

        /**
         * Filter articles by search term and category
         */
        filterArticles() {
            let filtered = [...this.articles];

            // Filter by search term
            if (this.searchTerm.trim()) {
                const term = this.searchTerm.toLowerCase().trim();
                filtered = filtered.filter(article => {
                    return (
                        article.title.toLowerCase().includes(term) ||
                        (article.summary && article.summary.toLowerCase().includes(term)) ||
                        (article.content && article.content.toLowerCase().includes(term)) ||
                        article.source.toLowerCase().includes(term)
                    );
                });
            }

            // Filter by category
            if (this.selectedCategory !== 'all') {
                filtered = filtered.filter(article => {
                    const category = this.getCategory(article).toLowerCase();
                    return category === this.selectedCategory ||
                           (this.selectedCategory === 'breaking' && this.isBreakingNews(article));
                });
            }

            // Separate breaking news
            this.breakingNews = filtered.filter(article => this.isBreakingNews(article)).slice(0, 4);

            // Regular articles (exclude breaking if showing all, include if filtering breaking)
            if (this.selectedCategory === 'breaking') {
                this.filteredArticles = this.breakingNews;
                this.breakingNews = [];
            } else {
                this.filteredArticles = filtered.filter(article => !this.isBreakingNews(article));
            }
        },

        /**
         * Check if article is breaking news (published within last 6 hours)
         */
        isBreakingNews(article) {
            if (!article.published_date) return false;

            const now = new Date();
            const publishedDate = new Date(article.published_date);
            const diffHours = (now - publishedDate) / (1000 * 60 * 60);

            return diffHours <= 6;
        },

        /**
         * Determine article category from title/content
         */
        getCategory(article) {
            const text = `${article.title} ${article.summary || article.content || ''}`.toLowerCase();

            if (text.match(/regulat|compliance|licens|legal|law|legislat/)) return 'Regulation';
            if (text.match(/merger|acquisition|acquir|deal|partnership|agreement/)) return 'M&A';
            if (text.match(/product|launch|release|platform|game|slot|casino/)) return 'Product';
            if (text.match(/market|expansion|growth|revenue|earnings/)) return 'Market';

            return 'General';
        },

        /**
         * Get category color class
         */
        getCategoryColor(article) {
            const category = this.getCategory(article);

            switch (category) {
                case 'Regulation': return 'bg-blue-100 text-blue-800';
                case 'M&A': return 'bg-green-100 text-green-800';
                case 'Product': return 'bg-purple-100 text-purple-800';
                case 'Market': return 'bg-orange-100 text-orange-800';
                default: return 'bg-gray-100 text-gray-800';
            }
        },

        /**
         * Get sentiment emoji based on article content
         */
        getSentimentEmoji(article) {
            const text = `${article.title} ${article.summary || article.content || ''}`.toLowerCase();

            // Positive indicators
            if (text.match(/launch|growth|success|win|approve|partner|expand|record|strong/)) {
                return '📈';
            }

            // Negative indicators
            if (text.match(/fine|penalt|suspend|ban|investigate|decline|loss|concern|warning/)) {
                return '⚠️';
            }

            // Neutral/informational
            return '📊';
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

                this.showMessage(`Daily digest created with ${data.article_count} articles!`, 'success');
            } catch (error) {
                console.error('Error creating digest:', error);
                this.showMessage('Failed to create digest: ' + error.message, 'error');
            } finally {
                this.loadingDigest = false;
            }
        },

        /**
         * Open article modal
         */
        openModal(article) {
            this.selectedArticle = article;
            // Prevent body scroll when modal is open
            document.body.style.overflow = 'hidden';
        },

        /**
         * Close article modal
         */
        closeModal() {
            this.selectedArticle = null;
            // Re-enable body scroll
            document.body.style.overflow = 'auto';
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
                if (diffHours < 6) return `${diffHours}h ago`;
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
        }
    };
}
