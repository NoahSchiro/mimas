import requests as rq
import json

from time import sleep

BASE_URL = "https://api.spacetraders.io/v2/"
TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZGVudGlmaWVyIjoiWkVQSE9TIiwidmVyc2lvbiI6InYyLjEuNCIsInJlc2V0X2RhdGUiOiIyMDIzLTEyLTMwIiwiaWF0IjoxNzAzOTY1NTY5LCJzdWIiOiJhZ2VudC10b2tlbiJ9.QPjW7TFCKLcPai_mC5ic1fDpKrLGeiUqkfkQlonEFyXbxvWpHZcOgnn0fIWNczSYxL0eFxy_zz8l0Ndyh7l-1_YVOmaTfQ0hcZgiW4wck96OsSrtFf0jj7iFL9HCyUbqeQNRYH_ghvEu37aG4M6k5tNkccAFS6HrXphVJs1BKPwj1_YWieyG0kgqceafCWOgpViBI7JFEww7hjRN0zNYZBIn8W124YqZWjhcRvwEgFpYBszflCkBaheUdu8Zpp63Ghw-adNWOZ2BRGigJJe1r1EoRoSduJtq5t3wjRkSO17UNS6QeVvD2zbr8NHUUbqNjHm_NctYmO9BVKnA-cXSJA"

AUTH_HEAD = {
    "Authorization": f"Bearer {TOKEN}"
}

POST_HEAD = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

JET_HEAD = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

SHIPS_HEAD = {
    "Accept" : "application/json",
    "Authorization" : f"Bearer {TOKEN}"
}

TRAIT_HEAD = {
    "Accept": "application/json"
}

# If a response has an error, handle it
def handle_error(data):
    if "error" in data:
        print(json.dumps(data, indent=2))
        raise Exception("Error in spacetraders response")

def handle_pages(original_url, response, head=AUTH_HEAD):
    
    # Else, there is multiple pages and we want to tack onto the original data
    data = response["data"]

    if "meta" not in response:
        return response

    num_pages = 1

    # If multiple pages
    if response["meta"]["total"] > response["meta"]["limit"]:
        num_pages += (response["meta"]["total"] // response["meta"]["limit"])

        # Get all the data
        for page in range(2, num_pages+1):

            sleep(0.5)

            # Get JUST the data from the next page
            response_data = rq.get(original_url, headers=head ,params={"page": page}).json()
            handle_error(response_data)
            response_data = response_data["data"]

            for item in response_data:
                # Add it to our data
                response["data"].append(item)

    # Reassign the data field and return
    return response

# Create a new agent
def register_new_agent():

    register_url = f"{BASE_URL}register"

    data = json.dumps({
        "symbol" : "ZEPHOS",
        "faction" : "COSMIC"
    })

    response = rq.post(register_url, headers=POST_HEAD, data=data).json()

    handle_error(response)
    response = handle_pages(register_url, response)

    return response

def list_all_agents():

    all_agents_url = f"{BASE_URL}agents"

    response = rq.get(all_agents_url, headers=TRAIT_HEAD).json()

    handle_error(response)
    response = handle_pages(all_agents_url, response)

    return response

# Display information about my account
def agent_info():

    agent_url = f"{BASE_URL}my/agent"
    response = rq.get(agent_url, headers=AUTH_HEAD).json()
    
    handle_error(response)
    response = handle_pages(agent_url, response)

    return response

# Display information about the current contract
def contract_info():
    
    contract_url = f"{BASE_URL}my/contracts"
    response = rq.get(contract_url, headers=AUTH_HEAD).json()
    
    handle_error(response)
    response = handle_pages(contract_url, response)

    return response

# Display information about all ships
def ships_info():

    ship_url = f"{BASE_URL}my/ships"

    response = rq.get(ship_url, headers=SHIPS_HEAD).json()
    
    handle_error(response)
    response = handle_pages(ship_url, response)

    return response

# Display information about a given ship
def ship_info(ship_name):

    ship_url = f"{BASE_URL}my/ships/{ship_name}"
    response = rq.get(ship_url, headers=AUTH_HEAD).json()
    
    handle_error(response)
    response = handle_pages(ship_url, response)

    return response

# Display what is in the ship cargo hold
def ship_cargo_info(ship_name):

    cargo_url = f"{BASE_URL}my/ships/{ship_name}/cargo"
    response = rq.get(cargo_url, headers=AUTH_HEAD).json()
    
    handle_error(response)
    response = handle_pages(cargo_url, response)

    return response

def waypoints_in_system(system):

    waypoints_url = f"{BASE_URL}systems/{system}/waypoints"

    response = rq.get(waypoints_url, headers=TRAIT_HEAD).json()

    handle_error(response)
    response = handle_pages(waypoints_url, response)

    return response

# Display more information about given location
def location_info(location):

    system = "-".join(location.split("-")[:2])
    
    location_url = f"{BASE_URL}systems/{system}/waypoints/{location}"
    response = rq.get(location_url, headers=AUTH_HEAD).json()
    
    handle_error(response)
    response = handle_pages(location_url, response)

    return response

# Find a location with a given trait
def location_trait(system, trait):
    
    trait_url = f"{BASE_URL}systems/{system}/waypoints?traits={trait}"
    response = rq.get(trait_url, headers=TRAIT_HEAD).json()

    handle_error(response)
    response = handle_pages(trait_url, response)

    return response

# Display what ships are available at shipyard
def shipyard_info(location):
    
    system = "-".join(location.split("-")[:2])

    shipyard_url = f"{BASE_URL}systems/{system}/waypoints/{location}/shipyard"
    response = rq.get(shipyard_url, headers=AUTH_HEAD).json()
    
    handle_error(response)
    response = handle_pages(shipyard_url, response)

    return response

# Buy a ship
def buy_ship(location, ship_type):

    buy_url = f"{BASE_URL}my/ships"
    data = json.dumps({
        "shipType" : ship_type,
        "waypointSymbol" : location
    })

    response = rq.post(buy_url, headers=POST_HEAD, data=data).json()
    
    handle_error(response)
    response = handle_pages(buy_url, response)

    return response

# Get a new contract
def negotiate_contract(ship):

    negotiate_url = f"{BASE_URL}my/ships/{ship}/negotiate/contract"
    response = rq.post(negotiate_url, headers=JET_HEAD).json()
    
    handle_error(response)
    response = handle_pages(negotiate_url, response)

    return response

# Accept a contract
def accept_contract(contract_id):

    accept_url = f"{BASE_URL}my/contracts/{contract_id}/accept"
    response = rq.post(accept_url, headers=AUTH_HEAD).json()
    
    handle_error(response)
    response = handle_pages(accept_url, response)

    return response

# Deliver cargo to contract point
def deliver_contract(contract_id, ship_name, resource, quantity):

    deliver_url = f"{BASE_URL}my/contracts/{contract_id}/deliver"
    
    data = json.dumps({
        "shipSymbol": ship_name,
        "tradeSymbol": resource,
        "units": quantity
    })

    response = rq.post(deliver_url, headers=JET_HEAD, data=data).json()
    
    handle_error(response)
    response = handle_pages(deliver_url, response)

    return response

# Once a contract has been completed, send a signal that it is done
def complete_contract(contract_id):

    complete_url = f"{BASE_URL}my/contracts/{contract_id}/fulfull"

    response = rq.get(complete_url, headers=AUTH_HEAD).json()
    
    handle_error(response)
    response = handle_pages(complete_url, response)

    return response

# Display information about a market at a given location
def market_info(location):
    
    system = "-".join(location.split("-")[:2])

    marketplace_url = f"{BASE_URL}systems/{system}/waypoints/{location}/market"
    response = rq.get(marketplace_url, headers=AUTH_HEAD).json()
    
    handle_error(response)
    response = handle_pages(marketplace_url, response)

    return response

# Orbit a ship
def orbit_ship(ship_name):

    orbit_url = f"{BASE_URL}my/ships/{ship_name}/orbit"
    response = rq.post(orbit_url, headers=AUTH_HEAD).json()
    
    handle_error(response)
    response = handle_pages(orbit_url, response)

    return response

# Dock a ship
def dock_ship(ship_name):
    dock_url = f"{BASE_URL}my/ships/{ship_name}/dock"
    response = rq.post(dock_url, headers=AUTH_HEAD).json()
    
    handle_error(response)
    response = handle_pages(dock_url, response)

    return response

# Fly the ship to a specified location
def navigate_ship(ship_name, location):

    # Data for post request
    flying_url = f"{BASE_URL}my/ships/{ship_name}/navigate"
    data = json.dumps({
        "waypointSymbol": location,
    })

    response = rq.post(flying_url, headers=POST_HEAD, data=data).json()
    
    handle_error(response)
    response = handle_pages(flying_url, response)

    return response

# Change the flight mode
def change_flight_mode(ship_name, flight_mode):

    flight_url = f"{BASE_URL}my/ships/{ship_name}/nav"
    data = json.dumps({
        "flightMode" : flight_mode
    })

    response = rq.patch(flight_url, headers=JET_HEAD, data=data).json()

    return response


# Buy fuel. Note that amount can be units of 100 or "max" where "max"
# will top up the tank
def buy_fuel(ship_name, amount):

    refuel_url = f"{BASE_URL}my/ships/{ship_name}/refuel"

    if amount != "max":
        data = json.dumps({
            "units" : amount
        })

        response = rq.post(refuel_url, headers=POST_HEAD, data=data).json()
    else:
        response = rq.post(refuel_url, headers=POST_HEAD).json()
    
    handle_error(response)
    response = handle_pages(refuel_url, response)

    return response

# Mine (if a ship is at a location where it is able to mine)
def mine(ship_name):

    mine_url = f"{BASE_URL}my/ships/{ship_name}/extract"

    response = rq.post(mine_url, headers=AUTH_HEAD).json()
    
    handle_error(response)
    response = handle_pages(mine_url, response)

    return response

def siphon(ship_name):

    siphon_url = f"{BASE_URL}my/ships/{ship_name}/siphon"

    response = rq.post(siphon_url, headers=AUTH_HEAD).json()

    handle_error(response)
    response = handle_pages(siphon_url, response)

    return response

def create_survey(ship_name):
    
    survey_url = f"{BASE_URL}my/ships/{ship_name}/survey"

    response = rq.post(survey_url, headers=JET_HEAD).json()

    return response

def refine_materials():
    pass

# Throw out junk
def jettison_cargo(ship_name, resource, quantity):

    jet_url = f"{BASE_URL}my/ships/{ship_name}/jettison"

    data = json.dumps({
        "symbol" : resource,
        "units" : quantity
    })

    response = rq.post(jet_url, headers=JET_HEAD, data=data).json()
    
    handle_error(response)
    response = handle_pages(jet_url, response)

    return response

# Sell cargo if at a market
def sell_cargo(ship_name, resource, quantity):
    
    sell_url = f"{BASE_URL}my/ships/{ship_name}/sell"

    data = json.dumps({
        "symbol" : resource,
        "units" : quantity
    })

    response = rq.post(sell_url, headers=POST_HEAD, data=data).json()
    
    handle_error(response)
    response = handle_pages(sell_url, response)

    return response

# Buy cargo if at a market
def buy_cargo(ship_name, resource, quantity):

    buy_url = f"{BASE_URL}my/ships/{ship_name}/purchase"
    data = json.dumps({
        "symbol" : resource,
        "units" : quantity
    })

    response = rq.post(buy_url, headers=JET_HEAD, data=data).json()
    
    handle_error(response)
    response = handle_pages(buy_url, response)

    return response

# Get information about a jump jump_gate
def jumpgate_info(location):

    system = "-".join(location.split("-")[:2])

    jumpgate_url = f"{BASE_URL}/systems/{system}/waypoints/{location}/jump-gate"

    response = rq.get(jumpgate_url, headers=TRAIT_HEAD).json()

    handle_error(response)
    response = handle_pages(jumpgate_url, response)

    return response

def construction_info(location):

    system = "-".join(location.split("-")[:2])

    construction_url = f"{BASE_URL}/systems/{system}/waypoints/{location}/construction"

    response = rq.get(construction_url, headers=TRAIT_HEAD).json()

    handle_error(response)
    response = handle_pages(construction_url, response)

    return response

# curl --request POST \
#   --url https://api.spacetraders.io/v2/systems/systemSymbol/waypoints/waypointSymbol/construction/supply \
#   --header 'Accept: application/json' \
#   --header 'Authorization: Bearer {TOKEN}' \
#   --header 'Content-Type: application/json' \
#   --data '{
#   "shipSymbol": "string",
#   "tradeSymbol": "string",
#   "units": 0
# }'
def supply_construction(location, ship_name, good, quantity):

    system = "-".join(location.split("-")[:2])

    supply_url = f"{BASE_URL}systems/{system}/waypoints/{location}/construction/supply"
    data = json.dumps({
        "shipSymbol" : ship_name,
        "tradeSymbol" : good,
        "units" : quantity
    })

    response = rq.post(supply_url, headers=JET_HEAD, data=data).json()

    handle_error(response)
    response = handle_pages(supply_url, response)

    return response

if __name__=="__main__":
    
    jump_gate = "X1-RY62-I58"
    system = "X1-RY62"

    r = construction_info(jump_gate)

    print(json.dumps(r, indent=2))

    r = agent_info()

    print(json.dumps(r, indent=2))
