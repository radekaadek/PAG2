import osmnx as ox
import networkx as nx
import os
import time
import geopandas as gpd

source_lat, source_lon = 8.5686, 76.8731
dest_lat, dest_lon = 8.52202892500963, 76.926448394559

file_name = "graph.ml"

if not os.path.exists(file_name):
    print("Downloading graph")
    north = max(source_lat, dest_lat)
    south = min(source_lat, dest_lat)
    east = max(source_lon, dest_lon)
    west = min(source_lon, dest_lon)
    G = ox.graph.graph_from_bbox(bbox=(north, south, east, west),
                                 network_type='drive')
    ox.io.save_graphml(G, file_name)
else:
    print("Loading graph")
    G = ox.io.load_graphml(file_name)

print(f"Number of nodes: {len(G.nodes)}")
print(f"Number of edges: {len(G.edges)}")



# fetch the nearest node w.r.t coordinates
orig = ox.distance.nearest_nodes(G, source_lon, source_lat)
dest = ox.distance.nearest_nodes(G, dest_lon, dest_lat)

def heur(n1, n2):
    n1x = G.nodes[n1]['x']
    n1y = G.nodes[n1]['y']
    n2x = G.nodes[n2]['x']
    n2y = G.nodes[n2]['y']
    destx = dest_lon
    desty = dest_lat
    # distance from n1 to dest minus distance from n2 to dest
    return ox.distance.great_circle(n1x, n1y, destx, desty) - ox.distance.great_circle(n2x, n2y, destx, desty)



# find shortest path
before = time.perf_counter()
route_nodes = nx.astar_path(G, orig, dest, weight="length", heuristic=heur)
after = time.perf_counter()
print(f"Time taken: {after - before} seconds")


# plot the shortest path
fig, ax = ox.plot_graph_route(G, route_nodes, route_color="r", 
                              route_linewidth=6, node_size=0)

gpd_route = ox.routing.route_to_gdf(G, route_nodes)

# save to route.geojson
gpd_route.to_file("route.geojson")


