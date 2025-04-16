import os
import requests
from dotenv import load_dotenv
from serpapi import GoogleSearch

# Load environment variables
load_dotenv()

def test_perplexity_api():
    """Test Perplexity API connection"""
    print("\nTesting Perplexity API...")
    
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('PERPLEXITY_KEY')}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": "Be precise and concise."
            },
            {
                "role": "user",
                "content": "How many stars are there in our galaxy?"
            }
        ],
        "max_tokens": 123,
        "temperature": 0.2
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        print("Response:", response.text[:500])
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_serpapi():
    """Test SerpAPI connection"""
    print("\nTesting SerpAPI...")
    
    try:
        # Test with a sample product ID
        params = {
            "api_key": os.getenv("SERPAPI_KEY"),
            "engine": "google_shopping",
            "q": "Samsung 65-inch QLED 4K TV",
            "gl": "us",
            "hl": "en",
            "location": "United States",
            "google_domain": "google.com",
            "device": "desktop"
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        print("Status: Success" if "error" not in results else f"Error: {results['error']}")
        if "error" not in results:
            print(f"Product Title: {results.get('title', 'Not found')}")
        return "error" not in results
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    perplexity_ok = test_perplexity_api()
    serpapi_ok = test_serpapi()
    
    print("\nAPI Test Results:")
    print(f"Perplexity API: {'✅ Working' if perplexity_ok else '❌ Failed'}")
    print(f"SerpAPI: {'✅ Working' if serpapi_ok else '❌ Failed'}")
