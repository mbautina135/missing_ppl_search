import vertexai

from vertexai.generative_models import (
    GenerationConfig,
    GenerativeModel,
    Tool,
    grounding,
)

import requests
from datetime import datetime, timedelta
from vertexai.preview.generative_models import GenerativeModel
from config import load_config

# Function to fetch articles for a given query
def fetch_articles(query, date_range=30, page_size=50, api_key = None):
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
        "apiKey": api_key,
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
def fetch_combined_articles(date_range=7, api_key= None):
    """
    Fetch articles for multiple queries and combine results.

    Args:
        queries (list): List of query strings.
        date_range (int): Number of past days to include in the search.

    Returns:
        list: Combined list of articles from all queries.
    """
    queries = [
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
        "rare phenomenon OR strange occurrence AND 'San Francisco'",
        "celebrity scandal OR high-profile arrest AND 'San Francisco'",
        "white-collar crime OR embezzlement AND 'San Francisco'",
        "organized crime OR gang activity AND 'San Francisco'",
        "explosion OR chemical fire AND 'San Francisco'",
        "boat accident OR ferry crash AND 'San Francisco'",
        "construction accident OR workplace injury AND 'San Francisco'"
    ]
    combined_articles = []
    for query in queries:
        print(f"Fetching articles for query: '{query}'")
        articles = fetch_articles(query, date_range, api_key)
        combined_articles.extend(articles)
    return combined_articles

def write_articles_to_file(articles, file_path):
    """
    Write a formatted list of articles to a file.

    Args:
        articles (list): List of articles to write to the file.
        file_path (str): Path to the file where articles will be written.
    """
    with open(file_path, 'w') as file:
        if not articles:
            file.write("No articles found.\n")
            return

        file.write(f"Found {len(articles)} articles:\n\n")
        for idx, article in enumerate(articles, start=1):
            file.write(f"{idx}. {article['title']}\n")
            file.write(f"   Source: {article['source']['name']}\n")
            file.write(f"   Published At: {article['publishedAt']}\n")
            file.write(f"   URL: {article['url']}\n\n")


def validate_articles_with_gemini(articles):
    gemini_model = GenerativeModel('gemini-1.5-pro')
    prompt = """You are tasked with analyzing a list of articles to identify the ones that might provide clues about the whereabouts of a missing adult in San Francisco.
                The articles must focus on specific incidents or details that provide actionable hints about the missing person.

                Guidelines:
                
                Include Only Relevant Articles: Select articles that provide specific clues, such as sightings, found belongings, or witness accounts related to the missing person.
                Focus on San Francisco: The incident must have occurred within San Francisco and reference a specific location whenever possible.
                Exclude Duplicates: Ensure that each unique incident is included only once.
                Incident Types to Consider:
                Sightings or reports of individuals matching the missing person’s description.
                Found personal items such as clothing, identification, or belongings linked to the missing person.
                Witness reports or unusual events that could involve the missing person.
                Relevant accidents, emergencies, or violent incidents tied to specific locations.
                Note: Exclude generic articles that do not provide concrete information or actionable details about the missing person. 
                Focus on those that offer clear, location-specific clues or connections to the case."""
    prompt += '\n' + articles
    model_response = gemini_model.generate_content([prompt])
    return model_response.text

config = load_config()

vertexai.init(project=config.get("project_id", ""), location="us-central1")

model = GenerativeModel(config.get("llm_id", ""))

# Use Google Search for grounding
tool = Tool.from_google_search_retrieval(grounding.GoogleSearchRetrieval())

prompt = """Where did the event described below occured? 
Provide the most accurate latitude and longitude possible for the location of the event. 
If you cannot determine precise coordinates, specify the neighborhood, street, or landmark to refine the location as much as possible. Returning only the city is insufficient, as detailed location data is crucial for mapping and analysis.
Group of individuals, including 12-year-old, charged in $84K San Francisco robbery spree
Source: New York Post
Published At: 2024-11-22T03:51:16Z
URL: https://nypost.com/2024/11/21/us-news/gang-of-minors-including-a-12-year-old-charged-in-84k-sf-robbery-spree/"""
response = model.generate_content(
    prompt,
    tools=[tool],
    generation_config=GenerationConfig(
        temperature=0.0,
    ),
)

print(response.text)
# Example response:
# The next total solar eclipse visible from the contiguous United States will be on **August 23, 2044**.

