import requests
import os
import json
import time
import hashlib
from datetime import datetime, timedelta
from dotenv import load_dotenv
from collections import defaultdict, deque
import jwt

# Load environment variables
load_dotenv()

API_KEY = os.getenv("NEWSAPI_KEY")
BASE_URL = "https://newsapi.org/v2/everything"
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")

if not API_KEY:
    print("ERROR: Please set your API key in the env : NEWSAPI_KEY")
    exit(1)

# Simple in-memory cache
CACHE = {}
CACHE_TTL = 300  # 5 minutes cache

# Simple rate limiter
class RateLimiter:
    def __init__(self, max_requests=10, window=60):  # 10 requests per minute
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(deque)  # user_id -> deque of timestamps
    
    def is_allowed(self, user_id):
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Remove old requests outside the window
        while user_requests and user_requests[0] <= now - self.window:
            user_requests.popleft()
        
        # Check if under limit
        if len(user_requests) < self.max_requests:
            user_requests.append(now)
            return True
        return False
    
    def get_remaining_requests(self, user_id):
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Clean old requests
        while user_requests and user_requests[0] <= now - self.window:
            user_requests.popleft()
        
        return max(0, self.max_requests - len(user_requests))

# Initialize rate limiter
rate_limiter = RateLimiter()

# JWT Authentication
def generate_token(user_id):
    # Generate JWT token for user with 24 hour expiry
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_token(token):
    # Verify JWT token and return user_id
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        print("Token has expired. Please login again.")
        return None
    except jwt.InvalidTokenError:
        print("Invalid token.")
        return None

def login():
    # Simple login function for demo purposes
    print("\n=== Authentication ===")
    username = input("Enter username (or 'demo' for demo): ").strip()
    if not username:
        username = "demo"
    
    # In a real app, you'd verify against a database
    # For demo purposes, we'll just generate a token
    token = generate_token(username)
    print(f"Login successful! Token: {token[:20]}...")
    return token

# Simple caching functions
def get_cache_key(keyword, from_date, to_date):
    # Generate cache key from parameters using MD5 hash
    key_string = f"{keyword}_{from_date}_{to_date}"
    return hashlib.md5(key_string.encode()).hexdigest()

def get_from_cache(cache_key):
    # Get data from cache if not expired
    if cache_key in CACHE:
        data, timestamp = CACHE[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            print("Data served from cache")
            return data
        else:
            # Remove expired cache
            del CACHE[cache_key]
    return None

def save_to_cache(cache_key, data):
    # Save data to cache with current timestamp
    CACHE[cache_key] = (data, time.time())
    print("Data cached for future requests")

def get_articles(keyword=None, from_date=None, to_date=None, token=None):
    # Enhanced get_articles with caching and rate limiting
    
    # Verify authentication
    user_id = verify_token(token)
    if not user_id:
        return []
    
    # Check rate limiting
    if not rate_limiter.is_allowed(user_id):
        remaining = rate_limiter.get_remaining_requests(user_id)
        print(f"Rate limit exceeded. You can make {remaining} more requests in the next minute.")
        return []
    
    # Check cache first
    cache_key = get_cache_key(keyword, from_date, to_date)
    cached_data = get_from_cache(cache_key)
    if cached_data:
        return cached_data
    
    # Proceed with API call
    url = BASE_URL
    params = {
        "domains": "bbc.co.uk",
        "language": "en",
        "apiKey": API_KEY
    }
    
    # Add optional parameters if provided
    if keyword:
        params["q"] = keyword
    if from_date:
        params["from"] = from_date
    if to_date:
        params["to"] = to_date

    try:
        print("Fetching fresh data from API...")
        response = requests.get(url, params=params, timeout=10)
        
        # Check HTTP status code  
        if response.status_code == 401:
            print("Error 401: Invalid API key. Please check your NEWSAPI_KEY.")  
            return []  
        elif response.status_code == 429:
            print("Error 429: API rate limit exceeded. Please try again later.")  
            return []  
        elif response.status_code == 426:
            print("Error 426: HTTP 426 - Upgrade Required : Free plan works only for 30 days from current date")
            return []
        elif response.status_code != 200:
            print(f"Error: HTTP {response.status_code} - {response.reason}")
            return []  
        
        data = response.json()
        
        # Check API response status
        if data.get("status") != "ok":
            error_message = data.get("message", "Unknown API error")
            print(f"API Error: {error_message}")
            return []  
            
        articles = data.get("articles", [])
        if not articles:  
            print("No articles found for your search criteria.") 
            return [] 
        
        # Save to cache
        save_to_cache(cache_key, articles)
        
        # Show rate limit info
        remaining = rate_limiter.get_remaining_requests(user_id)
        print(f"API call successful. {remaining} requests remaining this minute.")
        
        return articles
        
    except requests.exceptions.Timeout: 
        print("Error: Request timed out. Please check your internet connection.") 
        return []  
    except requests.exceptions.ConnectionError:  
        print("Error: Unable to connect to the API. Please check your internet connection.")  
        return [] 
    except requests.exceptions.RequestException as e: 
        print(f"Network Error: {e}")  
        return [] 
    except ValueError as e:  
        print(f"Error parsing API response: {e}") 
        return []  
    except Exception as e:  
        print(f"Unexpected error: {e}")  
        return []

def format_date(date_string):
    # Format date string to readable format
    if not date_string or date_string == "N/A":
        return "N/A"
    
    try:
        # Parse ISO format date from API (e.g., "2024-01-15T10:30:00Z")
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        # Format to readable format (e.g., "15 Jan 2024, 10:30 AM")
        return dt.strftime("%d %b %Y, %I:%M %p")
    except:
        # If parsing fails, return original string
        return date_string

def summarize(articles):
    # Enhanced summarize function with user feedback and dates
    if not articles:
        print("No articles found for your query.")
        return

    print(f"\nFound {len(articles)} articles:")
    for i, art in enumerate(articles, start=1):
        title = art.get("title", "N/A")
        description = art.get("description", "N/A")
        url = art.get("url", "N/A")
        published_at = art.get("publishedAt", "N/A")
        source = art.get("source", {}).get("name", "N/A")

        # Format the publication date
        formatted_date = format_date(published_at)

        print(f"\nArticle {i}")
        print(f"Title       : {title}")
        print(f"Source      : {source}")
        print(f"Published   : {formatted_date}")
        print(f"Description : {description}")
        print(f"URL         : {url}")  
        print("-" * 50)

def main():
    # Enhanced main function with authentication
    print("Enhanced News Summarizer")
    print("Features: JWT Auth, Rate Limiting, Caching")
    
    # Authentication
    token = login()
    if not token:
        print("Authentication failed. Exiting...")
        return
    
    while True:
        print("\n" + "="*50)
        print("News Search")
        keyword = input("Enter a keyword to filter (or leave blank): ").strip() or None
        from_date = input("Enter start date (DD-MM-YYYY, optional): ").strip() or None
        to_date = input("Enter end date (DD-MM-YYYY, optional): ").strip() or None

        # Validate dates if entered and convert to API format
        if from_date:
            try:  
                parsed_date = datetime.strptime(from_date, "%d-%m-%Y")
                from_date = parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                print(f"Invalid from date: '{from_date}'. Use DD-MM-YYYY format (e.g., 25-12-2024).")
                continue
                
        if to_date:
            try:  
                parsed_date = datetime.strptime(to_date, "%d-%m-%Y")
                to_date = parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                print(f"Invalid to date: '{to_date}'. Use DD-MM-YYYY format (e.g., 25-12-2024).")
                continue
        
        # Validate date range
        if from_date and to_date:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d")
            to_dt = datetime.strptime(to_date, "%Y-%m-%d")
            if from_dt > to_dt:
                print("Error: From date cannot be later than to date.")
                continue

        # Get articles with enhanced features
        articles = get_articles(keyword, from_date, to_date, token)
        summarize(articles)
        
        # Ask if user wants to continue
        continue_search = input("\nSearch again? (y/n): ").strip().lower()
        if continue_search != 'y':
            break



if __name__ == "__main__":
    main()
