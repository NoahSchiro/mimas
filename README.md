# mimas
---

[Mimas](https://en.wikipedia.org/wiki/Mimas) is a fleet commander for the game [SpaceTraders](https://spacetraders.io/). SpaceTraders is played by interacting with an https API and therefore can be automated with code.

If you are interested in playing the game, then this repository is, for all intents and purposes, "spoilers" for the game. Part of the fun and interest for the game is working out your own solutions to the problems you face through coding!

## File structure / current purposes

```
.
├── data
│   └── market_data.json
├── leaderboard.py
├── LICENSE
├── main.py
├── map.py
├── mimas
│   ├── find_market.py
│   ├── __init__.py
│   ├── pathfinding.py
│   ├── save_load.py
│   ├── ships.py
│   └── spacetraders.py
└── README.md
```
### Directory top level

```leaderboard.py``` is a small script to detail our current standing amongst all players in SpaceTraders. Specifically it will tell us our ranking in terms of credits and ship count.

```main.py``` runs the main script that controls the ships and tells them what to do. Currently we are just interested in import/export trade routes as well as building our local jump gate

```map.py``` displays a very simple map of the current system

### Directory "data"

This is where we will generally store any cached data. Currently we only have one file which stores a bit of data about each market that we have visted. This is useful for deciding which import / export routes are going to generate us the most money.

### Directory "mimas"

This directory contains general tools that are useful for interacting with the SpaceTraders API.

```spacetraders.py``` is a thin wrapper around HTTP requests. This just prevents us from having to deal with creating requests all over the place and it also handles potential errors if we don't have an internet connection or something is not working correctly. This bit of code will handle all of this for us and return the formatted JSON of the response of the request

```ships.py``` contains a class called "Ship". This is just our code representation of an individual ship within the game. We can use methods on this class to do basic things with the ship. Fly to a certain location, jettison cargo, buy and sell goods, etc. The ship is not responsible for doing anything "smart" like figure out what goods to move where. However, if we try to fly somewhere that is not possible to fly to directly, then we will utilize more complex route planning.

```pathfinding.py``` contains code that performs route planning by first turning the system we are in to a weighted graph, and then computing BFS on that graph.

```save_load.py``` is a thin wrapper for saving and loading JSON data to disk.

```find_market.py``` contains some code for identifying markets / locations with fuel but this needs to be retooled eventually into something more broad.
