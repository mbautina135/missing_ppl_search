import requests
from datetime import datetime, timedelta
from config import load_config

# Your News API Key
API_KEY = "9569e8b3686948ff9b87d93a0c58f59e"

# API Endpoint
NEWS_API_URL = "https://newsapi.org/v2/everything"

# Define broader keywords and scenarios
QUERIES = [
    "car crash OR accident AND 'San Francisco'",
    "fight OR assault OR violent incident AND 'San Francisco'",
    "wildlife attack OR animal attack AND 'San Francisco'",
    "natural disaster OR earthquake OR flood AND 'San Francisco'",
    "human trafficking OR smuggling OR abduction AND 'San Francisco'",
    "terrorist attack OR explosion OR bombing AND 'San Francisco'",
    "lost hiker OR missing traveler AND 'San Francisco'",
    "rescue operation OR search mission AND 'San Francisco'",
    "San Francisco AND collision",
    "fatal incident AND 'San Francisco'",
    "major incident OR emergency AND 'San Francisco'",
    "breaking news OR urgent report AND 'San Francisco'",
    "evacuation order OR emergency response AND 'San Francisco'",
    "serious injury OR fatality AND 'San Francisco'",
    "vehicle collision OR traffic accident AND 'San Francisco'",
    "hit and run OR pedestrian accident AND 'San Francisco'",
    "public transit delay OR Muni disruption AND 'San Francisco'",
    "bridge accident OR ferry mishap AND 'San Francisco'",
    "armed robbery OR theft AND 'San Francisco'",
    "shooting OR gun violence AND 'San Francisco'",
    "domestic violence OR neighborhood disturbance AND 'San Francisco'",
    "cybercrime OR online scam AND 'San Francisco'",
    "drug bust OR illegal operation AND 'San Francisco'",
    "missing child OR missing adult AND 'San Francisco'",
    "search and rescue OR missing pet AND 'San Francisco'",
    "silver alert OR amber alert AND 'San Francisco'",
    "wildfire OR forest fire AND 'San Francisco'",
    "storm damage OR landslide AND 'San Francisco'",
    "tsunami warning OR extreme weather AND 'San Francisco'",
    "power outage OR blackout AND 'San Francisco'",
    "toxic spill OR hazardous material AND 'San Francisco'",
    "disease outbreak OR quarantine AND 'San Francisco'",
    "public health emergency OR contamination AND 'San Francisco'",
    "homeless crisis OR encampment issue AND 'San Francisco'",
    "protest OR demonstration AND 'San Francisco'",
    "community rally OR strike AND 'San Francisco'",
    "paranormal activity OR unexplained event AND 'San Francisco'",
    "rare phenomenon OR strange occurrence AND 'San Francisco'",
    "UFO sighting OR unidentified object AND 'San Francisco'",
    "celebrity scandal OR high-profile arrest AND 'San Francisco'",
    "white-collar crime OR embezzlement AND 'San Francisco'",
    "organized crime OR gang activity AND 'San Francisco'",
    "explosion OR chemical fire AND 'San Francisco'",
    "boat accident OR ferry crash AND 'San Francisco'",
    "construction accident OR workplace injury AND 'San Francisco'"
]


# Function to fetch articles for a given query
def fetch_articles(query, date_range=30, page_size=50):
    """
    Fetch news articles from News API based on a query.

    Args:
        query (str): Search terms (e.g., "sighting OR unidentified person").
        date_range (int): Number of past days to include in the search.
        page_size (int): Number of results to return per page (max 100).

    Returns:
        list: List of articles matching the query.
    """
    # Set date range
    today = datetime.now()
    from_date = (today - timedelta(days=date_range)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")

    config = load_config()
    
    # Define API parameters
    params = {
        "q": query,
        "from": from_date,
        "to": to_date,
        "language": "en",
        "sortBy": "popularity",  # Use popularity to find trending articles
        "apiKey": config.get("api_key", ""),
        "pageSize": page_size
    }

    

    # Make the API request
    response = requests.get(config.get("news_api_url", ""), params=params)

    if response.status_code == 200:
        return response.json().get("articles", [])
    else:
        print(f"Error fetching query '{query}': {response.status_code}, {response.json()}")
        return []


# Function to combine results from multiple queries
def fetch_combined_articles(queries, date_range=7):
    """
    Fetch articles for multiple queries and combine results.

    Args:
        queries (list): List of query strings.
        date_range (int): Number of past days to include in the search.

    Returns:
        list: Combined list of articles from all queries.
    """
    combined_articles = []
    for query in queries:
        print(f"Fetching articles for query: '{query}'")
        articles = fetch_articles(query, date_range)
        combined_articles.extend(articles)
    return combined_articles


# Function to display articles
def display_articles(articles):
    """
    Print a formatted list of articles.

    Args:
        articles (list): List of articles to display.
    """
    if not articles:
        print("No articles found.")
        return

    print(f"Found {len(articles)} articles:\n")
    for idx, article in enumerate(articles, start=1):
        print(f"{idx}. {article['title']}")
        print(f"   Source: {article['source']['name']}")
        print(f"   Published At: {article['publishedAt']}")
        print(f"   URL: {article['url']}\n")


# Main function
def main():
    # Fetch articles from all queries
    articles = fetch_combined_articles(QUERIES, date_range=14)  # Search the last 14 days

    # Display results
    display_articles(articles)


# Run the script
if __name__ == "__main__":
    main()
