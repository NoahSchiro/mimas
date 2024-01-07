from mimas.ships import Ship, MiningShip
from mimas.spacetraders import *
from mimas.find_market import market_list
from mimas.save_load import save_json, load_json 

from itertools import product
import os
import threading
from time import sleep

lock = threading.Lock()

supply = {
    "SCARCE"   : 1,
    "LIMITED"  : 2,
    "MODERATE" : 3,
    "HIGH"     : 4,
    "ABUNDANT" : 5,
}

cached = {
    # marketWaypoint : {
    #     imports : {
    #         "good" : "supply level"
    #     }
    #     exports : {
    #         "good" : "supply level"
    #     }
    # }
}

system = "X1-RY62"
all_markets = [(m, x, y) for m, t, x, y in market_list(system)]

def get_import_exports(market):
    if market not in cached:
        response = market_info(market)
        imports = response["data"]["imports"]
        exports = response["data"]["exports"]
        cached[market] = {
            "imports" : {},
            "exports" : {}
        }

        for i in imports:
            cached[market]["imports"][i["symbol"]] = supply["SCARCE"]
        for e in exports:
            cached[market]["exports"][e["symbol"]] = supply["ABUNDANT"]

# Given the set of market waypoints, determine what good to deliver
def determine_path():

    # We will only move goods such that:
    # 1. Export supply is ABUNDANT, HIGH
    # 2. Import supply is SCARCE, LIMITED

    # [(market, good, supply)]
    potential_exports = []
    potential_imports = []

    for market in cached:
        for export in cached[market]["exports"]:
            if cached[market]["exports"][export] > 3:
                potential_exports.append((market, export, cached[market]["exports"][export]))

        for imp in cached[market]["imports"]:
            if cached[market]["imports"][imp] < 3:
                potential_imports.append((market, imp, cached[market]["imports"][imp]))

    # Get cartesian product of these lists
    combined = product(potential_exports, potential_imports)
    
    # Filter things that aren't an export / import combination
    combined = list(filter(lambda x: x[0][1] == x[1][1], combined))

    # Sort by the greatest differential in supply and demand
    sorted_list = list(sorted(combined, key=lambda x: -(x[0][2] - x[0][2])))

    if len(sorted_list) == 0:
        return None, None, None, None

    best_combination = sorted_list[0]
    
    final_good    = best_combination[0][1]
    good_supply   = best_combination[0][2]
    export_market = best_combination[0][0]
    import_market = best_combination[1][0]

    return final_good, good_supply, export_market, import_market

# Given a good, what market can we sell it at?
def determine_import_market(good):
    for market in cached:
        for imp in cached[market]["imports"]:
            if imp == good and cached[market]["imports"][imp] < 3:
                return market

# When we are at a waypoint we want to cache the data on the market
def cache_market_data(waypoint):

    # Get data on the market, specifically the data
    # on trade goods
    response = market_info(waypoint)["data"]["tradeGoods"]

    # For each good
    for item in response:

        # Get name, type (export/import), and supply level
        symbol = item["symbol"]
        market_type = item["type"]
        item_supply = item["supply"]

        # If it's an import, then mark in the approriate place
        if market_type == "IMPORT":
            cached[waypoint]["imports"][symbol] = supply[item_supply]
        elif market_type == "EXPORT":
            cached[waypoint]["exports"][symbol] = supply[item_supply]

    # Save the json out so that we have up to date market data
    save_json("./data/market_data.json", cached)

def hauling_directive(ship):

    # If the ship already has cargo, we need to sell it off
    if len(ship.cargo) != 0:

        # Need to save this is a seperate variable because
        # cargo changes as we sell goods
        remaining_cargo = ship.cargo.keys()

        for good in remaining_cargo:
            with lock:
                import_market = determine_import_market(good)

            print(f"\n[DIRECTIVE] [{ship.name}] moving {good} to {import_market}\n")

            # If we are not at this location then we need to move there
            if ship.location != import_market:
                ship.dock()
                ship.buy_fuel(True)
                ship.orbit()
                ship.fly(import_market)
                ship.dock()
                ship.buy_fuel(True)

            ship.dock()
            # Sell all of the good that we have
            ship.sell_cargo(good, ship.cargo[good]//2)
            ship.sell_cargo(good, ship.cargo[good])

    while True:

        # Determine what good to transport, where to buy it, where to take it
        with lock:
            good, good_supply, em, im = determine_path()

        print(f"\n[DIRECTIVE] [{ship.name}] moving {good} (supply level {good_supply}) from {em} to {im}\n")

        # If we are not already at the export market, we need to go there
        if ship.location != em:
            ship.dock()
            ship.buy_fuel(True)
            with lock:
                cache_market_data(ship.location)
            ship.orbit()
            ship.fly(em)

        # Now that we are there, let's buy the item
        ship.dock()
        ship.buy_fuel(True)
        with lock:
            cache_market_data(ship.location)
        ship.buy_cargo(good, ship.cargo_capacity//2)
        ship.buy_cargo(good, ship.cargo_capacity//2)
        ship.orbit()

        # Now let's fly to the import market
        ship.fly(im)
        ship.dock()

        #Sell goods
        ship.sell_cargo(good, ship.cargo_capacity//2)
        ship.sell_cargo(good, ship.cargo_capacity//2)
        with lock:
            cache_market_data(ship.location)

def build_jump_gate(ship):

    jump_gate = "X1-RY62-I58"

    # Find where I can buy advanced circuits
    # and fab mats

    circuit_market = None
    fab_market = None
    for market in cached:
        for good in cached[market]["exports"]:
            if cached[market]["exports"][good] >= 3:
                if good == "ADVANCED_CIRCUITRY":
                    circuit_market = market
                if good == "FAB_MATS":
                    fab_market = market

    while circuit_market != None and fab_market != None:

        # Get information about the construction site
        cdata = construction_info(jump_gate)["data"]

        # How much do I need of each?
        circuits_needed = 0
        fab_needed = 0

        for material in cdata["materials"]:
            if material["tradeSymbol"] == "ADVANCED_CIRCUITRY":
                circuits_needed = material["required"] - material["fulfilled"]
            if material["tradeSymbol"] == "FAB_MATS":
                fab_needed = material["required"] - material["fulfilled"]

        supply_item = "ADVANCED_CIRCUITY" if circuits_needed > fab_needed else "FAB_MATS"

        market = circuit_market if circuits_needed > fab_needed else fab_market

        print(f"\n[DIRECTIVE] [{ship.name}] supplying jump gate with {supply_item}\n")
        
        # Get ready to fly a while
        ship.dock()
        ship.buy_fuel(True)
        ship.orbit()

        # Buy supplies
        ship.fly(market)
        ship.dock()
        ship.buy_cargo(supply_item, 40)
        ship.buy_fuel(True)

        # Fly to the jump gate
        ship.orbit()
        ship.fly(jump_gate)
        ship.dock()

        # Give supplies to jump gate
        ship.supply_construction(supply_item, 40)

       
if __name__=="__main__":

    # TODO: Create a "Fleet" class which controls mining loops, import/export loops, etc.
    # as well as multi threading
    # Create a "System" class which will have a list of "Waypoints", which will have properties
    # such as market or jump gate or ship yard or whatever else is applicable 

    # X1-RY62-A2:
        # SHIP_PROBE
        # SHIP_LIGHT_SHUTTLE
        # SHIP_LIGHT_HAULER
    # X1-RY62-C45:
        # SHIP_PROBE
        # SHIP_SIPHON_DRONE
    # X1-RY62-H55:
        # SHIP_MINING_DRONE
        # SHIP_SURVEYOR

    contract_id = "clqsh3s6201r6s60cigkqsset"

    main_ship     = MiningShip("ZEPHOS-1")
    
    mining_drone1 = MiningShip("ZEPHOS-3")
    mining_drone2 = MiningShip("ZEPHOS-4")
    surveyor      = Ship("ZEPHOS-5")
    mining_drone3 = MiningShip("ZEPHOS-6")
    mining_drone4 = MiningShip("ZEPHOS-7")
    mining_drone5 = MiningShip("ZEPHOS-8")
    mining_drone6 = MiningShip("ZEPHOS-9")
    mining_drone7 = MiningShip("ZEPHOS-A")

    hauler1       = Ship("ZEPHOS-B")
    hauler2       = Ship("ZEPHOS-C")
    hauler3       = Ship("ZEPHOS-D")
    hauler4       = Ship("ZEPHOS-E")

    # Load / compute the import / export data
    if os.path.exists("./data/market_data.json"):
        print("Loaded market data...")
        cached = load_json("./data/market_data.json")
    else:
        print("Computing market data")
        for m, x, y in all_markets:
            get_import_exports(m)

    build_jump_gate(main_ship)

    t1 = threading.Thread(target=hauling_directive, args=(main_ship, ))
    t2 = threading.Thread(target=hauling_directive, args=(hauler1, ))
    t3 = threading.Thread(target=hauling_directive, args=(hauler2, ))
    t4 = threading.Thread(target=hauling_directive, args=(hauler3, ))
    t5 = threading.Thread(target=hauling_directive, args=(hauler4, ))

    t1.start()
    sleep(100)
    t2.start()
    sleep(100)
    t3.start()
    sleep(100)
    t4.start()
    sleep(100)
    t5.start()
    sleep(100)

    t1.join()
    t2.join()
    t3.join()
    t4.join()
    t5.join()
