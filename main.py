from mimas.ships import Ship, MiningShip
from mimas.fleet import Fleet
from mimas.spacetraders import *

system = "X1-RY62"
jump_gate = "X1-RY62-I58"
contract_id = "clqsh3s6201r6s60cigkqsset"

if __name__=="__main__":

    # TODO: 
    # Create a "System" class which will have a list of "Waypoints", which will have properties
    # such as market or jump gate or ship yard or whatever else is applicable 

    fleet = Fleet()
    fleet.run()
