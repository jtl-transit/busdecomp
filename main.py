""" 

This is the main program for the bus transit decomposition method described
in Caros, Stewart and Attanucci (2022). 

It takes as an input the filepath for a standard GTFS feed, and returns
a geoJSON file containing the edge-level representation of the bus transit
network, including the route ID and stop ID pair for each route traversing
the edge. 

Note that this program requires the Valhalla map matching engine to be
configured for the appropriate region and running locally. Instructions
for installing and configuring Valhalla are included in this repo. 


""" 

from shape_generation import map_matching, shape_matching
from edge_decomposition import edge_decomposition

# inpath: link to a standard GTFS feed in .zip format
# gtfs_shapes: an optional indicator of whether the shapes.txt table in the 
# GTFS feed should be used to create the route shapes.  
def main(gtfs_inpath, road_inpath, gtfs_shapes = False):
    
    # Generate the initial shapes defining the path of the bus routes.
    if gtfs_shapes:
        segments = shape_matching(gtfs_inpath)
    else: 
        segments = map_matching(gtfs_inpath)
    
    # Decompose the shapes into edge-length segments and save them to file.
    edge_decomposition(segments, road_inpath)
 
    
gtfs_inpath = 'data/mbta_09_2019.zip'
road_inpath = 'data/gis_osm_roads_free_1.shp'
main(gtfs_inpath, road_inpath, True)