import os
import re
import requests
import streamlit as st
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def fetch_firecrawl_reviews(product_name):
    """Fetch additional reviews using Firecrawl API with improved error handling"""
    firecrawl_key = os.getenv("FIRECRAWL_KEY")
    if not firecrawl_key:
        st.warning("Firecrawl API key is missing. Skipping this data source.")
        return []
        
    try:
        st.write("Debug: Using Firecrawl API to fetch reviews...")
        
        # Configure retry strategy
        session = requests.Session()
        retries = Retry(
            total=2,  # Try 3 times in total
            backoff_factor=1,  # Wait 1, 2, 4 seconds between retries
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )
        session.mount('https://', HTTPAdapter(max_retries=retries))
        
        # Make the API request with updated endpoint and parameters
        headers = {
            "Authorization": f"Bearer {firecrawl_key}",
            "Content-Type": "application/json"
        }
        
        # First search for fashion product pages with shorter timeout
        search_data = {
            "query": f"{product_name} reviews site:amazon.com OR site:nordstrom.com OR site:macys.com OR site:zappos.com OR site:asos.com OR site:revolve.com OR site:fashionnova.com",
            "limit": 5,  # Get top 5 product review pages
            "scrapeOptions": {
                "formats": ["markdown"],
                "timeout": 20000  # 20 second timeout per page
            }
        }
        
        with st.spinner("Searching for product review pages..."):
            search_response = session.post(
                "https://api.firecrawl.dev/v1/search",
                headers=headers,
                json=search_data,
                timeout=30  # 30 second timeout for full operation
            )
        
        if search_response.status_code != 200:
            st.error(f"Firecrawl API error: Status code {search_response.status_code}")
            if search_response.text:
                st.error(f"Error details: {search_response.text[:200]}...")
            return []
            
        search_data = search_response.json()
        if not search_data.get('success'):
            st.error(f"Firecrawl API error: {search_data.get('error', 'Unknown error')}")
            return []
            
        reviews = []
        for result in search_data.get('data', []):
            markdown_content = result.get('markdown', '')
            if not markdown_content:
                continue
                
            # Parse markdown content for reviews
            lines = markdown_content.split('\n')
            current_review = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Look for rating patterns
                rating_match = re.search(r'([0-5](?:[.,][0-9])?)[\s/]*(?:out of\s)?5?\s*(?:stars?)?', line.lower())
                if rating_match:
                    try:
                        current_review['rating'] = int(float(rating_match.group(1)))
                        continue
                    except (ValueError, TypeError):
                        pass
                        
                # Look for review content
                if len(line) > 20:
                    if 'content' in current_review:
                        current_review['content'] += '\n' + line
                    else:
                        current_review['content'] = line
                        
                # Look for date patterns
                date_match = re.search(r'(?:reviewed|posted|written)\s+(?:on\s+)?([A-Z][a-z]+\s+\d{1,2},\s+\d{4})', line)
                if date_match:
                    current_review['date'] = date_match.group(1)
                    
                # Look for verified purchase
                if 'verified' in line.lower():
                    current_review['verified'] = True
                    
                # Look for helpful votes
                helpful_match = re.search(r'(\d+)\s+(?:people|users?)\s+found this helpful', line.lower())
                if helpful_match:
                    current_review['helpful_votes'] = int(helpful_match.group(1))
                    
            # Save the review if it has content
            if current_review.get('content') and len(current_review['content']) > 20:
                review = {
                    'content': current_review['content'].strip(),
                    'rating': current_review.get('rating', 'N/A'),
                    'author': current_review.get('author', 'Anonymous'),
                    'source': result.get('title', 'Firecrawl'),
                    'date': current_review.get('date', ''),
                    'verified': current_review.get('verified', False),
                    'helpful_votes': current_review.get('helpful_votes', 0)
                }
                reviews.append(review)
                
        if reviews:
            st.success(f"Found {len(reviews)} reviews from Firecrawl")
        else:
            st.warning("No usable reviews found from Firecrawl.")
            
        return reviews
    except Exception as e:
        st.error(f"Error fetching reviews from Firecrawl: {str(e)}")
        return []
