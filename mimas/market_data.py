from threading import Lock, Thread 
import os

from .spacetraders import *
from .save_load import *

system = "X1-RY62"

supply_levels = {
    "SCARCE"   : 1,
    "LIMITED"  : 2,
    "MODERATE" : 3,
    "HIGH"     : 4,
    "ABUNDANT" : 5,
}


market_data_lock = Lock()

market_data = {
    # marketWaypoint : {
    #     imports : {
    #         "good" : "supply level"
    #     }
    #     exports : {
    #         "good" : "supply level"
    #     }
    # }
}

market_data_lock.acquire()

if os.path.exists("./data/market_data.json"):
    print("Loaded market data...")
    market_data = load_json("./data/market_data.json")
else:
    print("Computing market data")

    markets = location_trait(system, "MARKETPLACE")["data"]

    for m in markets:
        market = m["symbol"]
        if market not in market_data:
            response = market_info(market)
            imports = response["data"]["imports"]
            exports = response["data"]["exports"]
            market_data[market] = {
                "imports" : {},
                "exports" : {}
            }

            for i in imports:
                market_data[market]["imports"][i["symbol"]] = supply_levels["SCARCE"]
            for e in exports:
                market_data[market]["exports"][e["symbol"]] = supply_levels["ABUNDANT"]

market_data_lock.release()

# TODO: make this function match the buy function

# Given a good, what market can we sell it at?
def determine_sell_market(good):

    market_data_lock.acquire()

    sell_market = None

    for market in market_data:
        for imp in market_data[market]["imports"]:
            if imp == good and market_data[market]["imports"][imp] < 3:
                sell_market = market
                break

    market_data_lock.release()

    return sell_market

def determine_buy_market(good):
    max_buy_market = None
    max_buy_supply = 0

    market_data_lock.acquire()

    for market in market_data:
        for exp in market_data[market]["exports"]:
            if exp == good and market_data[market]["exports"][exp] > max_buy_supply:
                max_buy_market = market
                max_buy_supply = market_data[market]["exports"][exp]

    market_data_lock.release()

    return max_buy_market, max_buy_supply





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
