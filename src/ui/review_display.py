import streamlit as st

def display_categorized_reviews(result):
    """Display reviews categorized by aspects with review sources."""
    reviews = result.get('reviews', [])
    metadata = result.get('metadata', {})
    product_summary = result.get('product_summary', {})
    
    # Add CSS for styling
    st.markdown("""
    <style>
    .review-box { border: 1px solid #e0e0e0; padding: 15px; margin-bottom: 15px; border-radius: 5px; }
    .review-rating { font-weight: bold; margin-bottom: 5px; }
    .review-title { font-weight: bold; margin-bottom: 10px; }
    .review-content { margin-bottom: 10px; }
    .review-meta { color: #666; font-size: 0.9em; }
    .verified-badge { color: #007600; }
    .aspect-box { border: 1px solid #e0e0e0; padding: 15px; margin-bottom: 15px; border-radius: 5px; background-color: #f9f9f9; }
    .positive { color: #007600; }
    .negative { color: #d32f2f; }
    .mixed { color: #ff9800; }
    .summary-box { border: 1px solid #e0e0e0; padding: 20px; margin-bottom: 25px; border-radius: 5px; background-color: #f5f5f5; }
    .aspect-tag { display: inline-block; background-color: #f1f8ff; padding: 4px 10px; margin-right: 8px; margin-bottom: 8px; border-radius: 16px; border: 1px solid #cce5ff; }
    .rating-pill { display: inline-block; padding: 5px 10px; border-radius: 20px; font-weight: bold; color: white; background-color: #4CAF50; }
    .stat-box { display: inline-block; padding: 10px; margin-right: 15px; margin-bottom: 15px; border-radius: 5px; background-color: #f1f8ff; border: 1px solid #cce5ff; }
    </style>
    """, unsafe_allow_html=True)
    
    # Display overall product summary if available
    if product_summary:
        st.markdown("## Product Summary")
        
        # Create summary box
        with st.container():
            st.markdown("<div class='summary-box'>", unsafe_allow_html=True)
            
            # Display summary text
            summary_text = product_summary.get('summary', 'No summary available')
            st.markdown(f"<p><strong>{summary_text}</strong></p>", unsafe_allow_html=True)
            
            # Display rating
            rating = product_summary.get('rating', 0)
            if isinstance(rating, (int, float)):
                stars = "⭐" * int(rating)
                st.markdown(f"<p>Overall Rating: <span class='rating-pill'>{rating:.1f} {stars}</span></p>", unsafe_allow_html=True)
            
            # Display positive percentage
            positive_pct = product_summary.get('positive_percentage', 0)
            if isinstance(positive_pct, (int, float)):
                st.progress(positive_pct/100, text=f"{positive_pct:.0f}% Positive Reviews")
            
            # Display product link if available
            product_link = metadata.get('product_link', '')
            product_id = metadata.get('product_id', '')
            product_thumbnail = metadata.get('product_thumbnail', '')
            
            if product_link:
                # Create shopping section with product image
                col1, col2 = st.columns([1, 2])
                
                # Display product image in the first column if available
                if product_thumbnail:
                    with col1:
                        st.image(product_thumbnail, width=150, caption="Product Image")
                
                # Display shopping info in the second column
                with col2:
                    st.subheader("Shopping Options")
                    st.write("Compare prices and check availability from multiple retailers")
                    st.markdown(f"""<a href="{product_link}" target="_blank" style="background-color: #4CAF50; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 5px 0; font-weight: bold;">Shop on Google</a>""", unsafe_allow_html=True)
                    st.caption("View pricing, read reviews, and find retailers for this product")
            
            if product_id:
                st.markdown(f"<p><strong>Product ID:</strong> <code>{product_id}</code></p>", unsafe_allow_html=True)
                # Add a direct link option as backup
                st.caption(f"If the shopping button doesn't work, [click here](https://www.google.com/shopping/product/{product_id}?hl=en&gl=us) to view the product.")
            
            # Display who this item is best for
            best_for = product_summary.get('best_for', '')
            if best_for:
                st.markdown(f"<p><strong>Best For:</strong> {best_for}</p>", unsafe_allow_html=True)
            
            # Display key aspects
            aspects = product_summary.get('aspects', [])
            if aspects:
                st.markdown("<p><strong>Key Fashion Aspects:</strong></p>", unsafe_allow_html=True)
                aspects_html = ""
                for aspect in aspects:
                    name = aspect.get('name', '')
                    sentiment = aspect.get('sentiment', 'mixed')
                    aspects_html += f"<span class='aspect-tag {sentiment.lower()}'>{name} ({sentiment})</span>"
                st.markdown(f"<div>{aspects_html}</div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Display review statistics
    avg_rating = metadata.get('average_rating', 0)
    if not isinstance(avg_rating, (int, float)):
        avg_rating = 0
    total_reviews = metadata.get('total_reviews', 0)
    if not isinstance(total_reviews, (int, float)):
        total_reviews = 0
    
    # Display header for categorized reviews
    st.markdown("## Product Aspects Analysis")
    st.markdown("Each aspect shows positive and negative opinions with example reviews.")
    
    # Display categorized reviews
    # Get all categories from the result that have data (excluding 'reviews' and 'metadata')
    category_keys = [key for key in result.keys() if key not in ['reviews', 'metadata', 'filters'] and isinstance(result[key], dict)]
    
    # Define icons for common categories
    category_icons = {
        "Fit": "👕",
        "Comfort": "🛋️",
        "Color": "🎨",
        "Stretchiness": "🧵",
        "Quality": "⭐",
        "Value for money": "💰",
        "Waist": "👖",
        "Material thickness": "📏",
        # Add fallback for any other categories
        "default": "📌"
    }
    
    # Create category objects with appropriate icons
    categories = []
    for cat_name in category_keys:
        icon = category_icons.get(cat_name, category_icons["default"])
        categories.append({"name": cat_name, "icon": icon})
    
    if not categories:
        st.warning("No categorized reviews available.")
        return
    
    # Create tabs for different categories
    tabs = st.tabs([f"{cat['icon']} {cat['name']}" for cat in categories])
    
    # Process each category
    for i, (tab, category) in enumerate(zip(tabs, categories)):
        with tab:
            cat_name = category['name']
            cat_data = result.get(cat_name, {})
            
            if isinstance(cat_data, dict) and cat_data:
                # Display category analysis if available
                analysis = cat_data.get('analysis', {})
                
                if analysis:
                    # Create an aspect box for this category
                    st.markdown(f"<div class='aspect-box'>", unsafe_allow_html=True)
                    
                    # Display the summary
                    summary_text = analysis.get('summary', f"Reviews about {cat_name}")
                    st.markdown(f"<h3>{cat_name}</h3>", unsafe_allow_html=True)
                    st.markdown(f"<p><strong>{summary_text}</strong></p>", unsafe_allow_html=True)
                    
                    # Display positive/negative counts
                    pos_count = analysis.get('positive_count', 0)
                    neg_count = analysis.get('negative_count', 0)
                    total = pos_count + neg_count
                    
                    if total > 0:
                        pos_percent = (pos_count / total) * 100
                        
                        # Display counts and percentage
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"<div class='stat-box positive'>👍 {pos_count} Positive Reviews</div>", unsafe_allow_html=True)
                        with col2:
                            st.markdown(f"<div class='stat-box negative'>👎 {neg_count} Negative Reviews</div>", unsafe_allow_html=True)
                        
                        # Display progress bar
                        st.progress(pos_percent/100, text=f"{pos_percent:.0f}% Positive")
                    
                    # Display sub-aspects
                    sub_aspects = analysis.get('sub_aspects', [])
                    if sub_aspects:
                        st.markdown("<p><strong>Specific aspects mentioned:</strong></p>", unsafe_allow_html=True)
                        aspects_html = ""
                        for aspect in sub_aspects:
                            aspects_html += f"<span class='aspect-tag'>{aspect}</span>"
                        st.markdown(f"<div>{aspects_html}</div>", unsafe_allow_html=True)
                    
                    # Display style advice
                    style_advice = analysis.get('style_advice', '')
                    if style_advice:
                        st.markdown(f"<p><strong>Style Advice:</strong> {style_advice}</p>", unsafe_allow_html=True)
                    
                    # Display example reviews
                    pos_example = analysis.get('positive_example', '')
                    neg_example = analysis.get('negative_example', '')
                    
                    if pos_example or neg_example:
                        st.markdown("<p><strong>Example Reviews:</strong></p>", unsafe_allow_html=True)
                        
                        if pos_example:
                            st.markdown(
                                f"""<div class='review-box'>
                                <div class='review-rating'>👍 Positive Example</div>
                                <div class='review-content'>\"{pos_example}\"</div>
                                </div>""", 
                                unsafe_allow_html=True
                            )
                        
                        if neg_example:
                            st.markdown(
                                f"""<div class='review-box'>
                                <div class='review-rating'>👎 Negative Example</div>
                                <div class='review-content'>\"{neg_example}\"</div>
                                </div>""", 
                                unsafe_allow_html=True
                            )
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    # Fallback to original summary
                    summary = cat_data.get('summary', f"Reviews about {cat_name}")
                    st.markdown(f"<h3>{cat_name}</h3>", unsafe_allow_html=True)
                    st.markdown(f"<p><strong>{summary}</strong></p>", unsafe_allow_html=True)
                    
                    # Get sentiment scores
                    sentiment_scores = cat_data.get('sentiment_scores', {'positive': 0, 'negative': 0})
                    pos = sentiment_scores.get('positive', 0)
                    neg = sentiment_scores.get('negative', 0)
                    total = pos + neg
                    
                    if total > 0:
                        pos_percent = (pos / total) * 100
                        st.progress(pos_percent/100, text=f"{pos_percent:.0f}% Positive")
                
                # Display review snippets
                snippets = cat_data.get('snippets', [])
                if snippets:
                    st.markdown("### Sample reviews")
                    for snippet in snippets[:3]:  # Show top 3 reviews
                        if isinstance(snippet, str):
                            # Simple string snippet
                            st.markdown(f"<div class='review-box'><div class='review-content'>\"{snippet}\"</div></div>", unsafe_allow_html=True)
                        elif isinstance(snippet, dict) and 'text' in snippet:
                            # Rich snippet with metadata
                            rating = snippet.get('rating', 5)
                            if not isinstance(rating, (int, float)):
                                rating = 5
                            
                            stars = "⭐" * int(rating)
                            title = snippet.get('title', 'Review')
                            text = snippet.get('text', '')
                            verified = snippet.get('verified', False)
                            source = snippet.get('source', '')
                            date = snippet.get('date', '')
                            
                            verified_badge = "<span class='verified-badge'>✓ Verified Purchase</span>" if verified else ""
                            
                            st.markdown(f"""
                            <div class='review-box'>
                                <div class='review-rating'>{stars}</div>
                                <div class='review-title'>{title}</div>
                                <div class='review-content'>\"{text}\"</div>
                                <div class='review-meta'>
                                    {verified_badge} {source} {date}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                else:
                    st.markdown("No specific reviews found for this category.")
            else:
                st.markdown(f"No data available for {cat_name}.")
    
    # Display all reviews section
    st.markdown("## All Reviews")
    if reviews:
        # Sort reviews by helpfulness and recency
        sorted_reviews = sorted(reviews, 
                              key=lambda x: (x.get('helpful_votes', 0) if isinstance(x.get('helpful_votes', 0), (int, float)) else 0, 
                                           x.get('date', '')), 
                              reverse=True)
        
        for i, review in enumerate(sorted_reviews[:5]):  # Show top 5 reviews
            rating = review.get('rating', 5)
            if not isinstance(rating, (int, float)):
                rating = 5
                
            stars = "⭐" * int(rating)
            title = review.get('title', 'Review')
            content = review.get('content', '')
            if not content and 'text' in review:
                content = review.get('text', '')
                
            verified = review.get('verified', False)
            source = review.get('source', '')
            date = review.get('date', '')
            helpful_votes = review.get('helpful_votes', 0)
            
            verified_badge = "<span class='verified-badge'>✓ Verified Purchase</span>" if verified else ""
            helpful_text = f"👍 {helpful_votes} found this helpful" if helpful_votes else ""
            
            with st.expander(f"{stars} {title}"):
                st.markdown(f"""
                <div class='review-content'>{content}</div>
                <div class='review-meta'>
                    {verified_badge} {source} {date} {helpful_text}
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("No reviews available.")

    

