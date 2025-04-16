import os
import streamlit as st
from serpapi.google_search import GoogleSearch

def fetch_google_shopping_reviews(product_name):
    """Fetch reviews from Google Shopping using SerpAPI with enhanced product search and review collection"""
    serpapi_key = os.getenv("SERPAPI_KEY")
    if not serpapi_key:
        st.error("SerpAPI key is missing. Please add it to your .env file.")
        return {}
    try:
        # Display debug info
        masked_key = serpapi_key[:5] + '...' + serpapi_key[-5:] if len(serpapi_key) > 10 else '***'
        st.info(f"Debug: Using SerpAPI key: {masked_key}")
        st.info(f"Debug: Fetching reviews for product: {product_name}")
        
        # Validate product name
        if not product_name or len(product_name.strip()) < 3:
            st.error("Please provide a valid product name (at least 3 characters)")
            return []
        
        # First, get the product details with enhanced search
        params = {
            "api_key": serpapi_key,
            "engine": "google_shopping",
            "q": f"{product_name}",
            "gl": "us",
            "hl": "en",
            "location": "United States",
            "google_domain": "google.com",
            "device": "desktop",
            "num": "40",  # Increased for better coverage
            "start": "0",
            "safe": "active",
            "no_cache": "true"
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        # Check for API errors
        if "error" in results:
            error_msg = results["error"]
            st.error(f"SerpAPI error: {error_msg}")
            return {}
        
        # Extract product information and reviews
        shopping_results = results.get("shopping_results", [])
        if not shopping_results:
            # Try alternative search with broader terms
            alternative_terms = product_name.replace(' pro', '').replace(' max', '')
            params["q"] = alternative_terms
            search = GoogleSearch(params)
            results = search.get_dict()
            shopping_results = results.get("shopping_results", [])
            
            if not shopping_results:
                st.warning(f"Could not find product: {product_name}. This might be an unreleased or unavailable product.")
                return {}
        
        # Find best matching product with improved scoring
        best_product = None
        max_score = 0
        search_terms = set(product_name.lower().split())
        
        for product in shopping_results:
            title = product.get('title', '').lower()
            product_score = 0
            
            # Score based on word matches in title
            title_words = set(title.split())
            matching_words = search_terms & title_words
            product_score += len(matching_words) * 2
            
            # Bonus for exact phrase match
            if product_name.lower() in title:
                product_score += 5
            
            # Score based on review count if available
            review_count = product.get('reviews', 0)
            if isinstance(review_count, (int, float)) and review_count > 0:
                product_score += min(review_count / 100, 3)  # Cap at 3 points
            
            # Score based on rating if available
            rating = product.get('rating')
            if isinstance(rating, (int, float)) and rating > 0:
                product_score += min(rating / 2, 2)  # Cap at 2 points
            
            # Penalize if title suggests different model/version
            model_mismatch = False
            if 'pro' in product_name.lower() and 'pro' not in title:
                model_mismatch = True
            if 'max' in product_name.lower() and 'max' not in title:
                model_mismatch = True
            if model_mismatch:
                product_score -= 3
            
            if product_score > max_score:
                max_score = product_score
                best_product = product
        
        if not best_product:
            st.warning("Could not find an exact match for the product. Using best available alternative.")
            best_product = shopping_results[0]
        
        product_title = best_product.get('title', 'Unknown Product')
        st.success(f"Found product: {product_title}")
        
        # Now try to fetch reviews with the correct product title
        review_params = {
            "api_key": serpapi_key,
            "engine": "google_shopping",
            "q": f"{product_title} reviews",
            "gl": "us",
            "hl": "en",
            "num": "40"
        }
        
        try:
            review_search = GoogleSearch(review_params)
            review_results = review_search.get_dict()
            shopping_results = review_results.get("shopping_results", [])
        except Exception as e:
            st.warning(f"Error fetching reviews: {str(e)}")
            shopping_results = []
        
        # Process reviews and collect metadata
        # Extract and format the product link
        product_link = best_product.get('link', '')
        product_id = best_product.get('product_id', '')
        
        # Extract product thumbnail/image
        product_thumbnail = best_product.get('thumbnail', '')
        
        # Always construct the proper Google Shopping URL from the product_id
        # This is the format that works reliably based on SerpAPI documentation
        if product_id:
            # Format: https://www.google.com/shopping/product/{product_id}?hl=en&gl=us
            product_link = f"https://www.google.com/shopping/product/{product_id}?hl=en&gl=us"
            st.info(f"Debug: Product link constructed: {product_link}")
        elif product_link:
            st.info(f"Debug: Original product link found: {product_link}")
        else:
            st.warning("Debug: No product link or ID available")
            
        # Debug image info
        if product_thumbnail:
            st.info(f"Debug: Product image found: {product_thumbnail}")
        else:
            st.warning("Debug: No product image available")
            
        result = {
            'reviews': [],
            'metadata': {
                'total_reviews': 0,
                'average_rating': 0,
                'rating_distribution': {},
                'product_info': {
                    'title': product_title,
                    'description': best_product.get('description', ''),
                    'price': best_product.get('price', ''),
                    'features': best_product.get('features', [])
                },
                'product_link': product_link,
                'product_id': best_product.get('product_id', ''),
                'product_thumbnail': product_thumbnail,
                'variations': [],
                'related_products': []
            },
            'filters': []
        }
        seen_contents = set()
        # Try to get reviews from all matching products
        for product in shopping_results[:5]:  # Check top 5 matching products
            product_reviews = product.get('reviews', [])
            if not isinstance(product_reviews, (list, tuple)):
                continue
                
            for review_data in product_reviews:
                if not isinstance(review_data, dict):
                    continue
                    
                content = review_data.get('content', '')
                if not content or len(content) < 10:
                    continue
                    
                # Use content hash to avoid duplicates
                content_hash = hash(content.lower().strip())
                if content_hash not in seen_contents:
                    seen_contents.add(content_hash)
                    
                    # Safely get review data with type checking
                    rating = review_data.get('rating')
                    if not isinstance(rating, (int, float, str)):
                        rating = 'N/A'
                    
                    review = {
                        'content': content,
                        'rating': rating,
                        'author': str(review_data.get('author', 'Anonymous')),
                        'source': 'Google Shopping',
                        'date': str(review_data.get('date', '')),
                        'verified': bool(review_data.get('verified_purchase', False)),
                        'helpful_votes': int(review_data.get('helpful_votes', 0))
                    }
                    result['reviews'].append(review)
                    
                    # Update rating distribution
                    if isinstance(rating, (int, float)):
                        result['metadata']['rating_distribution'][rating] = result['metadata']['rating_distribution'].get(rating, 0) + 1
        
        if not result['reviews']:
            # If no reviews found in shopping results, try product endpoint
            product_id = best_product.get('product_id')
            if product_id:
                product_params = {
                    "api_key": serpapi_key,
                    "engine": "google_product",
                    "product_id": product_id,
                    "gl": "us",
                    "hl": "en"
                }
                
                try:
                    product_search = GoogleSearch(product_params)
                    product_results = product_search.get_dict()
                    
                    # Check if we have product results
                    if "product_results" in product_results:
                        product_data = product_results["product_results"]
                        
                        # Get reviews from product data
                        review_count = product_data.get("reviews", 0)
                        rating = product_data.get("rating", "N/A")
                        
                        # Check if this is a future/unreleased product
                        title = product_data.get("title", "").lower()
                        description = product_data.get("description", "").lower()
                        release_indicators = ["coming soon", "pre-order", "unreleased", "not yet available"]
                        is_unreleased = any(indicator in title or indicator in description for indicator in release_indicators)
                        
                        if is_unreleased:
                            st.warning("This appears to be an unreleased product. Reviews may be limited or speculative.")
                        
                        if review_count > 0:
                            st.info(f"Found {review_count} reviews with average rating {rating}")
                            
                            # First try to get reviews from reviews_results
                            if "reviews_results" in product_results:
                                reviews_data = product_results["reviews_results"]
                                
                                # Get rating distribution and filters
                                result['metadata']['rating_distribution'] = {
                                    rating_info['stars']: rating_info['amount']
                                    for rating_info in reviews_data.get('ratings', [])
                                    if isinstance(rating_info, dict) and 'stars' in rating_info and 'amount' in rating_info
                                }
                                
                                # Store review filters/aspects
                                result['filters'] = [
                                    {'label': f['label'], 'count': f['count']}
                                    for f in reviews_data.get('filters', [])
                                    if isinstance(f, dict) and 'label' in f and 'count' in f
                                ]
                                
                                # Show rating distribution info
                                if result['metadata']['rating_distribution']:
                                    st.info(f"Rating distribution: {result['metadata']['rating_distribution']}")
                                    
                                # If this is an unreleased product with suspiciously high review count,
                                # warn the user
                                total_reviews = sum(result['metadata']['rating_distribution'].values())
                                if is_unreleased and total_reviews > 1000:
                                    st.warning("⚠️ High review count for an unreleased product suggests these may be reviews for a different or previous model.")
                                
                                # Store product metadata
                                product_info = product_results.get('product_results', {})
                                result['metadata']['product_info'] = {
                                    'title': product_info.get('title'),
                                    'description': product_info.get('description'),
                                    'features': product_info.get('features', []),
                                    'highlights': product_info.get('highlights', []),
                                    'media': product_info.get('media', []),
                                    'specs': product_results.get('specs_results', {})
                                }
                                
                                # Store variations
                                variations = product_info.get('variations', {})
                                for var_type, var_options in variations.items():
                                    if isinstance(var_options, list):
                                        result['metadata']['variations'].append({
                                            'type': var_type,
                                            'options': [
                                                {
                                                    'name': opt.get('name'),
                                                    'thumbnail': opt.get('thumbnail'),
                                                    'selected': opt.get('selected', False)
                                                }
                                                for opt in var_options
                                                if isinstance(opt, dict)
                                            ]
                                        })
                                
                                # Store related products
                                related = product_results.get('related_products', {})
                                result['metadata']['related_products'] = [
                                    {
                                        'title': prod.get('title'),
                                        'price': prod.get('price'),
                                        'rating': prod.get('rating'),
                                        'reviews': prod.get('reviews'),
                                        'thumbnail': prod.get('thumbnail')
                                    }
                                    for prod in related.get('different_brand', [])
                                    if isinstance(prod, dict)
                                ]
                                
                                # Get total review count and rating data
                                total_reviews = product_data.get('total_reviews', 0)
                                rating_data = product_data.get('rating_breakdown', {})
                                if rating_data:
                                    for rating, count in rating_data.items():
                                        try:
                                            rating = int(float(rating))
                                            result['metadata']['rating_distribution'][rating] = count
                                        except (ValueError, TypeError):
                                            continue
                                    
                                # Process reviews from main product page
                                main_reviews = reviews_data.get('reviews', [])
                                if main_reviews:
                                    st.info(f"Found {len(main_reviews)} reviews from main product page")
                                    
                                for review_data in main_reviews:
                                    if not isinstance(review_data, dict):
                                        continue
                                        
                                    content = review_data.get("content", "")
                                    if not content or len(content) < 10:
                                        continue
                                        
                                    # For unreleased products, check if review mentions future tense
                                    if is_unreleased:
                                        future_words = ["will be", "coming", "expect", "hope", "can't wait", "looking forward"]
                                        if any(word in content.lower() for word in future_words):
                                            continue  # Skip speculative reviews
                                    
                                    title = review_data.get("title", "")
                                    if title:
                                        content = f"{title}\n{content}"
                                    
                                    content_hash = hash(content.lower().strip())
                                    if content_hash not in seen_contents:
                                        seen_contents.add(content_hash)
                                        
                                        # Parse rating
                                        try:
                                            rating = review_data.get("rating")
                                            if rating is not None:
                                                if isinstance(rating, str):
                                                    # Handle cases like "4.5 out of 5" or "4.5/5"
                                                    rating = rating.split()[0]
                                                rating = int(float(rating))
                                            else:
                                                rating = "N/A"
                                        except (ValueError, TypeError):
                                            rating = "N/A"
                                        
                                        review = {
                                            'content': content,
                                            'rating': rating,
                                            'author': str(review_data.get('author', 'Anonymous')),
                                            'source': review_data.get('source', 'Google Shopping'),
                                            'date': str(review_data.get('date', '')),
                                            'verified': True,
                                            'helpful_votes': int(review_data.get('helpful_votes', 0)),
                                            'position': review_data.get('position', 0),
                                            'title': review_data.get('title', ''),
                                        }
                                        result['reviews'].append(review)
                                        
                                        # Update rating distribution
                                        if isinstance(rating, (int, float)):
                                            result['metadata']['rating_distribution'][rating] = result['metadata']['rating_distribution'].get(rating, 0) + 1
                            
                            # If we still need more reviews, try seller offers
                            if len(result['reviews']) < review_count:
                                sellers = product_results.get("sellers_results", {}).get("online_sellers", [])
                                for offer in sellers:
                                    if not offer.get("offer_id"):
                                        continue
                                        
                                    seller_name = offer.get('name', 'Unknown Seller')
                                    try:
                                        review_params = {
                                            "api_key": serpapi_key,
                                            "engine": "google_product",
                                            "product_id": product_id,
                                            "offer_id": offer["offer_id"],
                                            "gl": "us",
                                            "hl": "en"
                                        }
                                        
                                        review_search = GoogleSearch(review_params)
                                        review_results = review_search.get_dict()
                                        
                                        if "error" in review_results:
                                            st.warning(f"Error from {seller_name}: {review_results['error']}")
                                            continue
                                            
                                        if "reviews_results" in review_results:
                                            seller_reviews = review_results["reviews_results"].get("reviews", [])
                                            if not seller_reviews:
                                                continue
                                                
                                            for review_data in seller_reviews:
                                                if not isinstance(review_data, dict):
                                                    continue
                                                    
                                                content = review_data.get("content", "")
                                                if not content or len(content) < 10:
                                                    continue
                                                    
                                                title = review_data.get("title", "")
                                                if title:
                                                    content = f"{title}\n{content}"
                                                    
                                                content_hash = hash(content.lower().strip())
                                                if content_hash not in seen_contents:
                                                    seen_contents.add(content_hash)
                                                    
                                                    try:
                                                        rating = review_data.get("rating")
                                                        rating = int(rating) if rating is not None else "N/A"
                                                    except (ValueError, TypeError):
                                                        rating = "N/A"
                                                    
                                                    review = {
                                                        "content": content,
                                                        "rating": rating,
                                                        "author": "Anonymous",
                                                        "source": f"Google Shopping - {seller_name}",
                                                        "date": str(review_data.get("date", "")),
                                                        "verified": True,
                                                        "helpful_votes": 0
                                                    }
                                                    result['reviews'].append(review)
                                                    
                                                    # Update rating distribution
                                                    if isinstance(rating, (int, float)):
                                                        result['metadata']['rating_distribution'][rating] = result['metadata']['rating_distribution'].get(rating, 0) + 1
                                            
                                            st.success(f"Found {len(seller_reviews)} reviews from {seller_name}")
                                    except Exception as e:
                                        st.warning(f"Error fetching reviews from {seller_name}: {str(e)}")
                                        continue
                except Exception as e:
                    st.warning(f"Could not fetch additional reviews: {str(e)}")
        
        # Final validation and cleanup
        if not result['reviews']:
            st.warning("No reviews found for this product. Try being more specific with the product name.")
            return result
            
        # Sort reviews by helpfulness and date
        result['reviews'].sort(key=lambda x: (x.get('helpful_votes', 0), x.get('date', '')), reverse=True)
        
        # Update metadata
        rating_dist = result['metadata']['rating_distribution']
        if rating_dist:
            total_ratings = sum(rating_dist.values())
            total_score = sum(rating * count for rating, count in rating_dist.items())
            result['metadata']['total_reviews'] = total_ratings
            result['metadata']['average_rating'] = round(total_score / total_ratings, 1)
            st.success(f"Found {total_ratings} total reviews with average rating {result['metadata']['average_rating']}")
            st.info(f"Rating distribution: {rating_dist}")
        else:
            # Fallback to using available reviews
            result['metadata']['total_reviews'] = len(result['reviews'])
            ratings = [r['rating'] for r in result['reviews'] if isinstance(r['rating'], (int, float))]
            if ratings:
                result['metadata']['average_rating'] = round(sum(ratings) / len(ratings), 1)
            st.success(f"Found {len(result['reviews'])} reviews")
        
        return result
    except Exception as e:
        st.error(f"Error fetching reviews from Google Shopping: {str(e)}")
        return {}
