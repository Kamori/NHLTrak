from icecream import ic

from pony.orm import db_session

from datetime import datetime, timedelta
from dateutil import parser

from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder

from nhlpy import NHLClient
from nhlpy.api.query.builder import QueryBuilder, QueryContext
from nhlpy.api.query.filters.season import SeasonQuery

from pony.orm import TransactionIntegrityError

from db_connection import init_db, db
from db_models.entities import Team, Player, PlayerTeamSeason
from db_helpers import create_db_helper


db = init_db(create_tables=True)

db_helper = create_db_helper(db)

nhl_client = NHLClient()

player_router = APIRouter()

current_season = datetime.now().year

if datetime.now().month >= 1 and datetime.now().month <= 4:
    current_season = str(current_season - 1) + str(current_season)
else:
    current_season = str(current_season) + str(current_season + 1)


async def _update_team_roster(team_id: int, team_abbr: str, season: str):
    """
    Helper function to fetch and update team roster from the NHL API.

    Parameters:
        team_id: The ID of the team.
        team_abbr: The team abbreviation.
        season: The season string.

    Returns:
        Updated list of players from the database.
    """
    players = nhl_client.players.players_by_team(team_abbr, season)

    team = db.get_by_id(Team, team_id)

    for position in players:
        for player in players[position]:
            birth_province_state = player.get("birthStateProvince", {}).get("default")

            data = {
                "id": player["id"],
                "first_name": player["firstName"]["default"],
                "last_name": player["lastName"]["default"],
                "birth_date": player["birthDate"],
                "birth_city": player["birthCity"]["default"],
                "birth_country": player["birthCountry"],
                "birth_province_state": birth_province_state,
                "position": player["positionCode"],
                "shoots_catches": player["shootsCatches"],
                "height_in_centimeters": player["heightInCentimeters"],
                "height_in_inches": player["heightInInches"],
                "weight_in_kilograms": player["weightInKilograms"],
                "weight_in_pounds": player["weightInPounds"],
                "headshot": player["headshot"],
                "sweater_number": player["sweaterNumber"],
                "last_updated": datetime.now(),
            }
            try:
                new_player = db.insert_one(Player, data)
            except TransactionIntegrityError as e:
                new_player = db.update_one(Player, player["id"], data)

            try:
                season_data = {
                    "player": new_player,
                    "team": team,
                    "season": season,
                    "sweater_number": player["sweaterNumber"],
                }

                db_helper.insert_player_team_season(new_player.id, team.id, season_data)
            except TransactionIntegrityError as e:
                update_data = {
                    "sweater_number": player["sweaterNumber"],
                }
                db_helper.update_player_team_season(
                    new_player.id, team.id, season, update_data
                )

    return db_helper.get_team_roster(team_id, season)


def _should_update_roster(players: list) -> bool:
    """
    Checks to see if roster data needs to be updated (older than 2 hours).

    Parameters:
        players: List of player dictionaries with last_updated timestamps.

    Returns:
        True if any player data is stale, False otherwise.
    """
    if len(players) == 0:
        return True

    update_threshold = datetime.now() - timedelta(hours=2)
    return any(player["last_updated"] <= update_threshold for player in players)


@player_router.get("/players_by_team_id/")
async def get_players_by_team_id(id: int, season: str = current_season):
    """
    Gets basic player information about all players on a given teas for a given season.

    Parameters:
        id: The ID of the team to retrieve roster data for.
        season: The season string for the season to get roster data for.
            (default: the current season)

    Returns:
        A list of players on the given team and a dictionary of their basic information.
    """
    team = db.get_by_id(Team, id)
    if not team:
        return {"error": "Team not found."}

    players = db_helper.get_team_roster(id, season)

    if _should_update_roster(players):
        players = await _update_team_roster(id, team.abbr, season)

    players = jsonable_encoder(players)
    return {"roster": players, "count": len(players)}


@player_router.get("/players_by_team_name/")
async def get_players_by_team_name(name: str, season: str = current_season):
    """
    Gets a team's roster for a specific season by the team's name.

    Parameters:
        name: The name, common_name, or abbreviation of the team to collect roster data for.
        season: The season string.

    Returns:
        A list aff the team's roster for the given season with a dictionary of the players basic information.
    """
    team = db.search_by_any_field(
        Team, name, fields=["name", "common_name", "abbr"], case_sensitive=False
    )
    if not team:
        return {"error": "Team not found"}

    players = db_helper.get_team_roster(team.id, season)

    if _should_update_roster(players):
        ic("We need to update.")
        players = await _update_team_roster(team.id, team.abbr, season)

    players = jsonable_encoder(players)
    return {"roster": players, "count": len(players)}


@player_router.get("player_by_name/{name}")
async def get_player_by_name(name: str):
    """
    Gets a single players basic information by name.

    Parameters:
        name: The name of the player to search for.

    Return:
        A list of players found by the search term, or None if none are found.

    """
    pass


def broken_function(test=[]):
      print("too many indents")
      my_really_really_long_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100]


      print ( " different indent"   )
      return "Blumberg"