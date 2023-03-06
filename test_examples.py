import sys
 
# Set path to parent directory
sys.path.append('../')
 
# Import functions
from busdecomp import *

comp_path = '../data/MBTA_JAN2011_reduced.zip'
base_path = '../data/MBTA_JAN2021_reduced.zip'
road_path = '../data/boston_roads_reduced.shp'

busdecomp_gtfs(base_path, comp_path, road_path, metrics = True)