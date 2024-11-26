import requests
from datetime import datetime, timedelta

# Your News API Key
API_KEY = "2f5b1c4122784cb9b6943b6814a5485f"

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

    # Define API parameters
    params = {
        "q": query,
        "from": from_date,
        "to": to_date,
        "language": "en",
        "sortBy": "popularity",  # Use popularity to find trending articles
        "apiKey": API_KEY,
        "pageSize": page_size
    }

    # Make the API request
    response = requests.get(NEWS_API_URL, params=params)

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
