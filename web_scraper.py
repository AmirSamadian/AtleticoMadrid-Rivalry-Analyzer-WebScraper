import requests
import csv
import io
import itertools                                    # combines iterables
import time                                         # measures execution time
from concurrent.futures import ThreadPoolExecutor   # manages concurrent network requests


# Functions

def download_laliga_season_csv(url):
    #Retrieve the resource
    response = requests.get(url, timeout=15)

    # Raise an exception if there is a 400 or 500 error 
    response.raise_for_status()

    # csv.DictReader turns each row in the table into a dictionary. Column Title: Row Value at that column. matches is an iterator
    matches = csv.DictReader(io.StringIO(response.text))
    return matches

def is_atleti_match(match: dict) -> bool:
    return match["HomeTeam"] == "Ath Madrid" or match["AwayTeam"] == "Ath Madrid"

           
def normalize_match(match: dict):
    """Convert the raw, match dictionary provided by a row of the csv file into a dictionary containing only the fields relevant to our algorithm"""
    if match["HomeTeam"] == "Ath Madrid":
        opponent = match["AwayTeam"]
        goals_scored = int(match["FTHG"])    # Full time home goals
        goals_conceded = int(match["FTAG"])  # Full time away goals
    else:
        opponent = match["HomeTeam"]
        goals_scored = int(match["FTAG"])
        goals_conceded = int(match["FTHG"])
    
    atleti_match = {
        "date" : match["Date"],
        "opponent" : opponent,
        "goals_scored" : goals_scored,
        "goals_conceded": goals_conceded
    }            
    return atleti_match

def calculate_rivalries(atleti_matches) -> dict:
    rivalries = {}

    for match in atleti_matches:
        opponent = match["opponent"]

        if opponent not in rivalries:
            rivalries[opponent] = {
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals_scored": 0,
                "goals_conceded": 0
            }

        # Update rivalries[opponent]
        # Reminder that all of these stats are in the perspective of atletico madrid so goals_scored is how many atleti scored
        rivalries[opponent]["goals_scored"] += match["goals_scored"]

        rivalries[opponent]["goals_conceded"] += match["goals_conceded"]

        if match["goals_scored"] > match["goals_conceded"]:
            rivalries[opponent]["wins"] += 1
        elif match["goals_scored"] == match["goals_conceded"]:
            rivalries[opponent]["draws"] += 1
        elif match["goals_scored"] < match["goals_conceded"]:
            rivalries[opponent]["losses"] += 1

    return rivalries

# This is the "Scoring Algorithm" to determine how difficult an opponent is for atletico madrid. 
def assign_difficulty(rivalries: dict):
    opponent_difficulties = {}
    for opponent, stats in rivalries.items():
        difficulty = 0
        # This is based on how many points they made atletico madrid lose in laliga
        loss_penalty = stats["losses"] * 3
        draw_penalty = stats["draws"] * 2

        goal_difference = stats["goals_conceded"] - stats["goals_scored"]

        difficulty = loss_penalty + draw_penalty + goal_difference

        opponent_difficulties[opponent] = difficulty

    return opponent_difficulties


def main():
    # This provides the links to the CSV that you can download from the website for 2015–16 through 2024–25.
    season_urls = [
    f"https://www.football-data.co.uk/mmz4281/{year:02d}{year+1:02d}/SP1.csv"
    for year in range(15, 25)
    ]

    atleti_matches = []

    # Download multiple La Liga seasons concurrently using 5 worker threads
    with ThreadPoolExecutor(max_workers=5) as executor:
        seasons = list(executor.map(download_laliga_season_csv, season_urls))

    # Combine all downloaded seasons into one iterator of matches
    matches = itertools.chain.from_iterable(seasons)


    # Data parallelism because it does the same task on many rows in the csv table
    # Iterator of atleti_matches where each element is a normalized dictionary (only contains the fields we care about)
    atleti_matches = map(normalize_match, filter(is_atleti_match, matches))

    rivalries = calculate_rivalries(atleti_matches)
    difficulties = assign_difficulty(rivalries)

    ranked = sorted(
        difficulties.items(),
        key=lambda item: item[1],
        reverse=True
    )

    for opponent, difficulty in ranked:
        print(f"{opponent}: {difficulty}")

if __name__ == "__main__":
    main()