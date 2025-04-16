# Fashion Review Summary App

This Streamlit application provides AI-powered summaries of fashion product reviews, helping shoppers make informed decisions about clothing, bags, and accessories.

## Features

- Multi-source review collection from fashion retailers (Amazon, Nordstrom, Macy's, Zappos, ASOS, etc.)
- Fashion-specific categorization (Fit, Style, Comfort, Material, Color, Quality, Value, etc.)
- AI-powered analysis with style advice and recommendations
- "Best for" information about body types and occasions
- Product images and direct shopping links
- Interactive UI to explore fashion aspects
- Visual metrics and sentiment analysis

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your API keys:
```
SERPAPI_KEY=your_serp_api_key
PERPLEXITY_KEY=your_perplexity_api_key
FIRECRAWL_KEY=your_firecrawl_api_key
```

4. Run the application:
```bash
streamlit run src/app.py
```

## Usage

1. Enter a fashion item name (e.g., "Men's Black T-shirt" or "Women's Summer Maxi Dress")
2. Alternatively, select from the sample fashion products in the sidebar
3. Wait for the reviews to be fetched and analyzed from multiple sources
4. Explore different fashion aspects (fit, style, comfort, etc.)
5. View style advice and "best for" recommendations
6. Click the shopping button to purchase the item

## Note

Make sure you have valid API keys for:
- SerpAPI (for fetching Google Shopping reviews)
- Perplexity (for AI-powered fashion analysis)
- Firecrawl (for scraping fashion-specific websites)

The app will work with limited functionality if some API keys are missing.
