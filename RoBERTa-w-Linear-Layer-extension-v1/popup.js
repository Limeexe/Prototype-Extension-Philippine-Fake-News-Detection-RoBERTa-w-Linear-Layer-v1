const GOOGLE_API_KEY = 'AIzaSyDWDo1Eoz-yf1633lJ3irRmQPCXAq5t4Lo';
const SEARCH_ENGINE_ID = '57e383326bc644591';

document.addEventListener('DOMContentLoaded', async () => {
    // Get current active tab URL
    try {
        const tabs = await chrome.tabs.query({active: true, currentWindow: true});
        const currentUrl = tabs[0].url;
        
        // Set the URL in the input field
        const urlInput = document.getElementById('url-input');
        urlInput.value = currentUrl;

        // Automatically trigger analysis if it's a valid URL
        if (isValidNewsUrl(currentUrl)) {
            document.getElementById('analyze-btn').click();
        }
    } catch (error) {
        console.error('Error getting tab URL:', error);
    }
});

// Helper function to validate news URLs
function isValidNewsUrl(url) {
    try {
        const urlObj = new URL(url);
        // List of common news domains
        const newsDomains = [
            'news.', 
            'bbc.', 
            'cnn.', 
            'reuters.', 
            'nytimes.', 
            'theguardian.',
            'washingtonpost.',
            'forbes.',
            'bloomberg.',
            'aljazeera.',
            'abc.',
            'nbc.',
            'fox',
            'usatoday.',
            'wsj.',
            'latimes.',
            'nypost.',
            'inquirer.',
            'philstar.',
            'rappler.',
            'abs-cbn.',
            'gmanews.',
            'manila',
            'adobochronicles',
            'manilabulletin',
            'manilatimes',
            'pinoyweekly',
            'getrealphilippines',
            'pinoytrending.altervista',
            'duterte',
            'thinkingpinoy',
            'grpshorts.blogspot',
            'duterte.today',
            'pilipinasonlineupdates',
            'pinoynewsblogger.blogspot',
            'pinoytrending.altervista',
            'hotnewsphil.blogspot',
            
        ];
        
        return newsDomains.some(domain => urlObj.hostname.toLowerCase().includes(domain));
    } catch {
        return false;
    }
}

// Add this function to analyze individual words
function analyzeAndHighlightWords(summary, wordAnalysis) {
    if (!wordAnalysis || !Array.isArray(wordAnalysis)) {
        return summary; // Return original summary if no analysis available
    }

    // Split the summary into words while preserving punctuation
    const words = summary.match(/\b\w+\b|[^\w\s]/g) || [];
    
    // Create highlighted HTML
    const highlightedWords = words.map(word => {
        // Find analysis for this word
        const analysis = wordAnalysis.find(a => a.word.toLowerCase() === word.toLowerCase());
        
        if (!analysis) {
            return word; // Return original word if no analysis found
        }

        // Calculate color based on confidence score
        const confidence = analysis.confidence;
        let colorClass = '';
        let tooltip = '';

        if (analysis.credibility === 'Credible') {
            colorClass = 'word-credible';
            tooltip = `Credible (${(confidence * 100).toFixed(1)}% confidence)`;
        } else {
            colorClass = 'word-suspicious';
            tooltip = `Suspicious (${(confidence * 100).toFixed(1)}% confidence)`;
        }

        return `<span class="${colorClass}" title="${tooltip}">${word}</span>`;
    });

    return highlightedWords.join(' ');
}

// Add function to generate search URLs based on headline
function getSearchUrls(headline) {
    const encodedQuery = encodeURIComponent(headline);
    return {
        'inquirer.net': `https://www.inquirer.net/search/?q=${encodedQuery}#gsc.tab=0&gsc.q=${encodedQuery}&gsc.page=1`,
        'gmanews.tv': `https://www.gmanetwork.com/news/search/?search_it#gsc.tab=0&gsc.q=${encodedQuery}&gsc.sort=`,
        'rappler.com': `https://www.rappler.com/?q=${encodedQuery}#gsc.tab=0&gsc.q=${encodedQuery}&gsc.page=1`,
        'abs-cbn.com': `https://www.abs-cbn.com/search?q=${encodedQuery}#gsc.tab=0&gsc.q=${encodedQuery}&gsc.page=1`,
        'mb.com.ph': `https://mb.com.ph/search-results?s=${encodedQuery}`
    };
}

// Add function to check if URL is likely to have results
function isLikelyToHaveResults(headline, domain) {
    // Remove special characters and extra spaces
    const cleanHeadline = headline.replace(/[^\w\s]/g, '').trim();
    
    // Skip if headline is too short or empty
    if (cleanHeadline.length < 3) {
        return false;
    }

    // Domain-specific conditions
    switch(domain) {
        case 'inquirer.net':
            return cleanHeadline.split(' ').length >= 2; // At least 2 words
        case 'gmanews.tv':
            return cleanHeadline.length >= 5; // At least 5 characters
        case 'rappler.com':
            return cleanHeadline.split(' ').length >= 2;
        case 'abs-cbn.com':
            return cleanHeadline.length >= 5;
        case 'mb.com.ph':
            return cleanHeadline.split(' ').length >= 2;
        default:
            return true;
    }
}

// Replace the existing find_related_articles function in app.py with this updated version
async function findRelatedArticles(title) {
    try {
        // Create search query from title
        const searchQuery = encodeURIComponent(title);
        const baseUrl = 'https://www.googleapis.com/customsearch/v1';
        
        // Construct the API URL with your credentials
        const searchUrl = `${baseUrl}?key=${GOOGLE_API_KEY}&cx=${SEARCH_ENGINE_ID}&q=${searchQuery}`;

        const response = await fetch(searchUrl);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(`Google API Error: ${data.error?.message || 'Unknown error'}`);
        }

        // Process and filter results
        const relatedArticles = data.items
            ?.filter(item => {
                // Filter for trusted news domains
                const trustedDomains = [
                    'inquirer.net',
                    'gmanews.tv',
                    'rappler.com',
                    'abs-cbn.com',
                    'mb.com.ph',
                    'philstar.com',
                    'manilatimes.net'
                ];
                return trustedDomains.some(domain => item.link.includes(domain));
            })
            .map(item => ({
                url: item.link,
                title: item.title,
                source: new URL(item.link).hostname,
                snippet: item.snippet
            }))
            .slice(0, 5); // Limit to top 5 results

        return relatedArticles || [];

    } catch (error) {
        console.error('Error finding related articles:', error);
        return [];
    }
}

// Update the createRelatedArticlesSection function
function createRelatedArticlesSection(articles) {
    if (!articles || articles.length === 0) {
        return `
            <div class="related-articles-section">
                <div class="related-header">
                    <h3>Cross-Reference on Trusted Sources</h3>
                    <div class="related-icon">🔍</div>
                </div>
                <p class="no-results-message">No related articles found in trusted sources.</p>
            </div>
        `;
    }

    const articlesList = articles.map(article => `
        <li class="related-article">
            <a href="${article.url}" target="_blank" class="related-link">
                <span class="related-title">${article.title}</span>
                <span class="related-source">${article.source}</span>
                <span class="related-snippet">${article.snippet}</span>
            </a>
        </li>
    `).join('');

    return `
        <div class="related-articles-section">
            <div class="related-header">
                <h3>Cross-Reference on Trusted Sources</h3>
                <div class="related-icon">🔍</div>
            </div>
            <ul class="related-articles-list">
                ${articlesList}
            </ul>
        </div>
    `;
}

document.getElementById("analyze-btn").addEventListener("click", async () => {
    const button = document.getElementById("analyze-btn");
    const loader = button.querySelector(".loader");
    const buttonText = button.querySelector(".button-text");
    const url = document.getElementById("url-input").value;

    if (!url) {
        alert("Please enter a valid news article URL!");
        return;
    }

    try {
        // Show loading state
        button.disabled = true;
        loader.classList.remove("hidden");
        buttonText.textContent = "Analyzing...";

        const response = await fetch("http://localhost:5000/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(data.error || "Failed to analyze article");
        }

        // Update the UI with results
        const title = data.title || "No title found";
        document.getElementById("title").textContent = title;
        document.getElementById("author").textContent = data.author || "Unknown Author";
        
        // Update credibility badge and percentage
        const credibilityElement = document.getElementById("credibility");
        const confidenceElement = document.getElementById("confidence");
        const credibilityBadge = credibilityElement.closest('.credibility-badge');
        
        credibilityElement.textContent = data.credibility;
        
        // Fix: Use direct confidence percentage for credible sources
        const confidencePercentage = data.credibility === "Credible" 
            ? data.confidencePercentage.toFixed(1)        // Use direct percentage for credible
            : data.confidencePercentage.toFixed(1);       // Use direct for suspicious
        
        // Update the confidence label based on credibility status
        const confidenceLabelElement = credibilityBadge.querySelector('.confidence-label');
        confidenceLabelElement.textContent = data.credibility === "Credible" 
            ? "Credibility Score via Cross-Referencing"
            : "Suspicious Score via Cross-Referencing";
        
        confidenceElement.textContent = `${confidencePercentage}%`;
        
        // Update progress bar
        const progressFill = credibilityBadge.querySelector('.progress-fill');
        progressFill.style.width = '0%'; // Reset width
        
        // Trigger reflow to ensure animation plays
        void progressFill.offsetWidth;
        
        // Set the new width with animation
        progressFill.style.width = `${confidencePercentage}%`;
        
        // Update badge class based on credibility
        credibilityBadge.className = "credibility-badge " + data.credibility.toLowerCase();

        // Update summary with word analysis highlighting
        const summaryElement = document.getElementById("summary");
        const highlightedSummary = analyzeAndHighlightWords(data.summary, data.wordAnalysis);
        summaryElement.innerHTML = highlightedSummary;

        // Get related articles using Google Custom Search
        const relatedArticles = await findRelatedArticles(title);
        
        // Remove any existing related articles section
        const existingRelatedSection = document.querySelector('.related-articles-section');
        if (existingRelatedSection) {
            existingRelatedSection.remove();
        }

        // Add related articles section
        const relatedArticlesHTML = createRelatedArticlesSection(relatedArticles);
        document.querySelector('.summary-section').insertAdjacentHTML('afterend', relatedArticlesHTML);

        document.getElementById("results").classList.remove("hidden");

    } catch (error) {
        console.error("Analysis error:", error);
        alert(`Analysis failed: ${error.message}`);
    } finally {
        // Reset button state
        button.disabled = false;
        loader.classList.add("hidden");
        buttonText.textContent = "Analyze Article";
    }
});

// Auto-analyze when URL is pasted
document.getElementById("url-input").addEventListener("paste", (e) => {
    setTimeout(() => {
        document.getElementById("analyze-btn").click();
    }, 100);
});

// Add URL validation
function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}