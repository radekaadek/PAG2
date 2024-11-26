import osmnx as ox
import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt
from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
import os
from fastapi.staticfiles import StaticFiles


file_name = "graph.ml"
location = "Warszawa, Poland"

def load_graph(network_type: str) -> nx.Graph:
    G = ox.graph_from_place(location, network_type=network_type)
    G = ox.routing.add_edge_speeds(G, fallback=30)
    G = ox.routing.add_edge_travel_times(G) # adds travel time (seconds) to each edge
    ox.io.save_graphml(G, file_name)
    return G

G = load_graph(network_type='drive')

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

@app.get("/shortest_path")
def get_path(lat1: float, lon1: float, lat2: float, lon2: float) -> str | dict:
    try:
        orig = ox.distance.nearest_nodes(G, lon1, lat1)
        dest = ox.distance.nearest_nodes(G, lon2, lat2)
        route_nodes = nx.astar_path(G, orig, dest, weight="length", heuristic=heur)
        if len(route_nodes) < 2:
            return {}
        # Get route coordinates
        route_coords = [
            (G.nodes[node]["y"], G.nodes[node]["x"]) for node in route_nodes
        ]

        # Return route as a GeoJSON-like structure
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[lon, lat] for lat, lon in route_coords],
                    },
                    "properties": {"distance_meters": sum(ox.utils_graph.get_route_edge_attributes(G, route_nodes, 'length'))}
                }
            ],
        }
    except Exception as e:
        return {"error": str(e)}
        

@app.get("/quickest_path")
def get_quickest_path(lat1: float, lon1: float, lat2: float, lon2: float) -> str | dict:
    try:
        orig = ox.distance.nearest_nodes(G, lon1, lat1)
        dest = ox.distance.nearest_nodes(G, lon2, lat2)
        route_nodes = nx.astar_path(G, orig, dest, weight="travel_time", heuristic=heur_travel_time)
        if len(route_nodes) < 2:
            return {}
                # Get route coordinates
        route_coords = [
            (G.nodes[node]["y"], G.nodes[node]["x"]) for node in route_nodes
        ]

        # Return route as a GeoJSON-like structure
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[lon, lat] for lat, lon in route_coords],
                    },
                    "properties": {"distance_meters": sum(ox.utils_graph.get_route_edge_attributes(G, route_nodes, 'length'))}
                }
            ],
        }
    except Exception as e:
        return {"error": str(e)}

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve the HTML file
@app.get("/")
def read_root():
    return FileResponse(os.path.join("static", "index.html"))