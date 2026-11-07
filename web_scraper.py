import requests
import csv
import io

# This is the link to the CSV that you can download from the website for the 24/25 season
url = "https://www.football-data.co.uk/mmz4281/2425/SP1.csv"  

#Retrieve the resource
response = requests.get(url)

# Raise an exception if there is a 400 or 500 error 
response.raise_for_status()

# csv.DictReader turns each row in the table into a dictionary. Column Title: Row Value at that column. matches is an iterator
matches = csv.DictReader(io.StringIO(response.text))

atleti_matches = []

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

# Data parallelism because it does the same task on many rows in the csv table
# Iterator of atleti_matches where each element is a normalized dictionary (only contains the fields we care about)
atleti_matches = map(normalize_match, filter(is_atleti_match, matches))

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

rivalries = calculate_rivalries(atleti_matches)
difficulties = assign_difficulty(rivalries)

ranked = sorted(
    difficulties.items(),
    key=lambda item: item[1],
    reverse=True
)

for opponent, difficulty in ranked:
    print(f"{opponent}: {difficulty}")

# --------  Debugging test 1
# counter=0
# for match in atleti_matches:
#     counter += 1
#     print(match)
# print(counter)

# print("\n\n\n")

# --------  Debugging test 2
# for opponent, stats in calculate_rivalries(atleti_matches).items():
#     print(opponent, stats)

# print("\n\n\n")

# --------  Debugging test 3
# rivalries = calculate_rivalries(atleti_matches)
# print(assign_difficulty(rivalries))