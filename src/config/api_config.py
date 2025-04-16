import os
import streamlit as st

def validate_api_keys():
    """Validate API keys and return their status"""
    api_status = {}
    
    # Check SerpAPI key
    serpapi_key = os.getenv("SERPAPI_KEY")
    if not serpapi_key:
        api_status["serpapi"] = {"valid": False, "message": "SerpAPI key not found in .env file"}
    else:
        api_status["serpapi"] = {"valid": True, "message": "SerpAPI key found"}
    
    # Check Perplexity key
    perplexity_key = os.getenv("PERPLEXITY_KEY")
    if not perplexity_key:
        api_status["perplexity"] = {"valid": False, "message": "Perplexity key not found in .env file"}
    else:
        api_status["perplexity"] = {"valid": True, "message": "Perplexity key found"}
    
    # Check Firecrawl key
    firecrawl_key = os.getenv("FIRECRAWL_KEY")
    if not firecrawl_key:
        api_status["firecrawl"] = {"valid": False, "message": "Firecrawl key not found in .env file"}
    else:
        api_status["firecrawl"] = {"valid": True, "message": "Firecrawl key found"}
    
    return api_status
