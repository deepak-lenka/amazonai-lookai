import os
import re
import json
import requests
import streamlit as st

def fetch_perplexity_reviews(product_name):
    """Fetch additional reviews using Perplexity API as specified in the Notion document"""
    perplexity_key = os.getenv("PERPLEXITY_KEY")
    if not perplexity_key:
        st.warning("Perplexity API key is missing. Skipping this data source.")
        return []
        
    try:
        st.info("Debug: Using Perplexity API to fetch reviews...")
        
        # Initialize the Perplexity client with correct headers
        headers = {
            "Authorization": f"Bearer {perplexity_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Prepare the prompt with specific domain focus
        prompt = (
            f"Search for detailed customer reviews of {product_name} on e-commerce websites and review platforms. "
            "For each review, extract and format the following information:\n\n"
            "1. Rating: [X out of 5 stars]\n"
            "2. Source: [Website name]\n"
            "3. Review: [Full review text]\n"
            "4. Date: [Review date if available]\n"
            "5. Verified Purchase: [Yes/No if available]\n\n"
            "Focus on recent, detailed reviews that discuss product features, performance, and user experience. "
            "Prioritize verified purchase reviews if available."
        )
        
        # Make the API request with optimized parameters based on testing
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json={
                "model": "sonar",  # Using sonar model as confirmed in testing
                "messages": [
                    {
                        "role": "system",
                        "content": "Be precise and concise in extracting and formatting product reviews."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 1024,  # Adjusted based on testing
                "temperature": 0.2,   # Lower temperature for consistency
                "stream": False      # Ensure we get complete response
            },
            timeout=30  # Add timeout to prevent hanging
        )
        
        # Handle API response with improved error checking
        if response.status_code == 400:
            st.error("Invalid request to Perplexity API. Please check the product name and try again.")
            return []
        elif response.status_code == 401:
            st.error("Unauthorized access to Perplexity API. Please check your API key.")
            return []
        elif response.status_code == 429:
            st.error("Rate limit exceeded for Perplexity API. Please try again later.")
            return []
        elif response.status_code != 200:
            st.error(f"Perplexity API error: Status code {response.status_code}")
            if response.text:
                error_details = response.json() if response.headers.get('content-type') == 'application/json' else response.text
                st.error(f"Error details: {str(error_details)[:200]}...")
            return []
            
        try:
            # Extract reviews from the response with validation
            result = response.json()
        except ValueError as e:
            st.error(f"Failed to parse Perplexity API response: {str(e)}")
            return []
            
        if not isinstance(result, dict) or 'choices' not in result:
            st.error("Unexpected response format from Perplexity API")
            return []
            
        # Continue with review extraction
        result = response.json()
        reviews_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        citations = result.get("citations", [])
        
        # Parse reviews from the text with improved structure handling
        reviews = []
        current_review = {}
        review_pattern = re.compile(r'(?:Rating|Source|Review|Date):', re.IGNORECASE)
        
        for line in reviews_text.split("\n"):
            line = line.strip()
            if not line:
                if current_review.get("content"):
                    # Clean up and validate the review before adding
                    content = current_review.get("content", "").strip()
                    if len(content) > 20:  # Minimum content length
                        reviews.append({
                            "content": content,
                            "rating": current_review.get("rating", "N/A"),
                            "author": current_review.get("author", "Anonymous"),
                            "source": current_review.get("source", "Online Review"),
                            "date": current_review.get("date", ""),
                            "verified": "verified" in content.lower()
                        })
                current_review = {}
                continue
                
            # Check if this line starts a new section
            if review_pattern.match(line):
                section = line.split(":", 1)
                if len(section) == 2:
                    key, value = section[0].lower(), section[1].strip()
                    if "rating" in key:
                        rating = re.search(r'([0-9.]+)(?:\s*(?:out\s*of|\/)\s*([0-9.]+))?|([★]+)', value)
                        if rating:
                            matched = rating.group(1) or rating.group(3)
                            if matched:
                                current_review["rating"] = matched
                    elif "source" in key:
                        current_review["source"] = value
                    elif "review" in key:
                        current_review["content"] = value
                    elif "date" in key:
                        current_review["date"] = value
            else:
                # Append to existing content if this is continuation of a review
                if "content" in current_review:
                    current_review["content"] += "\n" + line
                else:
                    current_review["content"] = line
        
        # Add the last review if present
        if current_review.get("content") and len(current_review["content"]) > 20:
            reviews.append({
                "content": current_review["content"].strip(),
                "rating": current_review.get("rating", "N/A"),
                "author": current_review.get("author", "Anonymous"),
                "source": current_review.get("source", "Online Review"),
                "date": current_review.get("date", ""),
                "verified": "verified" in current_review["content"].lower()
            })
        
        if reviews:
            st.success(f"Successfully found {len(reviews)} reviews from Perplexity!")
        else:
            st.warning("No reviews found from Perplexity.")
        
        return reviews
    except requests.exceptions.Timeout:
        st.warning("Perplexity API request timed out. Skipping this data source.")
        return []
    except Exception as e:
        st.error(f"Error fetching reviews from Perplexity: {str(e)}")
        return []

def filter_bad_reviews(reviews):
    """Filter out low-quality or spam reviews using Perplexity Sonar LLM if available, else fallback to heuristics."""
    if not reviews:
        return []
        
    perplexity_key = os.getenv("PERPLEXITY_KEY")
    if perplexity_key:
        try:
            st.info("Using Perplexity Sonar to filter low-quality reviews...")
            headers = {
                "Authorization": f"Bearer {perplexity_key}",
                "Content-Type": "application/json"
            }
            
            # Process reviews in batches to reduce API calls
            batch_size = 5
            filtered_reviews = []
            
            for i in range(0, len(reviews), batch_size):
                batch = reviews[i:i + batch_size]
                review_texts = [f"Review {j+1}:\n{review.get('content', '')}\nRating: {review.get('rating', 'N/A')}" 
                               for j, review in enumerate(batch)]
                
                prompt = (
                    "Analyze these product reviews for quality and authenticity. For each review, respond with KEEP or FILTER based on these criteria:\n\n"
                    "KEEP reviews that:\n"
                    "1. Provide specific details about product features, usage, or personal experience\n"
                    "2. Have coherent writing and natural language\n"
                    "3. Include balanced feedback (both pros and cons if applicable)\n\n"
                    "FILTER reviews that:\n"
                    "1. Are very short or lack meaningful details\n"
                    "2. Contain spam, promotional content, or excessive links\n"
                    "3. Are speculative about unreleased features\n"
                    "4. Only list specifications without actual experience\n"
                    "5. Show signs of being fake or computer-generated\n\n"
                    f"{chr(10).join(review_texts)}\n\n"
                    "For each review number, respond with only KEEP or FILTER."
                )
                
                data = {
                    "model": "sonar",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert at identifying high-quality product reviews. Analyze each review carefully and respond only with KEEP or FILTER."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 100,
                    "temperature": 0.1,  # Low temperature for consistent evaluation
                    "top_p": 0.9
                }
                
                try:
                    response = requests.post(
                        "https://api.perplexity.ai/chat/completions",
                        headers=headers,
                        json=data,
                        timeout=15
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        decisions = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip().split("\n")
                        
                        # Process the decisions
                        for j, (decision, review) in enumerate(zip(decisions, batch)):
                            if "KEEP" in decision.upper():
                                filtered_reviews.append(review)
                    else:
                        # Fallback to heuristics for this batch
                        for review in batch:
                            if _is_good_review_heuristic(review):
                                filtered_reviews.append(review)
                except Exception as e:
                    # Fallback to heuristics for this batch
                    for review in batch:
                        if _is_good_review_heuristic(review):
                            filtered_reviews.append(review)
            
            st.success(f"Filtered {len(reviews) - len(filtered_reviews)} low-quality reviews using Perplexity Sonar")
            return filtered_reviews
        except Exception as e:
            st.warning(f"LLM filtering failed, falling back to heuristic filtering: {str(e)}")
    
    # Heuristic fallback
    st.info("Using heuristic filtering for reviews...")
    filtered_reviews = []
    for review in reviews:
        if _is_good_review_heuristic(review):
            filtered_reviews.append(review)
    
    st.success(f"Filtered {len(reviews) - len(filtered_reviews)} low-quality reviews using heuristics")
    return filtered_reviews

def generate_product_summary(reviews):
    """Generate an overall product summary using Perplexity API."""
    perplexity_key = os.getenv("PERPLEXITY_KEY")
    if not perplexity_key or not reviews:
        return {}
        
    try:
        st.info("Using Perplexity API to generate product summary...")
        
        # Initialize the Perplexity client
        headers = {
            "Authorization": f"Bearer {perplexity_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Group reviews by source
        reviews_by_source = {}
        for review in reviews:
            source = review.get('source', 'Unknown')
            if source not in reviews_by_source:
                reviews_by_source[source] = []
            reviews_by_source[source].append(review)
        
        # Prepare review samples (up to 10, ensuring representation from all sources)
        review_samples = []
        sources_used = []
        
        # Get one review from each source first
        for source, source_reviews in reviews_by_source.items():
            if source_reviews and len(review_samples) < 10:
                # Sort by rating and helpfulness to get most useful reviews
                sorted_reviews = sorted(source_reviews, 
                                       key=lambda x: (x.get('helpful_votes', 0) if isinstance(x.get('helpful_votes', 0), (int, float)) else 0, 
                                                    x.get('rating', 0) if isinstance(x.get('rating', 0), (int, float)) else 0), 
                                       reverse=True)
                review = sorted_reviews[0]
                content = review.get('content', '') or review.get('text', '')
                rating = review.get('rating', 'N/A')
                verified = "(Verified)" if review.get('verified', False) else ""
                review_samples.append(f"Review from {source} {verified} (Rating: {rating}): {content}")
                sources_used.append(source)
        
        # Fill remaining slots with diverse ratings (positive, negative, mixed)
        if len(review_samples) < 10:
            # Get some positive reviews
            positive_reviews = [r for r in reviews if isinstance(r.get('rating', 0), (int, float)) and r.get('rating', 0) >= 4]
            for review in sorted(positive_reviews, key=lambda x: len(x.get('content', '') or x.get('text', '')), reverse=True)[:3]:
                if len(review_samples) >= 10:
                    break
                content = review.get('content', '') or review.get('text', '')
                rating = review.get('rating', 'N/A')
                source = review.get('source', 'Unknown')
                review_samples.append(f"Positive review (Rating: {rating}): {content}")
            
            # Get some negative reviews
            negative_reviews = [r for r in reviews if isinstance(r.get('rating', 0), (int, float)) and r.get('rating', 0) <= 2]
            for review in sorted(negative_reviews, key=lambda x: len(x.get('content', '') or x.get('text', '')), reverse=True)[:3]:
                if len(review_samples) >= 10:
                    break
                content = review.get('content', '') or review.get('text', '')
                rating = review.get('rating', 'N/A')
                source = review.get('source', 'Unknown')
                review_samples.append(f"Negative review (Rating: {rating}): {content}")
        
        # Create prompt for overall fashion product summary
        sources_list = ", ".join(set(sources_used))
        prompt = f"""
        Analyze these customer reviews about a fashion item (clothing, bag, or accessory). These reviews come from multiple sources: {sources_list}.
        
        REVIEWS:
        {chr(10).join(review_samples)}
        
        Based ONLY on these reviews, provide:
        1. A concise 2-3 sentence summary of what customers say about the fashion item overall
        2. List the top 5 most mentioned aspects (like fit, style, material, quality, value, etc.) with whether each aspect is viewed positively or negatively
        3. Overall product rating on a scale of 1-5 based on these reviews
        4. Percentage of positive vs. negative opinions
        5. Who this item would be best suited for (body type, style preference, occasion, etc.)
        
        Format your response as JSON with these keys: 
        "summary" (string), 
        "aspects" (array of objects with "name" and "sentiment" properties), 
        "rating" (number), 
        "positive_percentage" (number),
        "best_for" (string)
        """
        
        # Make API request with shorter timeout and reduced complexity
        try:
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json={
                    "model": "sonar",  # Using sonar model as specified in the memory
                    "messages": [
                        {
                            "role": "system",
                            "content": "You analyze product reviews and provide concise, accurate summaries in JSON format."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 400,  # Reduced from 800 to prevent timeout
                    "temperature": 0.1,
                    "stream": False
                },
                timeout=15  # Reduced timeout to fail faster
            )
        except requests.exceptions.Timeout:
            st.warning("Perplexity API request timed out. Using fallback summary.")
            # Provide a fallback summary
            return {
                "summary": "This fashion item has received mixed reviews with comments about fit, style, and quality.",
                "aspects": [
                    {"name": "Fit", "sentiment": "mixed"},
                    {"name": "Style", "sentiment": "positive"},
                    {"name": "Quality", "sentiment": "mixed"},
                    {"name": "Value", "sentiment": "positive"},
                    {"name": "Material", "sentiment": "mixed"}
                ],
                "rating": 3.5,
                "positive_percentage": 65,
                "best_for": "Suitable for most body types and casual occasions."
            }
        
        # Process response
        if response.status_code == 200:
            response_json = response.json()
            completion = response_json.get('choices', [{}])[0].get('message', {}).get('content', '{}')
            
            try:
                # Try to extract JSON from the completion
                json_match = re.search(r'```json\s*(.+?)\s*```', completion, re.DOTALL)
                if json_match:
                    completion = json_match.group(1)
                
                # Clean up any potential JSON issues
                completion = re.sub(r'\s*\n\s*', ' ', completion)  # Remove newlines
                completion = re.sub(r',\s*}', '}', completion)  # Remove trailing commas
                completion = re.sub(r',\s*]', ']', completion)  # Remove trailing commas in arrays
                
                # Fix common JSON formatting issues
                completion = re.sub(r'(\w+)\s*:\s*([^\s\{\[\"\d\-])', r'"\1": "\2', completion)  # Fix unquoted keys and values
                completion = re.sub(r'"([^"]+)"\s*:\s*([^\s\{\[\"\d\-])', r'"\1": "\2', completion)  # Fix unquoted values
                
                try:
                    result = json.loads(completion)
                    return result
                except:
                    # Try a more aggressive fix by wrapping all non-quoted values in quotes
                    completion = re.sub(r':\s*([^\s\{\[\"\d\-][^,\}\]]*)', r': "\1"', completion)
                    result = json.loads(completion)
                    return result
            except json.JSONDecodeError as e:
                st.warning(f"Could not parse product summary: {str(e)}. Using fallback summary.")
                # Return a fallback summary
                return {
                    "summary": "This fashion item has received mixed reviews with comments about fit, style, and quality.",
                    "aspects": [
                        {"name": "Fit", "sentiment": "mixed"},
                        {"name": "Style", "sentiment": "positive"},
                        {"name": "Quality", "sentiment": "mixed"},
                        {"name": "Value", "sentiment": "positive"},
                        {"name": "Material", "sentiment": "mixed"}
                    ],
                    "rating": 3.5,
                    "positive_percentage": 65,
                    "best_for": "Suitable for most body types and casual occasions."
                }
        else:
            st.warning(f"Error getting product summary: {response.status_code}")
            return {}
    except Exception as e:
        st.error(f"Error generating product summary: {str(e)}")
        return {}

def generate_category_analysis(reviews, categories):
    """Generate detailed analysis for each category using Perplexity API."""
    perplexity_key = os.getenv("PERPLEXITY_KEY")
    if not perplexity_key or not reviews or not categories:
        return {}
        
    try:
        st.info("Using Perplexity API to analyze product categories...")
        
        # Initialize the Perplexity client
        headers = {
            "Authorization": f"Bearer {perplexity_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        category_analysis = {}
        
        # Process each category
        for category_name, category_data in categories.items():
            # Get reviews for this category
            category_reviews = category_data.get('matching_reviews', [])
            if not category_reviews:
                continue
                
            # Prepare review samples (up to 10 reviews)
            review_samples = []
            
            # Sort reviews by rating to get a mix of positive and negative
            positive_reviews = [r for r in category_reviews if isinstance(r.get('rating', 0), (int, float)) and r.get('rating', 0) >= 4]
            negative_reviews = [r for r in category_reviews if isinstance(r.get('rating', 0), (int, float)) and r.get('rating', 0) <= 2]
            mixed_reviews = [r for r in category_reviews if r not in positive_reviews and r not in negative_reviews]
            
            # Add positive reviews
            for review in sorted(positive_reviews, key=lambda x: len(x.get('content', '') or x.get('text', '')), reverse=True)[:4]:
                if len(review_samples) >= 10:
                    break
                content = review.get('content', '') or review.get('text', '')
                rating = review.get('rating', 'N/A')
                review_samples.append(f"Positive review (Rating: {rating}): {content}")
            
            # Add negative reviews
            for review in sorted(negative_reviews, key=lambda x: len(x.get('content', '') or x.get('text', '')), reverse=True)[:4]:
                if len(review_samples) >= 10:
                    break
                content = review.get('content', '') or review.get('text', '')
                rating = review.get('rating', 'N/A')
                review_samples.append(f"Negative review (Rating: {rating}): {content}")
            
            # Add mixed reviews if needed
            for review in sorted(mixed_reviews, key=lambda x: len(x.get('content', '') or x.get('text', '')), reverse=True)[:2]:
                if len(review_samples) >= 10:
                    break
                content = review.get('content', '') or review.get('text', '')
                rating = review.get('rating', 'N/A')
                review_samples.append(f"Mixed review (Rating: {rating}): {content}")
                
            # Create prompt for this fashion category
            prompt = f"""
            Analyze these customer reviews about the '{category_name}' aspect of a fashion item (clothing, bag, or accessory).
            
            REVIEWS:
            {chr(10).join(review_samples)}
            
            Based ONLY on these reviews, provide:
            1. A concise 1-2 sentence summary of what customers say about the {category_name}
            2. Count of positive opinions about {category_name}
            3. Count of negative opinions about {category_name}
            4. One representative positive review example (direct quote)
            5. One representative negative review example (direct quote)
            6. List of specific sub-aspects of {category_name} that customers mention
            7. Style advice related to this aspect (e.g., for "fit" this might be "best for petite frames" or "size up if between sizes")
            
            Format your response as JSON with these keys: 
            "summary" (string), 
            "positive_count" (number), 
            "negative_count" (number), 
            "positive_example" (string), 
            "negative_example" (string), 
            "sub_aspects" (array of strings),
            "style_advice" (string)
            """
            
            # Make API request with better error handling
            try:
                response = requests.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers=headers,
                    json={
                        "model": "sonar",  # Using sonar model as specified in the memory
                        "messages": [
                            {
                                "role": "system",
                                "content": "You analyze product reviews and provide concise, accurate analysis in JSON format."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "max_tokens": 400,  # Reduced from 800 to prevent timeout
                        "temperature": 0.1,
                        "stream": False
                    },
                    timeout=15  # Reduced timeout to fail faster
                )
            except requests.exceptions.Timeout:
                st.warning(f"Perplexity API request timed out for {category_name}. Using fallback analysis.")
                # Create a fallback analysis based on the available data
                positive_count = len(positive_reviews)
                negative_count = len(negative_reviews)
                
                # Get a sample positive review if available
                pos_example = ""
                if positive_reviews and len(positive_reviews) > 0:
                    content = positive_reviews[0].get('content', '') or positive_reviews[0].get('text', '')
                    pos_example = content[:150] + "..." if len(content) > 150 else content
                
                # Get a sample negative review if available
                neg_example = ""
                if negative_reviews and len(negative_reviews) > 0:
                    content = negative_reviews[0].get('content', '') or negative_reviews[0].get('text', '')
                    neg_example = content[:150] + "..." if len(content) > 150 else content
                
                # Add fallback analysis to results
                category_analysis[category_name] = {
                    "summary": f"Customers have shared opinions about the {category_name.lower()} of this fashion item.",
                    "positive_count": positive_count,
                    "negative_count": negative_count,
                    "positive_example": pos_example,
                    "negative_example": neg_example,
                    "sub_aspects": [f"General {category_name}"],
                    "style_advice": f"Consider {category_name.lower()} carefully when making your purchase decision."
                }
                
                # Skip to next category
                continue
            
            # Process response
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # Extract JSON from the response
                try:
                    # Find JSON in the response (it might be wrapped in markdown code blocks)
                    json_match = re.search(r'```json\s*(.+?)\s*```', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1)
                    else:
                        json_str = content
                        
                    # Clean up the string and parse JSON
                    json_str = json_str.strip()
                    analysis_data = json.loads(json_str)
                    
                    # Store the analysis data
                    category_analysis[category_name] = analysis_data
                except (json.JSONDecodeError, ValueError) as e:
                    st.warning(f"Could not parse analysis for {category_name}: {str(e)}")
                    # Provide a fallback analysis
                    category_analysis[category_name] = {
                        "summary": f"Reviews discuss various aspects of the product's {category_name.lower()}.",
                        "positive_count": len(positive_reviews),
                        "negative_count": len(negative_reviews),
                        "positive_example": "This product has good features" if not positive_reviews else "",
                        "negative_example": "This product could be improved" if not negative_reviews else "",
                        "sub_aspects": [f"General {category_name}"]
                    }
            else:
                st.warning(f"Error getting analysis for {category_name}: {response.status_code}")
                
        return category_analysis
    except Exception as e:
        st.error(f"Error generating category analysis: {str(e)}")
        return {}

def _is_good_review_heuristic(review):
    """Helper function to determine if a review is good quality using heuristics"""
    content = review.get("content", "").lower()
    
    # Check for very short reviews
    if len(content) < 10:
        return False
        
    # Check for spam indicators but allow product URLs
    spam_indicators = ["click here", "buy now", "discount code", "follow me", "check out my"]
    if any(indicator in content for indicator in spam_indicators):
        return False
        
    # Less strict on capitalization - allow up to 70% uppercase
    if sum(1 for c in content if c.isupper()) / len(content) > 0.7:
        return False
        
    # Allow more punctuation for emphasis
    if any(char * 4 in content for char in "!?."):
        return False
        
    # Check for common spam patterns
    spam_patterns = [
        r'\b\d+\s*free\s*followers\b',
        r'\bfollow me\b',
        r'\bcheck out my\b',
        r'\bvisit\s+https?://\b'
    ]
    
    if any(re.search(pattern, content) for pattern in spam_patterns):
        return False
        
    # Check if content is just a product name or spec
    words = content.split()
    if len(words) < 5 and any(spec in content for spec in ['gb', 'inch', 'model', 'color']):
        return False
        
    return True
