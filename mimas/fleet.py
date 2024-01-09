from .spacetraders import *
from .ships import Ship, MiningShip
from .market_data import market_data, market_data_lock, determine_sell_market, determine_buy_market

from time import sleep
from random import randint
from threading import Thread
from itertools import product

class Fleet():

    # Get all information for all my ships and store it into an array
    def __init__(self):

        # Get a list of ships (as the class) as well as a
        # dictionary that says what role each one has (and their current activity) 
        self.ships = []
        self.ships_meta = {}
        self.register_ships()

        self.threads = []

    def register_ships(self):

        print("Registering ships...")

        # Find out how many ships I have
        ships = ships_info()["data"]

        # Iterate through those ships
        for idx, ship in enumerate(ships):
            
            # We have an API request limit so let's
            # make sure we don't spam them...
            sleep(0.5)
            print(f"Registered ship {idx+1}/{len(ships)}", end='\r')

            ship_name = ship["symbol"]
            
            # If it's a mining / siphon ship then register it as such
            if ship["registration"]["role"] == "HARVESTER":
                self.ships.append(MiningShip(ship_name))
            else:
                self.ships.append(Ship(ship_name))

            self.ships_meta[ship_name] = {"activity": "INACTIVE"}

        print("\nDone registering ships...")

    # This shows us information about our fleet
    def show_ships(self):

        for ship in self.ships:
            ship_activity = self.ships_meta[ship.name]["activity"]
            print(f"{ship.name} ({ship.status}); {ship.location}")
            print(f"DIRECTIVE: {ship_activity}")
            print(f"FUEL: {ship.current_fuel}/{ship.fuel_capacity}")

            for c in ship.cargo.keys():
                print(f"\t{c}: {ship.cargo[c]}")

            print("")

    # This will check for inactive ships and reassign
    # them to a new task depending on current conditions
    def reassign_inactive_ships(self):

        print("[FLEET META] checking for inactive ships")

        jump_gate = "X1-RY62-I58"

        for ship in self.ships:

            ship_act = self.ships_meta[ship.name]["activity"]

            if ship.role == "HAULER" or ship.role == "COMMAND" and ship_act == "INACTIVE":

                # Reassign it a new role randomly
                # 1/3rd chance of building the jump gate
                # 2/3rds chance of hauling
                if randint(1,3) == 1:
                    temp = Thread(target=self.build_jump_gate, args=(ship, jump_gate))
                    temp.start()
                    #self.threads.append(temp)
                    self.ships_meta[ship.name]["activity"] = "BUILDING"
                    sleep(10)
                else:
                    temp = Thread(target=self.hauling_directive, args=(ship,))
                    temp.start()
                    #self.threads.append(temp)
                    self.ships_meta[ship.name]["activity"] = "HAULING"
                    sleep(10)

        # Every 20 minutes check for inactive ships
        sleep(60 * 20)

    # Main entry point to get our ships going
    def run(self):

        jump_gate = "X1-RY62-I58"

        # For each ship
        for ship in self.ships:

            # If it is a hauler type
            if ship.role == "HAULER":
                
                temp = Thread(target=self.hauling_directive, args=(ship,))
                temp.start()
                #self.threads.append(temp)
                self.ships_meta[ship.name]["activity"] = "HAULING"
                
                # Wait for a bit before we spin up the next thread
                sleep(90)

            # Start the command ship off by moving goods to the jump gate
            elif ship.role == "COMMAND":

                temp = Thread(target=self.build_jump_gate, args=(ship, jump_gate))
                temp.start()
                #self.threads.append(temp)
                self.ships_meta[ship.name]["activity"] = "BUILDING"

                # Wait for a bit before we spin up the next thread
                sleep(90)

        # Once we have gone through all the ships, we will spin up a thread
        # that is responsible for reassigning inactive ships
        # This feature is on temporary hold as it might be locking up my other threads somehow
        #temp = Thread(target=self.reassign_inactive_ships(), args=())
        #temp.start()


    ########### DIRECTIVES ###############
    
    # Given the set of market waypoints, determine what good to deliver
    def _determine_import_export_path(self):

        # We will only move goods such that:
        # 1. Export supply is ABUNDANT, HIGH
        # 2. Import supply is SCARCE, LIMITED

        # [(market, good, supply)]
        potential_exports = []
        potential_imports = []

        market_data_lock.acquire()

        for market in market_data:
            for export in market_data[market]["exports"]:
                if market_data[market]["exports"][export] > 3:
                    potential_exports.append((market, export, market_data[market]["exports"][export]))

            for imp in market_data[market]["imports"]:
                if market_data[market]["imports"][imp] < 3:
                    potential_imports.append((market, imp, market_data[market]["imports"][imp]))

        market_data_lock.release()

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
    
    # If the ship already has cargo, we need to sell it off
    def sell_extra_cargo(self, ship):
        
        if len(ship.cargo) != 0:

            # Need to save this is a seperate variable because
            # cargo changes as we sell goods
            remaining_cargo = list(ship.cargo.keys())

            for good in remaining_cargo:
                import_market = determine_sell_market(good)

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

                # Sometimes there is a cap on how much goods you
                # can buy or sell at a time so this will break it up a bit
                while ship.cargo[good] > 40:
                    ship.sell_cargo(good, 40)

                # Sell off whatever remains
                ship.sell_cargo(good, ship.cargo[good])

            print(f"\n[DIRECTIVE] [{ship.name}] has no more targets for selling task\n")

    def hauling_directive(self, ship):

        self.sell_extra_cargo(ship)

        # Determine what good to transport, where to buy it, where to take it
        good, good_supply, em, im = self._determine_import_export_path()

        while good != None:

            print(f"\n[DIRECTIVE] [{ship.name}] moving {good} (supply level {good_supply}) from {em} to {im}\n")

            # If we are not already at the export market, we need to go there
            if ship.location != em:
                ship.dock()
                ship.buy_fuel(True)
                ship.orbit()
                ship.fly(em)

            # Now that we are there, let's buy the item
            ship.dock()
            ship.buy_fuel(True)
            ship.buy_cargo(good, ship.cargo_capacity//2)
            ship.buy_cargo(good, ship.cargo_capacity//2)
            ship.orbit()

            # Now let's fly to the import market
            ship.fly(im)
            ship.dock()

            #Sell goods
            ship.sell_cargo(good, ship.cargo_capacity//2)
            ship.sell_cargo(good, ship.cargo_capacity//2)


        print(f"\n[DIRECTIVE] [{ship.name}] has no more targest for hauling task\n")

        # Once this while loop ends, reset activity to INACTIVE
        self.ships_meta[ship.name]["activity"] = "INACTIVE"

    # Command a hauler to move items to the jump gate and construct it
    def build_jump_gate(self, ship, jump_gate):

        circ_market, circ_supply = determine_buy_market("ADVANCED_CIRCUITRY")
        fab_market, fab_supply = determine_buy_market("FAB_MATS")

        # While there exists a market where we can get a decent price for building goods
        while circ_market != None and fab_market != None and (circ_supply >= 3 or fab_supply >= 3):

            # Get information about the construction site
            cdata = construction_info(jump_gate)["data"]

            circuits_needed = 1000
            fab_needed = 1000

            for material in cdata["materials"]:
                if material["tradeSymbol"] == "ADVANCED_CIRCUITRY":
                    circuits_needed = material["required"] - material["fulfilled"]
                if material["tradeSymbol"] == "FAB_MATS":
                    fab_needed = material["required"] - material["fulfilled"]

            supply_item = "ADVANCED_CIRCUITRY" if circ_supply > fab_supply else "FAB_MATS"
            market = circ_market if circ_supply > fab_supply else fab_market
            amount_to_buy = min(40, circuits_needed) if circ_supply > fab_supply else min(40, fab_needed)

            print(f"\n[DIRECTIVE] [{ship.name}] supplying jump gate with {supply_item} (supply level: {max(circ_supply, fab_supply)})\n")
            
            # Get ready to fly a while
            ship.dock()
            ship.buy_fuel(True)
            ship.orbit()

            # Buy supplies
            ship.fly(market)
            ship.dock()
            ship.buy_cargo(supply_item, amount_to_buy)
            ship.buy_fuel(True)

            # Fly to the jump gate
            ship.orbit()
            ship.fly(jump_gate)
            ship.dock()

            # Give supplies to jump gate
            ship.supply_construction(supply_item, amount_to_buy)

            # Update information about the market once we have done the trade
            circ_market, circ_supply = determine_buy_market("ADVANCED_CIRCUITRY")
            fab_market, fab_supply = determine_buy_market("FAB_MATS")


        print(f"\n[DIRECTIVE] [{ship.name}] no more viable markets for building jump gate\n")

        # Once this while loop ends, reset activity to INACTIVE
        self.ships_meta[ship.name]["activity"] = "INACTIVE"
