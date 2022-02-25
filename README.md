# Spatial Decomposition of Bus Transit Networks 

This is the main repository for the bus transit decomposition method described
in Caros, Stewart and Attanucci (2022). 

It takes as an input the filepath for a standard GTFS feed, and returns
a geoJSON file containing the edge-level representation of the bus transit
network, including the route ID and stop ID pair for each route traversing
the edge. 

Note that this program requires the Valhalla map matching engine to be
configured for the appropriate region and running locally. Instructions
for installing and configuring Valhalla are included in this repo. 
