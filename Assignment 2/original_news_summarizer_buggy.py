import requests
import json

API_KEY = "INSERT_YOUR_API_KEY"
BASE_URL = "https://newsapi.org/v1/articles"


def get_articles():
    url = f"{BASE_URL}?source=bbc-news&apiKey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json()['articles']
        return articles
    else:
        print("Failed to fetch news")
        return []


def summarize(articles):
    for art in articles:
        print("Title:", art['title'])
        print("Description:", art['description'])
        print("URL:", art['url'])
        print("----")


def main():
    try:
        articles = get_articles()
        if articles:
            summarize(articles)
    except:
        print("Something went wrong")


main()
