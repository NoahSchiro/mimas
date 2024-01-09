from .spacetraders import *
from .pathfinding import dist, construct_graph, bfs_with_weight_limit
from .market_data import market_data, market_data_lock, supply_levels, market_list, location_has_fuel
from .save_load import save_json
import json
from datetime import datetime
from time import sleep

class Ship():
    def __init__(self, ship_name):

        info = ship_info(ship_name)["data"]

        nav_info = info["nav"]
        fuel_info = info["fuel"]
        cargo_info = info["cargo"]

        self.name     = ship_name
        self.status   = nav_info["status"]
        self.role     = info["registration"]["role"]
        self.location = nav_info["waypointSymbol"]
        self.x = nav_info["route"]["destination"]["x"]
        self.y = nav_info["route"]["destination"]["y"]
        self.flight_mode = nav_info["flightMode"]

        self.fuel_capacity = fuel_info["capacity"]
        self.current_fuel = fuel_info["current"]
        
        self.cargo_capacity = cargo_info["capacity"]
        self.cargo = {}
        for item in cargo_info["inventory"]:
            self.cargo[item["symbol"]] = item["units"]

    def cargo_full(self):
        return sum(self.cargo.values()) >= self.cargo_capacity

    def orbit(self):

        if self.status != "DOCKED":
            print(f"Trying to orbit {self.name} when status is {self.status}")

        # Send the command
        response = orbit_ship(self.name)

        location = response["data"]["nav"]["waypointSymbol"]

        if response["data"]["nav"]["status"] == "IN_ORBIT":
            print(f"[{self.name}] [{location}] [ORBIT]")
            self.status = "IN_ORBIT"
        else:
            print("Orbit not successful")

    def dock(self):

        # Send the command
        response = dock_ship(self.name)
        
        if "error" in response:
            print(json.dumps(response, indent=2))
            return

        location = response["data"]["nav"]["waypointSymbol"]

        if response["data"]["nav"]["status"] == "DOCKED":
            print(f"[{self.name}] [{location}] [DOCKED]")
            self.status = "DOCKED"
        else:
            print("Dock was not successful")

    def change_flight_mode(self, mode):
        change_flight_mode(self.name, mode)
        print(f"[{self.name}] [FLIGHT MODE={mode}]")
        self.flight_mode = mode

    def fly(self, location):

        if self.location == location:
            print(f"[{self.name}] already at {location}")
            return

        # Need to determine distance to end location
        endpoint_info = location_info(location)
        endpoint_x = endpoint_info["data"]["x"]
        endpoint_y = endpoint_info["data"]["y"]

        # Can't fly somewhere if we aren't in orbit
        if self.status != "IN_ORBIT":
            self.orbit()

        # If we can't fly there in one shot, then we need to do something
        # more complex
        if dist(self.x, self.y, endpoint_x, endpoint_y) > self.fuel_capacity and self.flight_mode != "DRIFT":
            self.route_planning(location)
        
        # If we are in the correct range then just fly there normally
        else:

            # Post request
            response = navigate_ship(self.name, location)

            route_data = response["data"]["nav"]["route"]

            format = "%Y-%m-%dT%H:%M:%S.%fZ"

            # Want to figure out how long it will take me to get there
            arrival_time = datetime.strptime(route_data["arrival"], format)
            departure_time = datetime.strptime(route_data["departureTime"], format)

            # Compute difference
            time_delta = arrival_time - departure_time

            # Report
            print(f"[{self.name}] flying to {location} ({time_delta.total_seconds()} seconds remaining)")

            # Change status
            self.status = "IN_TRANSIT"
            self.current_fuel = response["data"]["fuel"]["current"]

            print(f"[{self.name}] [FUEL={self.current_fuel}/{self.fuel_capacity}]")

            # Wait till we arrive
            sleep(time_delta.total_seconds())
            
            # Reset variables
            self.location = location
            self.x = route_data["destination"]["x"]
            self.y = route_data["destination"]["y"]
            self.status = "IN_ORBIT"

    # When we have a really long path, this will let us plan each step
    def route_planning(self, location):

        system = "-".join(location.split("-")[:2])

        # For now, we only want to stop at places
        # with fuel so we don't get stuck
        all_markets = market_list(system)
        markets = [(name, x, y) for name, _, x, y in all_markets]
        graph = construct_graph(markets)

        # Now that we have the system plotted as a graph,
        # we want to find a path to the location from our current location
        path = bfs_with_weight_limit(
            graph,              # Graph object
            self.location,      # Our location
            location,           # Where we want to go
            self.fuel_capacity  # How far we are allowed to go in one jump
        )

        if path is None:
            print(f"[{self.name}] no path exists")
            return

        # For each spot in the path, fly to it
        for idx, (_, end) in enumerate(path):
            print(f"[{self.name}] routing to [{location}]. Flying to stop {idx+1}/{len(path)}")
            self.fly(end)
            self.dock()
            self.buy_fuel(True)
            self.orbit()

    def buy_fuel(self, override=False):

        # How much could we buy?
        diff = self.fuel_capacity - self.current_fuel

        # Check to make sure that the location we are at has fuel
        if not location_has_fuel(self.location):
            return

        amount_to_buy = (diff // 100) * 100

        amount_to_buy = "max" if override else amount_to_buy

        response = buy_fuel(self.name, amount_to_buy)

        self.current_fuel = response["data"]["fuel"]["current"]
        unit_price = response["data"]["transaction"]["pricePerUnit"]
        total_price = response["data"]["transaction"]["totalPrice"]

        print(f"[{self.name}] [BUY] [{amount_to_buy} FUEL] (total: {total_price}) (unit price: {unit_price})")


    # When we are at a waypoint we want to cache the data on the market
    def cache_market_data(self):

        # Get data on the market, specifically the data
        # on trade goods
        response = market_info(self.location)["data"]["tradeGoods"]

        market_data_lock.acquire()

        # For each good
        for item in response:

            # Get name, type (export/import), and supply level
            symbol = item["symbol"]
            market_type = item["type"]
            item_supply = item["supply"]

            # If it's an import, then mark in the approriate place
            if market_type == "IMPORT":
                market_data[self.location]["imports"][symbol] = supply_levels[item_supply]
            elif market_type == "EXPORT":
                market_data[self.location]["exports"][symbol] = supply_levels[item_supply]

        # Save the json out so that we have up to date market data
        save_json("./data/market_data.json", market_data)

        market_data_lock.release()

    def buy_cargo(self, resource, quantity):
        response = buy_cargo(self.name, resource, quantity)
        
        total_price = response["data"]["transaction"]["totalPrice"]
        unit_price = response["data"]["transaction"]["pricePerUnit"]

        print(f"[{self.name}] [BUY] [{quantity} {resource}] (total: {total_price}) (unit price: {unit_price})")
        if resource in self.cargo:
            self.cargo[resource] += quantity
        else:
            self.cargo[resource] = quantity

        print(f"[{self.name}] [CARGO={sum(self.cargo.values())}/{self.cargo_capacity}]")

        # Update how the market data has changed
        self.cache_market_data()

        return total_price

    def sell_cargo(self, resource, quantity):
        response = sell_cargo(self.name, resource, quantity)

        data = response["data"]["transaction"]
        resource = data["tradeSymbol"]
        quantity = data["units"]
        unit_price = data["pricePerUnit"]
        total_price = data["totalPrice"]

        print(f"[{self.name}] [SELL] [{quantity} {resource}] (total: {total_price}) (unit price: {unit_price})")

        # Remove that cargo from our inventory
        if resource in self.cargo:
            self.cargo[resource] -= quantity

            # Delete the cargo if it reaches 0
            if self.cargo[resource] == 0:
                del self.cargo[resource]

        # Update how the market data has changed
        self.cache_market_data()

        return total_price

    #ship.supply_construction(jump_gate, supply_item, 40)
    def supply_construction(self, good, quantity):
        _ = supply_construction(self.location, self.name, good, quantity)

        # Remove that cargo from our inventory
        if good in self.cargo:
            self.cargo[good] -= quantity

            # Delete the cargo if it reaches 0
            if self.cargo[good] == 0:
                del self.cargo[good]

        print(f"[{self.name}] [JUMP GATE CONSTRUCT] [{quantity} {good}]")


class MiningShip(Ship):
    def __init__(self, ship_name):
        Ship.__init__(self, ship_name)

    def jettison(self, resource, quantity):
        response = jettison_cargo(self.name, resource, quantity)

        print(f"[{self.name}] [JETTISON] [{quantity} {resource}]")
        return response

    def mine(self):

        response = mine(self.name)

        cooldown = response["data"]["cooldown"]["totalSeconds"]
        resource = response["data"]["extraction"]["yield"]["symbol"]
        quantity = response["data"]["extraction"]["yield"]["units"]

        print(f"[{self.name}] [MINE] [{quantity} {resource}]")

        if resource in self.cargo:
            self.cargo[resource] += quantity
        else:
            self.cargo[resource] = quantity

        sleep(cooldown)

# Ship starts at a market
def mining_loop(ship):
    
    # Locations we care about for now
    market = "X1-HD34-B7"
    mining = "X1-HD34-B11"
 
    while ship.cargo["IRON_ORE"] < 31:

        # Fly to the mining location
        ship.orbit()
        ship.fly(mining)

        while not ship.cargo_full():
            ship.mine()
        print("Cargo full")

        # Go back to the market and sell goods
        ship.fly(market)
        ship.dock()
        ship.sell_cargo()

        # If we need fuel, buy some
        if ship.fuel_capacity - ship.current_fuel >= 100:
            ship.buy_fuel()

