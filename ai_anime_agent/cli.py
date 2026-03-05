"""Terminal interface for the anime agent."""

import argparse
from ai_anime_agent.agent import AnimeAgent


def main():
    parser = argparse.ArgumentParser(description="Anime video selector CLI")
    parser.add_argument("query", help="Search term for anime titles")
    args = parser.parse_args()

    # sample catalogue - in a real agent this might be loaded from API or DB
    catalogue = [
        {"title": "Naruto Shippuden Episode 1", "url": "https://example.com/naruto1"},
        {"title": "One Piece Episode 900", "url": "https://example.com/onepiece900"},
        {"title": "My Hero Academia Season 1", "url": "https://example.com/mha1"},
    ]
    agent = AnimeAgent(catalogue)
    results = agent.search(args.query)
    if not results:
        print("No matches found.")
        return

    print("Search results:")
    for i, item in enumerate(results):
        print(f"[{i}] {item['title']}")
    choice = input("Select index: ")
    try:
        idx = int(choice)
        selection = results[idx]
        print(f"Opening URL: {selection['url']}")
        # in real system might open in browser
    except Exception as e:
        print(f"Invalid selection: {e}")


if __name__ == "__main__":
    main()
