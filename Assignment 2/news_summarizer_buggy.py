import requests
import os
from datetime import datetime

API_KEY = os.getenv("NEWSAPI_KEY") # Load API key from environment variable
BASE_URL = "https://newsapi.org/v2/everything" # support for date and keyword is only in v2 not v1

if not API_KEY:
    print("ERROR: Please set your API key in the env : NEWSAPI_KEY")
    exit(1)


def get_articles(keyword=None, from_date=None, to_date=None):
    url = BASE_URL
    params = {
        "domains": "bbc.co.uk",  # BBC cause of the sample output.
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
        response = requests.get(url, params=params, timeout=10) # HTTP request to NewsAPI
        
        # Check HTTP status code  
        if response.status_code == 401:  # 1.b
            print("Error 401: Invalid API key. Please check your NEWSAPI_KEY.")  
            return []  
        elif response.status_code == 429:  # 1.b
            print("Error 429: API rate limit exceeded. Please try again later.")  
            return []  
        elif response.status_code == 426:  # 1.b
            print("Error 426: HTTP 426 - Upgrade Required : Free plan works only for 30 days from current date")  # 1.b
            return []  # 1.b
        elif response.status_code != 200:  # 1.b
            print(f"Error: HTTP {response.status_code} - {response.reason}")  # 1.b
            return []  # 1.b  
        
        data = response.json() #API response from JSON
        
        # Check API response status
        if data.get("status") != "ok":
            error_message = data.get("message", "Unknown API error")  # 1.b
            print(f"API Error: {error_message}")
            return []  
            
        articles = data.get("articles", []) # articles from the API response
        if not articles:  
            print("No articles found for your search criteria.") 
            return [] 
            
        return articles # return articles from the API response
        
    #adding possibilites of exceptions, just for the sake of error handling - 1.b
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


def summarize(articles):
    if not articles:
        print("No articles found for your query.")
        return

    for i, art in enumerate(articles, start=1):
        title = art.get("title", "N/A")
        description = art.get("description", "N/A")
        url = art.get("url", "N/A")

        # print(f"\nArticle {i}")  # to show article numbers
        print(f"\nTitle       : {title}")
        print(f"Description : {description}")
        print(f"URL         : {url}")  
        print("-" * 4)


def main():
    print("News Search")
    keyword = input("Enter a keyword to filter (or leave blank): ").strip() or None
    from_date = input("Enter start date (DD-MM-YYYY, optional): ").strip() or None
    to_date = input("Enter end date (DD-MM-YYYY, optional): ").strip() or None

    # Validate dates if entered and convert to API format
    if from_date:
        try:  
            parsed_date = datetime.strptime(from_date, "%d-%m-%Y")
            from_date = parsed_date.strftime("%Y-%m-%d")  # Convert to YYYY-MM-DD for API
        except ValueError:
            print(f"Invalid from date: '{from_date}'. Use DD-MM-YYYY format (e.g., 25-12-2024).")  # 1.b
            return
            
    if to_date:
        try:  
            parsed_date = datetime.strptime(to_date, "%d-%m-%Y")
            to_date = parsed_date.strftime("%Y-%m-%d")  # Convert to YYYY-MM-DD for API
        except ValueError:
            print(f"Invalid to date: '{to_date}'. Use DD-MM-YYYY format (e.g., 25-12-2024).")  # 1.b
            return
    
    # Validate date range  # 1.b
    if from_date and to_date:  # 1.b
        from_dt = datetime.strptime(from_date, "%Y-%m-%d")  # 1.b
        to_dt = datetime.strptime(to_date, "%Y-%m-%d")  # 1.b
        if from_dt > to_dt:  # 1.b
            print("Error: From date cannot be later than to date.")  # 1.b
            return  # 1.b

    articles = get_articles(keyword, from_date, to_date)
    summarize(articles)


if __name__ == "__main__":
    main()
