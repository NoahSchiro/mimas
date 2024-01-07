from mimas.spacetraders import list_all_agents


all_agents = list_all_agents()["data"]
num_agents = len(all_agents)

print(f"Number of agents: {num_agents}")

credit_rank = list(sorted(all_agents, key=lambda x: -x["credits"]))
for idx, x in enumerate(credit_rank):
    if x["symbol"] == "ZEPHOS":
        count = x["credits"] 
        top_percent = (idx+1)/num_agents * 100
        print(f"Credit ranking: {idx+1}/{num_agents} ({count} credits) (top {top_percent:.2f}%)")

ship_rank = list(sorted(all_agents, key=lambda x: -x["shipCount"]))
for idx, x in enumerate(ship_rank):
    if x["symbol"] == "ZEPHOS":
        count = x["shipCount"]
        top_percent = (idx+1)/num_agents * 100
        print(f"Ship ranking: {idx+1}/{num_agents} ({count} ships) (top {top_percent:.2f}%)")
