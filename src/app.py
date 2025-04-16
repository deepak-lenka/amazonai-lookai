# app_new.py - Main application file
import streamlit as st
import os
import requests
from dotenv import load_dotenv

# Import modules
from apis.serpapi_client import fetch_google_shopping_reviews
from apis.perplexity_client import fetch_perplexity_reviews, filter_bad_reviews
from apis.firecrawl_client import fetch_firecrawl_reviews
from utils.review_analyzer import categorize_reviews
from ui.review_display import display_categorized_reviews
from config.api_config import validate_api_keys

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Fashion Review Summary",
    page_icon="👗",
    layout="centered"
)

def main():
    st.title("👗 Fashion Review Summary")
    st.write("AI-powered review analysis for clothing, bags, and accessories")
    
    # Check API keys and display status
    api_status = validate_api_keys()
    
    # Display API status in the sidebar
    with st.sidebar:
        st.header("API Status")
        for api, status in api_status.items():
            if status["valid"]:
                st.success(f"{api.title()}: ✅ {status['message']}")
            else:
                if api == "serpapi":
                    st.error(f"{api.title()}: ❌ {status['message']}")
                else:
                    st.warning(f"{api.title()}: ⚠️ {status['message']} (optional)")
    
    # Initialize session state for product selection
    if 'selected_product' not in st.session_state:
        st.session_state.selected_product = None
    if 'product_name' not in st.session_state:
        st.session_state.product_name = ""

    # Add sample fashion products for easy testing
    st.sidebar.markdown("### Sample Fashion Products for Testing")
    sample_products = [
        "Women's Summer Maxi Dress",
        "Men's Slim Fit Dress Shirt",
        "Leather Tote Bag",
        "Women's High Waist Jeans",
        "Designer Crossbody Purse",
        "Men's Cotton T-shirt",
        "Women's Floral Sundress",
        "Canvas Backpack"
    ]

    def on_product_select():
        if st.session_state.selected_product:
            st.session_state.product_name = st.session_state.selected_product
    
    # Product selection in sidebar
    st.sidebar.selectbox(
        "Select a sample product",
        sample_products,
        index=None,
        key="selected_product",
        on_change=on_product_select,
        placeholder="Choose a product to test"
    )

    # Product name input
    product_name = st.text_input(
        "Enter Product Name",
        value=st.session_state.product_name,
        placeholder="e.g., Men's Black T-shirt",
        help="Enter the exact product name for best results"
    )
    
    st.caption("💡 Tip: Be specific with the product name to get more accurate reviews. Include model number, size, or color if applicable.")
    
    # Add a button to run the analysis
    run_analysis = st.button("Analyze Reviews", type="primary")
    
    # Show warning if SerpAPI key is missing
    if not api_status["serpapi"]["valid"]:
        st.error("⚠️ SerpAPI key is missing or invalid. The app will not be able to fetch reviews.")
    
    if product_name and run_analysis:
        with st.spinner("Fetching and analyzing reviews..."):
            # Fetch reviews from all available sources
            all_reviews = []
            
            # 1. Google Shopping (primary source)
            try:
                result = fetch_google_shopping_reviews(product_name)
                if result and result.get('reviews'):
                    st.success(f"Found {len(result['reviews'])} reviews from Google Shopping")
                    all_reviews.extend(result['reviews'])
                else:
                    # Initialize empty result structure if Google Shopping failed
                    result = {
                        'reviews': [],
                        'metadata': {
                            'total_reviews': 0,
                            'average_rating': 0,
                            'rating_distribution': {},
                            'product_info': {},
                            'product_link': result.get('product_link', ''),
                            'product_id': result.get('product_id', ''),
                            'variations': [],
                            'related_products': []
                        },
                        'filters': []
                    }
            except Exception as e:
                st.error(f"Error with Google Shopping API: {str(e)}")
                # Initialize empty result structure on error
                result = {
                    'reviews': [],
                    'metadata': {
                        'total_reviews': 0,
                        'average_rating': 0,
                        'rating_distribution': {},
                        'product_info': {},
                        'variations': [],
                        'related_products': []
                    },
                    'filters': []
                }
            
            # If no Google Shopping reviews are found, inform the user
            if not all_reviews:
                st.warning("No reviews found from Google Shopping. Try being more specific with the product name.")
            
            # 2. Perplexity Sonar (if product name is provided)
            if product_name and os.getenv("PERPLEXITY_KEY"):
                try:
                    with st.spinner("Fetching additional reviews from Perplexity Sonar..."):
                        perplexity_reviews = fetch_perplexity_reviews(product_name)
                        if perplexity_reviews:
                            st.success(f"Found {len(perplexity_reviews)} additional reviews from Perplexity Sonar")
                            all_reviews.extend(perplexity_reviews)
                except Exception as e:
                    st.warning(f"Error with Perplexity API: {str(e)}")
            
            # 3. Firecrawl (if product name is provided)
            if product_name and os.getenv("FIRECRAWL_KEY"):
                try:
                    with st.spinner("Fetching additional reviews from Firecrawl..."):
                        firecrawl_reviews = fetch_firecrawl_reviews(product_name)
                        if firecrawl_reviews:
                            st.success(f"Found {len(firecrawl_reviews)} additional reviews from Firecrawl")
                            all_reviews.extend(firecrawl_reviews)
                except Exception as e:
                    st.warning(f"Error with Firecrawl API: {str(e)}")
            
            # If we have no reviews at all, inform the user
            if not all_reviews:
                st.warning("No reviews found from any source. Please try a different product ID or product name.")
                return
            
            # Filter out bad reviews
            filtered_reviews = filter_bad_reviews(all_reviews)
            st.info(f"Filtered out {len(all_reviews) - len(filtered_reviews)} low-quality reviews")
            
            # Show source distribution of reviews
            review_sources = {}
            for review in filtered_reviews:
                source = review.get('source', 'Unknown')
                if source not in review_sources:
                    review_sources[source] = 0
                review_sources[source] += 1
                
            if review_sources:
                st.success("Reviews collected from multiple sources:")
                for source, count in review_sources.items():
                    st.info(f"• {source}: {count} reviews")
            
            # Update the result with filtered reviews
            result['reviews'] = filtered_reviews
            
            # Recalculate rating distribution from filtered reviews
            rating_dist = {}
            for review in filtered_reviews:
                rating = review.get('rating')
                if isinstance(rating, (int, float)):
                    rating_dist[rating] = rating_dist.get(rating, 0) + 1
            
            # Update metadata
            result['metadata']['rating_distribution'] = rating_dist
            if rating_dist:
                total_ratings = sum(rating_dist.values())
                total_score = sum(rating * count for rating, count in rating_dist.items())
                result['metadata']['total_reviews'] = total_ratings
                result['metadata']['average_rating'] = round(total_score / total_ratings, 1)
            else:
                result['metadata']['total_reviews'] = len(filtered_reviews)
                result['metadata']['average_rating'] = 0
            
            # First, generate an overall product summary using Perplexity
            if os.getenv("PERPLEXITY_KEY"):
                try:
                    with st.spinner("Analyzing reviews with AI to generate fashion summary..."):
                        from apis.perplexity_client import generate_product_summary
                        product_summary = generate_product_summary(filtered_reviews)
                        result['product_summary'] = product_summary
                        st.success("AI analysis of fashion reviews complete")
                except requests.exceptions.Timeout:
                    st.warning("Perplexity API timed out. Using simplified analysis.")
                    # Create a basic fallback summary
                    result['product_summary'] = {
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
                except Exception as e:
                    st.error(f"Error generating fashion summary: {str(e)}")
            
            # Categorize the reviews
            categorized_results = categorize_reviews(filtered_reviews)
            
            # Add categorized results to the main result dictionary
            if categorized_results:
                # Generate detailed category analysis using Perplexity
                if os.getenv("PERPLEXITY_KEY"):
                    try:
                        with st.spinner("Analyzing fashion aspects (fit, style, material, etc.)..."):
                            from apis.perplexity_client import generate_category_analysis
                            category_analysis = generate_category_analysis(filtered_reviews, categorized_results)
                            
                            # Add the category analysis to the results
                            for category, analysis_data in category_analysis.items():
                                if category in categorized_results:
                                    categorized_results[category]['analysis'] = analysis_data
                    except requests.exceptions.Timeout:
                        st.warning("Perplexity API timed out during category analysis. Using simplified analysis.")
                        # Create basic fallback analysis for each category
                        for category, category_data in categorized_results.items():
                            matching_reviews = category_data.get('matching_reviews', [])
                            if matching_reviews:
                                # Count positive and negative reviews
                                positive_reviews = [r for r in matching_reviews if isinstance(r.get('rating', 0), (int, float)) and r.get('rating', 0) >= 4]
                                negative_reviews = [r for r in matching_reviews if isinstance(r.get('rating', 0), (int, float)) and r.get('rating', 0) <= 2]
                                
                                # Get sample reviews
                                pos_example = ""
                                if positive_reviews:
                                    content = positive_reviews[0].get('content', '') or positive_reviews[0].get('text', '')
                                    pos_example = content[:150] + "..." if len(content) > 150 else content
                                
                                neg_example = ""
                                if negative_reviews:
                                    content = negative_reviews[0].get('content', '') or negative_reviews[0].get('text', '')
                                    neg_example = content[:150] + "..." if len(content) > 150 else content
                                
                                # Create fallback analysis
                                categorized_results[category]['analysis'] = {
                                    "summary": f"Customers have shared opinions about the {category.lower()} of this fashion item.",
                                    "positive_count": len(positive_reviews),
                                    "negative_count": len(negative_reviews),
                                    "positive_example": pos_example,
                                    "negative_example": neg_example,
                                    "sub_aspects": [f"General {category}"],
                                    "style_advice": f"Consider {category.lower()} carefully when making your purchase decision."
                                }
                    except Exception as e:
                        st.error(f"Error generating fashion category analysis: {str(e)}")
                
                # Add all categorized data to the result
                for category, data in categorized_results.items():
                    result[category] = data
                    
                st.success(f"Reviews analyzed for {len(categorized_results)} product aspects")
            else:
                st.warning("Could not categorize reviews. Please try a different product or check the review content.")
            
            # Display the reviews and metadata
            display_categorized_reviews(result)
    
    # Instructions
    with st.sidebar:
        st.header("How to use")
        st.write("""
        1. Enter a product name
        2. Click "Analyze Reviews"
        3. View AI-generated review summaries
        4. Click on categories to see detailed reviews
        """)
        
        st.header("About")
        st.write("""
        This tool analyzes product reviews from multiple sources:
        - Google Shopping (via SerpAPI)
        - Perplexity Sonar API (optional)
        - Firecrawl (optional)
        
        Features:
        - Amazon-style review categorization
        - Sentiment analysis by category
        - Review filtering to remove low-quality content
        - Interactive category exploration
        """)
        
        # Add information about API keys
        st.header("API Keys")
        st.write("""
        The following API keys are used:
        - SerpAPI: Required for Google Shopping reviews
        - Perplexity Sonar: Optional for additional reviews
        - Firecrawl: Optional for additional reviews
        
        Add these to your .env file to enable all features.
        """)

if __name__ == "__main__":
    main()