import math

from .spacetraders import *

def location_has_fuel(location):

    # Get information about location
    response = location_info(location)

    # Check if there is a marketplace
    has_marketplace = "MARKETPLACE" in [x["symbol"] for x in response["data"]["traits"]]

    # If not, no fuel
    if not has_marketplace:
        return False

    # Get what items are traded in marketplace
    response = market_info(location)

    has_fuel = "FUEL" in [x["symbol"] for x in response["data"]["exchange"]]

    return has_fuel


def get_mining_locations(system):

    response = waypoints_in_system(system)["data"]

    data = filter(
        lambda x: x["type"] == "ASTEROID" or x["type"] == "ASTEROID_FIELD",
        response
    )
    
    mining_place_locations = []

    # Now for each page
    for waypoint in data:

        mining_place_locations.append(
            (waypoint["symbol"], waypoint["type"], waypoint["x"], waypoint["y"])
        )

    return mining_place_locations 

def get_marketplace_locations(system):

    response = location_trait(system, "MARKETPLACE")

    market_place_locations = []

    # Now for each page

    for waypoint in response["data"]:
        market_place_locations.append(
            (waypoint["symbol"], waypoint["type"], waypoint["x"], waypoint["y"])
        )

    return market_place_locations

def market_list(system):

    response = location_trait(system, "MARKETPLACE")

    return [(item["symbol"], item["type"], item["x"], item["y"])
            for item in response["data"]]
