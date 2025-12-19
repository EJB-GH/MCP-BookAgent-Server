from fastmcp import FastMCP
import sys
import requests
import os

mcp = FastMCP("Book Agent Server")

"""
The concept of this MCP server is to provide book recommendations based on user input.
the tool should take the query and extract the book title and author
and then query the Google Books API to find similar books.

With a secondary tool that will use the google maps api to find nearby bookstores based
on the user's location input into the LLM

"""

cache = {
    "last_located_book": None
}

@mcp.tool()
def locate_book(book_title: str, author: str) -> dict:
    """
    Using information from the official site
    https://developers.google.com/books/docs/v1/using

    Here is an example of searching for Daniel Keyes' "Flowers for Algernon":

    GET https://www.googleapis.com/books/v1/volumes?q=flowers+inauthor:keyes&key=yourAPIKey
    switching to author and title search, genre can be extracted by the llm for recommendation purposes
    """
    
    starting_url = "https://www.googleapis.com/books/v1/volumes"
    response = requests.get(starting_url, params={
        "q": f"{book_title}+inauthor:{author}", "maxResults": 1})
    data = response.json()

    #check in case no results are found
    if "items" not in data:
        return "No books found matching the title and author, please try again."

    #extract book info from the json response
    book = data["items"][0]["volumeInfo"]
    title = book.get("title", "N/A")
    author = book.get("authors", ["N/A"])[0]
    categories = book.get("categories", ["N/A"])
    genre = categories[0] if categories else "N/A"

    clean_genre = genre.lower()
    for word in ["novel", "book", "story", "fiction"]:
        if word in clean_genre and len(clean_genre.split()) > 1:
            clean_genre = clean_genre.replace(word, "").strip()

    result = {"title": title, "author": author, "genre": clean_genre}

    # Cache the book for later use
    cache["last_located_book"] = result

    return result

@mcp.tool()
def recommend_books() -> dict:
    """
    Recommend books using ONLY the cached located book.
    """
    book = cache["last_located_book"]
    if not book:
        return {"error": "No book located yet. Use locate_book first."}

    title = book["title"]
    author = book["author"]
    genre = book["genre"]

    starting_url = "https://www.googleapis.com/books/v1/volumes"
    response = requests.get(starting_url, params={
        "q": f"subject:{genre}",
        "maxResults": 5
    })

    recommendations = []
    for item in response.json().get("items", []):
        info = item["volumeInfo"]
        rec_title = info.get("title", "N/A")
        rec_author = info.get("authors", ["N/A"])[0]

        if rec_title.lower().strip() != title.lower().strip():
            recommendations.append(f"{rec_title} by {rec_author}")
        
    print(f"Recommendations based on {title} by, {author}")

    return {"recommendations": recommendations}


@mcp.tool()
def find_bookstores(location: str) -> str:
    """
    Uses the google maps api to find bookstores based on the users location input, City,State
    should return up to 5 nearby stores using the places api as it allows searching based on queries
    https://developers.google.com/maps/documentation/places/web-service/text-search

    url = "https://places.googleapis.com/v1/places:searchText"
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    url = "https://places.googleapis.com/v1/places:searchText"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress"
    }
    payload = {
        "textQuery": f"bookstores in {location}",
        "includedType": "book_store",
        "maxResultCount": 5
    }

    #places had a table of types you can specify and book stores is one of them
    response = requests.post(url, headers=headers, json=payload) 
    data = response.json()

    #in case we search in the middle of nowhere
    if "places" not in data:
        return f"No bookstores found in {location}, please try again."
    #added a cool pin
    print(f"📍 Bookstores near {location}:\n")
    bookstores = []

    for place in data["places"]:
        name = place.get("displayName", {}).get("text", "N/A")
        address = place.get("formattedAddress", "N/A")
        bookstores.append(f"{name}, located at {address}")

    return "Nearby Bookstores:\n" + "\n".join(bookstores)


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8080)
