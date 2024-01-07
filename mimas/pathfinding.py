import math
from collections import deque

def dist(x1, y1, x2, y2):
    return math.sqrt((x2-x1)**2 + (y2-y1)**2)

# For this, we need to pass in a list of [waypoint, x, y]
def construct_graph(waypoints):

    graph = {}

    for name1, x1, y1 in waypoints:
        graph[name1] = []
        for name2, x2, y2 in waypoints:

            # Distance between these two points
            distance = dist(x1, y1, x2, y2)

            # Don't add connections to myself
            if name1 != name2:
                graph[name1].append((name2, distance))

    return graph

def bfs_with_weight_limit(graph, start, end, weight_limit):
    visited = set()
    queue = deque([(start, [])])

    while queue:
        current, path = queue.popleft()

        if current == end:
            return path

        if current not in visited:
            visited.add(current)
            
            neighbors = [
                (neighbor, weight)
                for neighbor, weight in graph[current]
                if weight <= weight_limit
            ]

            for neighbor, _ in neighbors:
                if neighbor not in visited:
                    queue.append((neighbor, path + [(current, neighbor)]))

    return None
