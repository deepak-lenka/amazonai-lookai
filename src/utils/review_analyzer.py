import re
from datetime import datetime

def categorize_reviews(reviews):
    """Categorize reviews into Amazon-style aspects and include review sources."""
    if not reviews:
        return {}
        
    # Fashion-focused categories with specific keywords and sub-aspects
    categories = {
        "Fit": {
            "keywords": ["fit", "fits", "fitting", "size", "sizing", "snug", "tight", "loose", "big", "small", "large", "medium", "petite", "plus"],
            "sub_aspects": ["overall fit", "sizing accuracy", "true to size", "runs small", "runs large", "length", "body type"]
        },
        "Style": {
            "keywords": ["style", "design", "look", "fashion", "trendy", "classic", "cute", "elegant", "chic", "pattern", "aesthetic"],
            "sub_aspects": ["appearance", "design elements", "fashion appeal", "versatility", "uniqueness"]
        },
        "Comfort": {
            "keywords": ["comfort", "comfortable", "soft", "cozy", "itchy", "scratchy", "breathable", "feel", "wearable", "irritating"],
            "sub_aspects": ["comfort level", "softness", "all-day wear", "skin feel", "breathability"]
        },
        "Material": {
            "keywords": ["material", "fabric", "cotton", "polyester", "silk", "linen", "leather", "synthetic", "wool", "blend", "canvas", "denim"],
            "sub_aspects": ["fabric quality", "texture", "feel", "composition", "eco-friendly"]
        },
        "Color": {
            "keywords": ["color", "shade", "tone", "hue", "vibrant", "dull", "bright", "dark", "light", "faded", "match", "dye"],
            "sub_aspects": ["color accuracy", "color options", "color consistency", "color matching", "color fading"]
        },
        "Quality": {
            "keywords": ["quality", "durable", "sturdy", "craftsmanship", "stitching", "seams", "construction", "lasting", "wear", "tear", "workmanship"],
            "sub_aspects": ["overall quality", "stitching quality", "durability", "defects", "longevity"]
        },
        "Value": {
            "keywords": ["price", "value", "worth", "expensive", "cheap", "cost", "investment", "budget", "deal", "bargain", "money", "affordable"],
            "sub_aspects": ["price point", "value proposition", "cost vs quality", "market comparison", "discounts/deals"]
        },
        "Occasion": {
            "keywords": ["occasion", "casual", "formal", "work", "office", "party", "wedding", "everyday", "special", "event", "versatile"],
            "sub_aspects": ["versatility", "appropriateness", "formal wear", "casual wear", "special events"]
        },
        "Details": {
            "keywords": ["details", "zipper", "button", "pocket", "strap", "handle", "clasp", "buckle", "hardware", "embellishment", "decoration"],
            "sub_aspects": ["functional details", "decorative elements", "hardware quality", "usability", "design features"]
        },
        "Maintenance": {
            "keywords": ["wash", "washing", "clean", "cleaning", "care", "iron", "wrinkle", "stain", "maintain", "maintenance", "laundry"],
            "sub_aspects": ["ease of cleaning", "wrinkle resistance", "care instructions", "stain resistance", "maintenance requirements"]
        }
    }
    
    # Initialize results dictionary
    results = {}
    
    # Sentiment analysis configuration
    sentiment_indicators = {
        "positive": {
            "words": ["excellent", "amazing", "great", "good", "love", "perfect", "recommend", "fantastic", "wonderful", "best", "awesome", "satisfied", "pleased", "impressive", "superb"],
            "phrases": ["worth every penny", "highly recommend", "very happy", "no complaints", "exceeded expectations"]
        },
        "negative": {
            "words": ["poor", "terrible", "bad", "awful", "horrible", "disappointing", "avoid", "worst", "regret", "waste", "defective", "broken", "cheap", "frustrated"],
            "phrases": ["waste of money", "don't buy", "not worth", "very disappointed", "would not recommend"]
        }
    }
    
    # Process each category
    for category, data in categories.items():
        matching_reviews = []
        category_aspects = {aspect: [] for aspect in data["sub_aspects"]}
        
        # Find matching reviews and categorize by sub-aspects
        for review in reviews:
            content = review.get("content", "") or review.get("text", "")
            if not content:
                continue
                
            content = content.lower()
            
            # Use word boundaries for more accurate matching
            matched = False
            for keyword in data["keywords"]:
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                if re.search(pattern, content):
                    matching_reviews.append(review)
                    matched = True
                    break
            
            # If matched, categorize into sub-aspects
            if matched:
                for aspect in data["sub_aspects"]:
                    if any(re.search(r'\b' + re.escape(keyword.lower()) + r'\b', content) for keyword in aspect.split('/')):
                        category_aspects[aspect].append(review)
        
        if matching_reviews:
            # Calculate sentiment scores
            sentiment_scores = {
                "positive": 0,
                "negative": 0,
                "verified_positive": 0,
                "verified_negative": 0
            }
            
            for review in matching_reviews:
                content = review.get("content", "") or review.get("text", "")
                if not content:
                    continue
                    
                content = content.lower()
                is_verified = review.get("verified", False)
                rating = review.get("rating", 0)
                
                # Count sentiment indicators with word boundaries for accuracy
                pos_count = 0
                for word in sentiment_indicators["positive"]["words"]:
                    pattern = r'\b' + re.escape(word.lower()) + r'\b'
                    if re.search(pattern, content):
                        pos_count += 1
                
                for phrase in sentiment_indicators["positive"]["phrases"]:
                    if phrase.lower() in content:
                        pos_count += 2  # Phrases are stronger indicators
                
                neg_count = 0
                for word in sentiment_indicators["negative"]["words"]:
                    pattern = r'\b' + re.escape(word.lower()) + r'\b'
                    if re.search(pattern, content):
                        neg_count += 1
                
                for phrase in sentiment_indicators["negative"]["phrases"]:
                    if phrase.lower() in content:
                        neg_count += 2  # Phrases are stronger indicators
                
                # Also consider rating if available
                if isinstance(rating, (int, float)):
                    if rating >= 4:
                        pos_count += 1
                    elif rating <= 2:
                        neg_count += 1
                
                # Weight verified reviews more heavily
                weight = 1.5 if is_verified else 1.0
                
                if pos_count > neg_count:
                    sentiment_scores["positive"] += weight
                    if is_verified:
                        sentiment_scores["verified_positive"] += 1
                elif neg_count > pos_count:
                    sentiment_scores["negative"] += weight
                    if is_verified:
                        sentiment_scores["verified_negative"] += 1
            
            # Determine overall sentiment
            total_positive = sentiment_scores["positive"]
            total_negative = sentiment_scores["negative"]
            sentiment = "positive" if total_positive > total_negative else "negative" if total_negative > total_positive else "mixed"
            
            # Generate detailed summary
            verified_count = sentiment_scores["verified_positive"] + sentiment_scores["verified_negative"]
            total_count = len(matching_reviews)
            
            if sentiment == "positive":
                summary = f"Strong positive feedback on {category.lower()}, with {sentiment_scores['verified_positive']} verified positive reviews. "
                if category_aspects:
                    top_aspects = sorted(category_aspects.items(), key=lambda x: len(x[1]), reverse=True)[:2]
                    if top_aspects:
                        summary += f"Particularly praised for {', '.join(aspect for aspect, _ in top_aspects)}."
            elif sentiment == "negative":
                summary = f"Notable concerns about {category.lower()}, with {sentiment_scores['verified_negative']} verified negative reviews. "
                if category_aspects:
                    top_aspects = sorted(category_aspects.items(), key=lambda x: len(x[1]), reverse=True)[:2]
                    if top_aspects:
                        summary += f"Main issues reported with {', '.join(aspect for aspect, _ in top_aspects)}."
            else:
                summary = f"Mixed opinions on {category.lower()}, with balanced positive and negative feedback. "
                if verified_count:
                    summary += f"Including {verified_count} verified purchaser reviews."

            # Select the most helpful and relevant snippets with enhanced scoring
            snippets = []
            scored_snippets = []
            
            for review in matching_reviews:
                content = review.get("content", "") or review.get("text", "")
                if not content:
                    continue
                    
                source = review.get("source", "Unknown")
                is_verified = review.get("verified", False)
                helpful_votes = review.get("helpful_votes", 0)
                if not isinstance(helpful_votes, (int, float)):
                    helpful_votes = 0
                rating = review.get("rating", 0)
                if not isinstance(rating, (int, float)):
                    rating = 0
                rating = review.get("rating", 0)
                date = review.get("date", "")
                
                # Split into sentences and score each one
                sentences = re.split(r'[.!?]\s+', content)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) < 10:  # Skip very short sentences
                        continue
                        
                    # Enhanced sentence relevance scoring
                    keyword_matches = sum(keyword in sentence.lower() for keyword in data["keywords"])
                    aspect_matches = sum(aspect in sentence.lower() for aspect in data["sub_aspects"])
                    detail_score = len(re.findall(r'\b\w+\b', sentence)) / 50.0  # Normalize by 50 words
                    sentiment_score = sum(word in sentence.lower() for word in sentiment_indicators["positive"]["words"]) - \
                                     sum(word in sentence.lower() for word in sentiment_indicators["negative"]["words"])
                    
                    # Calculate recency score (newer reviews get higher scores)
                    recency_score = 0
                    if date:
                        try:
                            review_date = datetime.strptime(date, "%Y-%m-%d")
                            days_old = (datetime.now() - review_date).days
                            recency_score = max(0, 1 - (days_old / 365))  # Decay over a year
                        except:
                            recency_score = 0.5  # Default score for reviews without dates
                    
                    # Enhanced scoring system based on Notion requirements
                    # Ensure rating is a numeric value before using it in calculations
                    rating_score = 0.0
                    if isinstance(rating, (int, float)):
                        rating_score = (rating / 5.0) * 2.0
                    
                    total_score = (
                        keyword_matches * 3.0 +      # Keywords are critical
                        aspect_matches * 2.5 +       # Aspects are highly relevant
                        detail_score * 2.0 +         # Detailed reviews preferred
                        (helpful_votes * 1.0) +      # Community validation
                        (3.0 if is_verified else 0.0) + # Verified purchases prioritized
                        rating_score +               # Rating weight increased
                        sentiment_score * 1.5 +      # Clear sentiment importance
                        recency_score * 2.5          # Recent reviews heavily favored
                    )
                    
                    # Create rich snippet with metadata
                    scored_snippets.append({
                        "text": sentence,
                        "source": source,
                        "rating": rating,
                        "date": date,
                        "verified": is_verified,
                        "helpful_votes": helpful_votes,
                        "score": total_score,
                        "verified": is_verified,
                        "rating": rating,
                        "date": date
                    })
            
            # Sort snippets by score and select top ones
            scored_snippets.sort(key=lambda x: x["score"], reverse=True)
            selected_snippets = scored_snippets[:10]  # Get top 10 snippets
            
            # Create rich snippets with all metadata
            rich_snippets = []
            for s in selected_snippets:
                rich_snippet = {
                    'text': s['text'],
                    'source': s['source'],
                    'verified': s['verified'],
                    'rating': s['rating'],
                    'date': s['date'],
                    'helpful_votes': s.get('helpful_votes', 0)
                }
                rich_snippets.append(rich_snippet)
            
            # Calculate positive percentage
            total_sentiment = sentiment_scores["positive"] + sentiment_scores["negative"]
            positive_percent = (sentiment_scores["positive"] / total_sentiment * 100) if total_sentiment > 0 else 50
            
            # Create category-specific summaries
            if category == "Fit":
                if positive_percent >= 70:
                    custom_summary = "Most customers find the fit excellent. Reviews indicate the product is true to size and fits as expected."
                elif positive_percent >= 50:
                    custom_summary = "Customers generally like the fit, though some mention sizing issues. Consider checking size charts before ordering."
                else:
                    custom_summary = "Many customers have concerns about the fit. Common issues include sizing inconsistency and fit problems."
            elif category == "Comfort":
                if positive_percent >= 70:
                    custom_summary = "Customers rave about the comfort. Many mention the softness and excellent support."
                elif positive_percent >= 50:
                    custom_summary = "Most customers find this product comfortable, though some mention it could be improved."
                else:
                    custom_summary = "Comfort is a concern for many customers. Issues mentioned include lack of padding and support."
            elif category == "Color":
                if positive_percent >= 70:
                    custom_summary = "Customers love the color. Many mention it matches the product images perfectly."
                elif positive_percent >= 50:
                    custom_summary = "Color is generally well-received, though some note slight variations from what's shown online."
                else:
                    custom_summary = "Many customers are disappointed with the color. Common complaints include fading and color mismatch."
            elif category == "Stretchiness":
                if positive_percent >= 70:
                    custom_summary = "The stretchiness gets high marks. Customers appreciate the flexibility and movement it allows."
                elif positive_percent >= 50:
                    custom_summary = "Stretchiness is generally good according to most reviews, with some minor concerns."
                else:
                    custom_summary = "Many customers find issues with the stretchiness. Common complaints include lack of give and recovery."
            elif category == "Quality":
                if positive_percent >= 70:
                    custom_summary = "Quality is excellent according to most reviews. Customers praise the materials and construction."
                elif positive_percent >= 50:
                    custom_summary = "Overall quality is good, though some customers mention room for improvement in certain aspects."
                else:
                    custom_summary = "Quality concerns are mentioned by many customers. Issues include durability problems and material flaws."
            elif category == "Value for money":
                if positive_percent >= 70:
                    custom_summary = "Customers feel this product offers excellent value for money. Many mention it exceeds expectations for the price."
                elif positive_percent >= 50:
                    custom_summary = "Most customers think the price is fair for what you get, though some expected more at this price point."
                else:
                    custom_summary = "Many customers feel this product is overpriced for the quality received."
            elif category == "Waist":
                if positive_percent >= 70:
                    custom_summary = "The waist fit is excellent according to most reviews. Customers mention good comfort and support."
                elif positive_percent >= 50:
                    custom_summary = "Waist fit is generally good, though some mention it could be more comfortable or supportive."
                else:
                    custom_summary = "Many customers have issues with the waist fit. Common complaints include tightness and lack of stretch."
            elif category == "Material thickness":
                if positive_percent >= 70:
                    custom_summary = "Customers are very satisfied with the material thickness. Many mention it's just right for the purpose."
                elif positive_percent >= 50:
                    custom_summary = "Material thickness is generally well-received, though opinions vary on whether it's too thick or thin."
                else:
                    custom_summary = "Many customers are disappointed with the material thickness. Common complaints include it being too thin or flimsy."
            else:
                # Use the general summary for other categories
                custom_summary = summary
            
            # Store results with enhanced metadata
            results[category] = {
                "summary": custom_summary,
                "sentiment": sentiment,
                "review_count": total_count,
                "verified_count": verified_count,
                "snippets": rich_snippets,
                "aspect_breakdown": {
                    aspect: len(reviews) 
                    for aspect, reviews in category_aspects.items() 
                    if reviews
                },
                "sentiment_scores": sentiment_scores,
                "positive_percent": positive_percent
            }
    
    return results
