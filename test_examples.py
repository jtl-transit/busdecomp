import sys
 
# Set path to parent directory
sys.path.append('../')
 
# Import functions
from busdecomp import busdecomp_gtfs
from shape_generation import map_matching, shape_matching
from edge_decomposition import edge_decomposition
from compare_edges import compare_edges

gtfs_shapes = True
compare = True
metrics = True
port = 8002
route_ids = [None, None]

base_path = 'data/MBTA_GTFS_OCT2019.zip'
comp_path = 'data/MBTA_GTFS_OCT2020.zip'
road_path = 'data/boston_roads_small.shp'

# Filter to one specific route for this example to limit file sizes
route_ids = [['1'], ['1']]

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

# busdecomp_gtfs(base_path, comp_path, road_path, metrics = True, route_ids = route_ids)