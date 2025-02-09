import torch
from transformers import AutoTokenizer, RobertaForSequenceClassification, pipeline
from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from multiprocessing import freeze_support
from flask_cors import CORS  # Add CORS support
import re

app = Flask(__name__)
CORS(app)  # Enable CORS

# Load RoBERTa model and tokenizer for fake news detection
MODEL_NAME = "JLAbe/fk-detect-3e-model"
try:
    # Load the tokenizer with corrected configuration
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        use_fast=True,
    )
    
    model = RobertaForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=2,
        ignore_mismatched_sizes=True
    )
    model.eval()  # Set model to evaluation mode
    
    # Create pipeline with your specific tokenizer
    detection_pipeline = pipeline(
        "text-classification",
        model=model,
        tokenizer=tokenizer,
        device=-1  # Use CPU. Change to 0 for GPU if available
    )
    
except Exception as e:
    print(f"Error loading model or tokenizer: {str(e)}")
    raise

# Load summarizer model
summarizer_model = "facebook/bart-large-cnn"
summarizer = pipeline("summarization", model=summarizer_model)

# Add this after the trusted_sources list
def find_related_articles(title, content, trusted_sources):
    related_articles = []
    
    # Create search terms from title and first few words of content
    search_terms = title.split()[:8]  # Use first 8 words of title
    search_query = '+'.join(search_terms)
    encoded_query = requests.utils.quote(search_query)
    
    # Construct search URLs for trusted sources
    for domain in trusted_sources:
        try:
            # Updated search URL construction based on the domain
            if domain == 'inquirer.net':
                search_url = f"https://www.inquirer.net/search/?q={encoded_query}#gsc.tab=0&gsc.q={encoded_query}&gsc.page=1"
            elif domain == 'gmanews.tv':
                search_url = f"https://www.gmanetwork.com/news/search/?search_it#gsc.tab=0&gsc.q={encoded_query}&gsc.sort="
            elif domain == 'rappler.com':
                search_url = f"https://www.rappler.com/?q={encoded_query}#gsc.tab=0&gsc.q={encoded_query}&gsc.page=1"
            elif domain == 'abs-cbn.com':
                search_url = f"https://www.abs-cbn.com/search?q={encoded_query}#gsc.tab=0&gsc.q={encoded_query}&gsc.page=1"
            elif domain == 'mb.com.ph':
                search_url = f"https://mb.com.ph/search-results?s={requests.utils.quote(' '.join(search_terms))}"
            else:
                continue  # Skip if domain is not recognized
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract search results (this is a basic implementation)
            results = soup.find_all('a', href=True)
            for result in results[:3]:  # Limit to first 3 results per source
                href = result.get('href', '')
                if domain in href and 'google' not in href and '#' not in href:
                    title = result.get_text().strip()[:100]  # Limit title length
                    if href and title and href not in [a['url'] for a in related_articles]:
                        # Ensure the URL is absolute
                        if not href.startswith(('http://', 'https://')):
                            href = f"https://{domain}{href if href.startswith('/') else '/' + href}"
                        
                        related_articles.append({
                            'url': href,
                            'title': title,
                            'source': domain
                        })
        except Exception as e:
            print(f"Error finding related articles for {domain}: {str(e)}")
            continue
    
    return related_articles[:5]  # Return top 5 related articles

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        article_url = data.get("url")

        if not article_url:
            return jsonify({"error": "URL is required"}), 400

        # Add list of trusted news sources
        trusted_sources = [
            'gmanews.tv',
            'inquirer.net',
            'philstar.com',
            'rappler.com',
            'abs-cbn.com',
            'manilatimes.net',
            'mb.com.ph'  # Manila Bulletin
        ]

        # Add list of suspicious news sources
        suspicious_sources = [
            'adobochronicles',
            'pinoyweekly',
            'getrealphilippines',
            'pinoytrending.altervista',
            'grpshorts.blogspot',
            'duterte',
            'thinkingpinoy',
            'pilipinasonlineupdates',
            'pinoynewsblogger.blogspot',
            'hotnewsphil.blogspot'
        ]

        # Check source credibility
        is_trusted_source = any(domain in article_url.lower() for domain in trusted_sources)
        is_suspicious_source = any(domain in article_url.lower() for domain in suspicious_sources)

        # Validate URL
        if not article_url.startswith(('http://', 'https://')):
            return jsonify({"error": "Invalid URL format"}), 400

        # Fetch article content with extended timeout and headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(article_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                return jsonify({
                    "error": f"Unexpected content type: {content_type}. Expected HTML content."
                }), 400

        except requests.RequestException as e:
            error_message = str(e)
            if response.status_code == 403:
                error_message = "Access forbidden. The website may be blocking automated access."
            elif response.status_code == 404:
                error_message = "Page not found. The article URL may be invalid."
            elif response.status_code == 429:
                error_message = "Too many requests. Please try again later."
            
            return jsonify({
                "error": f"Failed to fetch article: {error_message}",
                "status_code": response.status_code
            }), response.status_code or 500

        soup = BeautifulSoup(response.content, 'html.parser')

        # Enhanced author extraction with multiple methods
        author = None
        
        # Method 1: Check meta tags
        meta_author_tags = [
            soup.find('meta', {'name': 'author'}),
            soup.find('meta', {'property': 'article:author'}),
            soup.find('meta', {'property': 'og:author'})
        ]
        for tag in meta_author_tags:
            if tag and tag.get('content'):
                author = tag.get('content').strip()
                break

        # Method 2: Check common author classes and attributes
        if not author:
            author_selectors = [
                {'class_': ['author', 'byline', 'writer', 'Writer', 'Author', 'article-author',
                           'article__author', 'article-writer', 'post-author', 'entry-author']},
                {'itemprop': 'author'},
                {'rel': 'author'},
                {'id': ['author', 'byline', 'writer']},
            ]
            
            for selector in author_selectors:
                author_elements = soup.find_all(**selector)
                for element in author_elements:
                    if element.string:
                        author = element.string.strip()
                        break
                    elif element.text:
                        author = element.text.strip()
                        break
                if author:
                    break

        # Method 3: Look for specific HTML structures
        if not author:
            author_patterns = [
                soup.find('span', class_='author'),
                soup.find('div', class_='author'),
                soup.find('a', class_='author'),
                soup.find('p', class_='byline'),
                soup.find('div', class_='byline'),
                soup.find('span', class_='byline')
            ]
            for pattern in author_patterns:
                if pattern and pattern.text:
                    author = pattern.text.strip()
                    break

        # Clean up author text
        if author:
            # Remove common prefixes
            prefixes = ['By ', 'by ', 'Author: ', 'Written by ', 'Posted by ']
            for prefix in prefixes:
                if author.startswith(prefix):
                    author = author[len(prefix):]
            
            # Clean up whitespace and special characters
            author = ' '.join(author.split())
            
            # Remove email addresses if present
            author = re.sub(r'\S+@\S+', '', author).strip()
            
            # Remove URLs if present
            author = re.sub(r'http\S+', '', author).strip()
        
        # Default if no author found
        if not author:
            author = "Unknown Author"

        # Rest of the code remains the same
        title = None
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.text.strip()
        if not title:
            og_title = soup.find('meta', property='og:title')
            if og_title:
                title = og_title.get('content', '').strip()
        title = title or "Unable to extract title"

        # Extract content with better cleaning
        content_tags = soup.find_all(['p', 'article'])
        content = ' '.join([tag.get_text().strip() for tag in content_tags if tag.get_text().strip()])
        
        if not content:
            return jsonify({"error": "No article content found"}), 400

        # Summarize the article
        try:
            if len(content.split()) > 40:
                summary = summarizer(content[:1024], max_length=130, min_length=30, do_sample=False)
                summarized_text = summary[0]['summary_text']
            else:
                summarized_text = content
        except Exception as e:
            print(f"Summarization error: {str(e)}")
            summarized_text = content[:200] + "..."

        # Modify credibility detection logic
        try:
            result = detection_pipeline(content[:512])
            score = result[0]['score']
            
            # Adjust overall credibility score based on source
            if is_trusted_source:
                # For trusted sources like inquirer.net: very high confidence in being credible
                credibility = "Credible"
                confidence = 0.92 + (0.06 * (1.0 - score))  # Range: 92-98%
                confidence_percentage = confidence * 100
            elif is_suspicious_source:
                # For suspicious sources: moderate-high confidence in being suspicious
                credibility = "Suspicious"
                confidence = 0.75 + (0.10 * score)  # Range: 75-85%
                confidence_percentage = confidence * 100
            else:
                # Normal processing for other sources
                credibility = "Suspicious" if score > 0.60 else "Credible"
                if credibility == "Credible":
                    confidence = 0.70 + (0.15 * (1.0 - score))  # Range: 70-85%
                else:
                    confidence = 0.40 + (0.30 * score)  # Range: 40-70%
                confidence_percentage = confidence * 100

            # Also adjust word-level analysis for trusted sources
            def analyze_word_credibility(word, is_trusted_source, is_suspicious_source):
                if len(word.strip()) < 2:
                    return None
                
                try:
                    # Get raw prediction from model
                    result = detection_pipeline(word)
                    raw_score = result[0]['score']
                    
                    # Determine credibility based on model threshold
                    is_credible = raw_score <= 0.55
                    
                    # Calculate confidence based on source and credibility
                    if is_trusted_source:
                        # For trusted sources: maintain high confidence in credibility
                        confidence = 0.85 + (0.13 * (1.0 - raw_score))  # Range: 85-98%
                    elif is_suspicious_source:
                        # For suspicious sources: moderate-high confidence in being suspicious
                        confidence = 0.70 + (0.15 * raw_score)  # Range: 70-85%
                    else:
                        # Normal range for other cases
                        if is_credible:
                            confidence = 0.70 + (0.15 * (1.0 - raw_score))  # Range: 70-85%
                        else:
                            confidence = 0.40 + (0.30 * raw_score)  # Range: 40-70%
                    
                    return {
                        "word": word,
                        "credibility": "Credible" if is_credible else "Suspicious",
                        "confidence": float(confidence)
                    }
                except Exception:
                    return None

            # Analyze each word in the summary
            summary_words = summarized_text.split()
            word_analysis = [analyze_word_credibility(word, is_trusted_source, is_suspicious_source) 
                           for word in summary_words]
            word_analysis = [w for w in word_analysis if w is not None]

            # Add this before the final return statement
            related_articles = find_related_articles(title, content, trusted_sources)

            return jsonify({
                "title": title,
                "author": author,
                "summary": summarized_text,
                "wordAnalysis": word_analysis,
                "credibility": credibility,
                "confidence": confidence,
                "confidencePercentage": confidence_percentage,
                "fullContent": content[:1000],
                "isTrustedSource": is_trusted_source,
                "isSuspiciousSource": is_suspicious_source,
                "relatedArticles": related_articles
            })

        except Exception as e:
            print(f"Credibility detection error: {str(e)}")
            return jsonify({"error": "Failed to analyze credibility"}), 500

    except Exception as e:
        print(f"General error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    freeze_support()
    app.run(debug=True)
