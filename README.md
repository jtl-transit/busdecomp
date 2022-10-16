# Spatial Decomposition of Bus Transit Networks 

This is the main repository for the bus transit decomposition method described
in a recent submission to Environment and Planning B. 

It takes as an input the filepath for a standard GTFS feed, and returns
a geoJSON file containing the edge-level representation of the bus transit
network, including the route ID and stop ID pair for each route traversing
the edge. 

Note that this program requires the Valhalla map matching engine to be
configured for the appropriate region and running locally. Instructions
for installing and configuring Valhalla are included in a [readme file](valhalla_readme.md). 

This program was written for Python 3.9, and required packages are available in [requirements.txt](requirements.txt).
