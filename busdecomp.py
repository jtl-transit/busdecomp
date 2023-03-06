""" 

This is the main program for the bus transit decomposition method described
in Caros, Stewart and Attanucci (2022). 

It takes as an input the filepath for a standard GTFS feed, and returns
a geoJSON file containing the edge-level representation of the bus transit
network, including the route ID and stop ID pair for each route traversing
the edge. 

Note that this program requires the Valhalla map matching engine to be
configured for the appropriate region and running locally. Instructions
for installing and configuring Valhalla are included in the README file. 


""" 

from shape_generation import map_matching, shape_matching
from edge_decomposition import edge_decomposition
from compare_edges import compare_edges

# This function starts the decomposition process from scratch using a GTFS feed and a road network file
def busdecomp_gtfs(base_path, comp_path, road_path, gtfs_shapes = False,
                    compare = True, metrics = False, port = 8002, route_ids = [None, None]):
    
    # Generate the initial shapes defining the path of the bus routes.
    if gtfs_shapes:
        base_segments = shape_matching(base_path, route_ids = route_ids[0])
        comp_segments = shape_matching(comp_path, route_ids = route_ids[1])
    else: 
        base_segments = map_matching(base_path, route_ids = route_ids[0])
        comp_segments = map_matching(comp_path, route_ids = route_ids[1])
    
    # Decompose the shapes into edge-length segments and save them to file with same root filename as input gtfs feeds.
    edge_decomposition(base_segments, road_path, base_path[:-4], port = port)
    edge_decomposition(comp_segments, road_path, comp_path[:-4], port = port)

    # Compare the two segments (metrics optional) and save them to file.
    if compare:
        
        # Get the output path from edge_decomposition by removing the '.zip' file extension
        base_shapes = base_path[:-4] + '.geojson'
        comp_shapes = comp_path[:-4] + '.geojson'
        compare_edges(base_path, comp_path, base_shapes, comp_shapes, metrics = metrics)

# This function runs the comparison only if shapes have already been generated
def busdecomp_edges(base_gtfs, comp_gtfs, base_shapes, comp_shapes, metrics = False):
    
    # Compare the two segments (metrics optional) and save them to file.
    compare_edges(base_gtfs, comp_gtfs, base_shapes, comp_shapes, metrics = metrics)

# base_path = 'data/MBTA_JAN2011_reduced.zip'
# comp_path = 'data/MBTA_JAN2021_reduced.zip'
# road_path = 'data/boston_roads_reduced.shp'

# busdecomp_gtfs(base_path, comp_path, road_path, metrics = True)