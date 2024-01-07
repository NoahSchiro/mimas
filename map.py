import requests as rq
import matplotlib.pyplot as plt

from mimas.spacetraders import *
from mimas.find_market import get_marketplace_locations

url = "https://api.spacetraders.io/v2/"

system = "X1-RY62"

if __name__=="__main__":

    locs = get_marketplace_locations(system)
    xs = [l[2] for l in locs]
    ys = [l[3] for l in locs]
    ls = [l[0] for l in locs]

    # Create scatter plot
    fig, ax = plt.subplots()
    fig = plt.scatter(xs, ys)

    # Add labels to each point
    for i, label in enumerate(ls):
        text = plt.text(xs[i], ys[i], label)

    plt.show()
