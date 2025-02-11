# Prototype-Extension-Philippine-Fake-News-Detection-RoBERTa-w-Linear-Layer-v1

This is a Python-based Chrome extension designed to detect fake news by analyzing text content created for the purpose of the research thesis entitled "**Development and Prototype Implementation of a Browser Extension for Fake News Detection in Philippine News Using Natural Language Processing Algorithms**" in Computer Science Thesis 1 & 2 subject in Bachelor of Computer Science in Camarines Sur Polytechnic Colleges. The extension uses machine learning models to determine the credibility of news articles.

<<<<<<< SEARCH
=======
# Chrome Extension: Fake News Detector using RoBERTa

**Objective**: Detect credibility of news articles using AI-powered text analysis.

---

## Overview

This Chrome extension implements an AI-based fake news detection system using the RoBERTa large pre-trained model. It combines multiple natural language processing (NLP) techniques to analyze and evaluate the credibility of news articles. The extension provides:

1. Credibility scoring for URLs
2. Text summarization with confidence scores
3. Word-level importance analysis
4. Related article detection using Google Custom Search
5. Visual feedback during analysis

---

## Installation

1. Clone the repository:
```bash
git clone https://github.com/username/YOUR_USERNAME/popup.html.git
cd popup-extension
```

2. Extract the necessary files:
```bash
unzip popup-extension.zip
```

3. Place the following files in `content/popup.html` and `content/popup.js` in your browser's `public_html` directory (e.g., `~/.config/google/barrier/extension/crm-popsicle-content/popup/`):
   - popup.html: Main extension HTML file
   - popup.js: JavaScript functionality

4. Restart your Chrome browser to load the extension.

---

## Description

This extension uses RoBERTa, a state-of-the-art transformer model from Facebook's AI research lab, for several key tasks:

1. **Text Classification**:
   - Categorizes articles as "Credible" or "Suspicious"
   - Uses word-level labels to provide detailed credibility scores

2. **Text Summarization**:
   - Generates concise summaries while maintaining key information
   - Highlights important content (sources, dates, and entities)

3. **Word-Level Analysis**:
   - Identifies important words contributing to article credibility
   - Provides confidence scores for each word's importance

4. **Related Articles Detection**:
   - Finds similar articles from trusted domains using Google Custom Search
   - Shows multiple sources and authors for context

5. **Confidence Feedback**:
   - Visual progress bars during analysis
   - Confidence scores displayed in styled boxes
   - Loading states and error handling

---

## Features

- **Credibility Scoring**: 
  - Combines multi-label classification (Credible/Suspicious) with confidence scoring
  - Provides credibility badge with percentage score
  
- **Text Summarization**:
  - Maintains source information
  - Shows word importance scores
  - Highlight key findings

- **Word Analysis**:
  - High/low importance words highlighted in bold
  - Confidence scores for each word's contribution

- **Related Content**:
  - Finds similar articles from trusted domains
  - Displays multiple sources and authors

- **User Interface**:
  - Clean, modern design with clear feedback
  - Responsive layout across different screen sizes
  - Easy-to-read sections with hover effects

---

## How to Use

1. Open Chrome and go to:  
   ```bash
   chrome://extensions/
   ```
2. Enable "Developer mode" if not already enabled.
3. Click the "Add" button on the toolbar.
4. Select your popup.html file from the extracted files.
5. Click "Open" to install the extension.

**Actions Available**:
- Enter a news article URL in the input field
- Paste text directly into the textarea
- Click the "Analyze Article" button to get results

---

## Model Architecture

### Key Components

1. **Input Handling**
   - URL validation checks (e.g., domain trustworthiness)
   - Text normalization (punctuation removal)

2. **NLP Pipeline**:
   - Tokenization with word importance scoring
   - RoBERTa model inference for multiple tasks:
     - Credibility classification
     - Sentiment analysis
     - Text summarization

3. **Output Display**
   - Confidence badges with percentages
   - Highlighted key words and phrases
   - Summary section with main content points
   - Related articles suggestions

4. **Technology Stack**:
   - Google Chrome extension framework
   - React, TypeScript for component-based UI
   - RoBERTa large model (Hugging Face)
   - TensorFlow.js for GPU/TPU acceleration

---

## Technical Details

- **Backend**:
  - Uses fetch API for external calls to Google Custom Search
  - Leverages pre-trained RoBERTa model weights
  - Configurable parameters for context window and API keys

- **Frontend**:
  - Single-page application with React components
  - TypeScript for modern, type-safe code
  - CSS custom properties for consistent styling

---
