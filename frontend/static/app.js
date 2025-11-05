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

        // State - View
        currentView: 'feed', // 'feed' or 'digest'

        // State - Digest
        digest: '',
        digestDate: '',
        digestArticleCount: 0,

        // State - LinkedIn Article
        linkedinArticle: '',
        articleCharCount: 0,
        articleWordCount: 0,

        // State - Modal
        selectedArticle: null,

        // Loading states
        loadingArticles: false,
        loadingFetch: false,
        loadingSummaries: false,
        loadingDigest: false,
        loadingArticle: false,

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

            // Regulation & Compliance
            if (text.match(/regulat|compliance|licens|legal|law|legislat/)) return 'Regulation';

            // M&A - Enhanced with more keywords
            if (text.match(/merger|acquisition|acquir|deal|partnership|partner(s)? with|joint venture|stake|investment|invest(s)? in|buyout|takeover/)) return 'M&A';

            // Product & Innovation
            if (text.match(/product|launch|release|platform|game|slot|casino/)) return 'Product';

            // Market & Business
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
         * Fetch latest news from RSS feeds (fast - no summary generation)
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
                const newArticles = data.new_articles;

                if (newArticles > 0) {
                    this.showMessage(`Fetched ${newArticles} new articles!`, 'success');
                } else {
                    this.showMessage('No new articles found', 'success');
                }

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
         * Load digest from API
         */
        async loadDigest() {
            if (this.digest) return; // Already loaded

            this.loadingDigest = true;
            try {
                const today = new Date().toISOString().split('T')[0];
                const response = await fetch(`${this.apiUrl}/digest/${today}`);

                if (!response.ok) {
                    // No digest for today
                    this.digest = '';
                    this.loadingDigest = false;
                    return;
                }

                const data = await response.json();
                this.digest = data.digest.content;
                this.digestDate = this.formatDigestDate(data.digest.digest_date);
                this.digestArticleCount = data.digest.article_count;

                console.log('Digest loaded successfully');
            } catch (error) {
                console.error('Error loading digest:', error);
                this.digest = '';
            } finally {
                this.loadingDigest = false;
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

                // Update digest state
                this.digest = data.digest;
                this.digestDate = this.formatDigestDate(data.digest_date);
                this.digestArticleCount = data.article_count;

                // Switch to digest view
                this.currentView = 'digest';

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
         * Format digest content (convert markdown to HTML with links)
         */
        formatDigestContent(content) {
            if (!content) return '';

            let formatted = content
                // Headers
                .replace(/## (.*?)(\n|$)/g, '<h2 class="text-2xl font-bold mt-6 mb-4 text-gray-900">$1</h2>')
                .replace(/### (.*?)(\n|$)/g, '<h3 class="text-lg font-semibold mt-4 mb-2 text-gray-800">$1</h3>')
                // Bold text
                .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-900">$1</strong>')
                // Markdown links with styling
                .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 hover:underline inline-flex items-center gap-1">$1 <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg></a>')
                // Paragraphs
                .replace(/\n\n/g, '</p><p class="mb-4 text-gray-700 leading-relaxed">')
                .replace(/\n/g, '<br>');

            return '<p class="mb-4 text-gray-700 leading-relaxed">' + formatted + '</p>';
        },

        /**
         * Generate LinkedIn article from digest
         */
        async generateArticle() {
            this.loadingArticle = true;
            try {
                const response = await fetch(`${this.apiUrl}/generate-article`, {
                    method: 'POST'
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP ${response.status}`);
                }

                const data = await response.json();
                this.linkedinArticle = data.article;
                this.articleCharCount = data.char_count;
                this.articleWordCount = data.word_count;

                this.showMessage('LinkedIn article generated successfully!', 'success');

                // Scroll to article
                setTimeout(() => {
                    document.querySelector('.article-content')?.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }, 100);

            } catch (error) {
                console.error('Error generating article:', error);
                this.showMessage('Failed to generate article: ' + error.message, 'error');
            } finally {
                this.loadingArticle = false;
            }
        },

        /**
         * Copy article to clipboard
         */
        async copyArticle() {
            try {
                // Remove HTML tags for plain text copy
                const plainText = this.linkedinArticle
                    .replace(/\*\*/g, '')  // Remove markdown bold
                    .replace(/##\s/g, '')  // Remove markdown headers
                    .replace(/###\s/g, '');

                await navigator.clipboard.writeText(plainText);
                this.showMessage('Article copied to clipboard!', 'success');
            } catch (error) {
                console.error('Error copying article:', error);
                this.showMessage('Failed to copy article', 'error');
            }
        }
    };
}
