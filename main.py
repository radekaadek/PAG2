import osmnx as ox
import networkx as nx
import os
import time
import geopandas as gpd
import matplotlib.pyplot as plt
from fastapi import FastAPI

file_name = "graph.ml"
location = "Warszawa, Poland"

if not os.path.exists(file_name):
    print("Downloading graph")
    G = ox.graph_from_place(location, network_type='drive')
    G = ox.routing.add_edge_speeds(G, fallback=30)
    G = ox.routing.add_edge_travel_times(G) # adds travel time (seconds) to each edge
    ox.io.save_graphml(G, file_name)
else:
    print("Loading graph")
    G = ox.io.load_graphml(file_name)

def heur(n1, n2):
    n1x = G.nodes[n1]['x']
    n1y = G.nodes[n1]['y']
    n2x = G.nodes[n2]['x']
    n2y = G.nodes[n2]['y']
    return ox.distance.great_circle(n1x, n1y, n2x, n2y)

def heur_travel_time(n1, n2):
    n1x = G.nodes[n1]['x']
    n1y = G.nodes[n1]['y']
    n2x = G.nodes[n2]['x']
    n2y = G.nodes[n2]['y']
    # multiplied by Magic number - time needed to travel 1 meter at 100km/h
    return ox.distance.great_circle(n1x, n1y, n2x, n2y)*0.036

app = FastAPI()

@app.get("/path")
def get_path(lat1: float, lon1: float, lat2: float, lon2: float):
    orig = ox.distance.nearest_nodes(G, lon1, lat1)
    dest = ox.distance.nearest_nodes(G, lon2, lat2)
    route_nodes = nx.astar_path(G, orig, dest)
    if len(route_nodes) < 2:
        return {}
    gpd_route = ox.routing.route_to_gdf(G, route_nodes)
    gpd_route.to_file("route.geojson")
    with open("route.geojson", "r") as f:
        return f.read()

