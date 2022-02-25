""" 

This program is used to find the set of "pieces" spanned by the routes in a 
bus transit network. An piece is a section of the road network split at 
intersections or bus stop locations. Each piece is assigned a unique
identification number. A list of the route patterns that traverse each piece
is stored as an attribute of the piece.

There are several different terms herein used to refer to sections of a bus 
route or street network at different resolutions. For clarity, they are 
briefly defined here:
    
Segment: The section of a bus route between two consecutive stops.

Way:     An OpenStreetMap element that represents a street. Can span one or more
         blocks. Not unique for different travel directions on a two-way street.

Edge:    A Valhalla output, which represents a directional section of the road
         network between two intersections (roughly equivalent to a city block)

Piece:   The smallest resolution. Pieces are edges that are also split at 
         mid-block bus stops. One edge may contain two or more pieces. 

IMPORTANT NOTE:
- The OSM download used for the map matching in Valhalla should be the same
  version as the shapefile used to look up OSM way shapes. Both are collected
  from the same source (geofabrik.de). Otherwise the transit shapes might be 
  matched to ways that no longer exist, or do not exist yet, in OSM.

Author: Nick Caros, September 2020

"""

import polyline
import requests
import json
import time
from shapely.geometry import LineString, Point
from pyproj import Geod
import geopandas as gpd

def edge_decomposition(segments, road_inpath):
    
    turn_penalty_factor = 100 # Penalizes turns in Valhalla routes. Range 0 - 100,000.
    maneuver_penalty = 60 # Penalty when a route includes a change from one road to another (seconds). Range 0 - 43,200. 
    search_radius = 15 # Radius for searching in the map matching
    
    midblock_tolerance = 0 # Maximum distance from center of intersection for a bus stop to be considered "mid-block"
    
    """ Function and Class Definitions """
    
    # Initialize Valhalla input dictionary with some empty values
    request_parameters = {'shape': None,
                          'costing': 'bus',
                          'shape_match': 'map_snap',
                          'filters':{
                              'attributes': ['edge.id',
                                             'edge.way_id',
                                             'edge.begin_shape_index',
                                             'edge.end_shape_index',
                                             'shape'],
                              'action':'include'
                              },
                          'costing_options':{'bus':{'maneuver_penalty': maneuver_penalty}},
                          'trace_options':{"turn_penalty_factor": turn_penalty_factor,
                                           'search_radius': None},
                          }
    
    
    
    class Edge: # Attributes for edge traversed by the routes in the network
        def __init__(self, way_id):
            self.way = way_id
            self.break_points = []
            self.bounds = []
            self.segments = []
            self.routes = []
    
    class Piece: # Attributes for partial edges, split at bus stops or service changes
        def __init__(self, edge, shape):
            self.edge = edge
            self.shape = shape
            self.segments = []
            self.routes = []
    
    # Function to extract the shape associated with one edge from the full segment shape
    def extract_edge_shapes(result):
    
        temp_dict = {}    
        return_dict = {}
        
        # Get coordinates from the polyline shape
        seg_shape_coords = polyline.decode(result['shape'], geojson = True, precision = 6)
        for edge in result['edges']:
    
            edge_start = edge['begin_shape_index']
            edge_end= edge['end_shape_index']
            
            temp_dict[edge['id']] = seg_shape_coords[edge_start : edge_end + 1]
        
        # Check that there aren't any lines which are two identical coordinates (possible output from Valhalla)
        for edge in temp_dict:
            edge_len = len(temp_dict[edge])
            if edge_len == 2:
                edge_start = temp_dict[edge][0]
                edge_end = temp_dict[edge][1]
                if edge_start == edge_end:
                    continue
            return_dict[edge] = temp_dict[edge]
        
        return return_dict
    
    def update_edge(edge_dict, edge_id, new_coords, stop_pair, route):
        
        edge_dict[edge_id].break_points.append(new_coords[0])
        edge_dict[edge_id].break_points.append(new_coords[-1])
        edge_dict[edge_id].bounds.append((new_coords[0], new_coords[-1]))
        edge_dict[edge_id].segments.append(stop_pair)
        edge_dict[edge_id].routes.append(route)
        
        return edge_dict
    
    # Function for cutting a line at a point
    def cut(line, stop):
        distance = line.project(stop)
        
        # Cuts a line in two at a distance from its starting point
        if distance <= 0.0 or distance >= line.length:
            return [LineString(line), None]
        coords = list(line.coords)
        last_pd = 0
        for i, p in enumerate(coords):
            pd = line.project(Point(p))
    
            if pd < last_pd: # Error handling for circular segments
                pd = last_pd + pd
            
            if pd == distance:
                return [
                    LineString(coords[:i+1]),
                    LineString(coords[i:])]
            if pd > distance:
                cp = line.interpolate(distance)
                return [
                    LineString(coords[:i] + [(cp.x, cp.y)]),
                    LineString([(cp.x, cp.y)] + coords[i:])]
            last_pd = pd
    
        return [LineString(line), None]
    
    """ Main Program """
    
    origin_time = time.time()
    
    # Load shapes file with stop-to-stop segment resolution
    with open(segments) as f:
      segment_dict = json.load(f)
    
    # """ TO BE DELETED """
    # # DO NOT USE: FOR DEBUGGING ONLY
    # temp_list = []
    # for seg in segment_dict:
    #     if seg['route_id'] == '47':
    #         temp_list.append(seg)
    # segment_dict = temp_list
    # """ END TBD """ 
    
    # Use Valhalla to find the set of edges that comprise each stop-to-stop segment
    edge_dict = {}
    mm_dict = {}
    start_time = time.time()
    error_count = 0
    for count, segment in enumerate(segment_dict):
        
        stop_pair = tuple([segment['stop_pair'][0], segment['stop_pair'][1]])
        
        # If already processed this stop pair, continue
        if stop_pair in mm_dict: 
            elapsed_time = time.time() - start_time
            if count % 100 == 0: print('Edges matched for', count, 'of', len(segment_dict), 'patterns', "Elapsed time:", round(elapsed_time,0))
            continue
        
        else:
            
            error_binary = False
            radius = search_radius 
            
            # Get segment info
            seg_polyline = segment['geometry']
            route = segment['route_id']
            
            # If request times out, try twice more and then raise an error
            to_count = 1
            while to_count < 6:
                try:
                    # Use Valhalla map matching engine to snap shapes to the road network
                    request_data = request_parameters.copy()
                    request_data['encoded_polyline'] = seg_polyline
                    request_data['trace_options']['search_radius'] = radius
                    req = requests.post('http://localhost:8002/trace_attributes',
                                        data = json.dumps(request_data),
                                        timeout = 30)
                    
                    # Extract encoded polyline from Valhalla response
                    result = req.json()
                    
                    # Error handling for unexpected Valhalla responses - add to search radius
                    if len(result) == 4:
                        print("Valhalla did not find shape for", str(stop_pair), ", Count = ", str(count))
                        radius += 5
                        if radius > 100: 
                            error_count += 1
                            error_binary = True
                            break
                        else:
                            continue
                        #raise Exception("Valhalla error: Check error messages or restart matching.")
                        
                    mm_dict[stop_pair] = result
                    to_count = 10
                    
                except:
                    print("Timeout #", to_count)
                    to_count += 1
                    
                if to_count == 5:
                    raise Exception("Valhalla timeout: Check error messages or restart matching.")
        
        if error_binary:
            continue
        else:
                       
            edge_shapes = extract_edge_shapes(result)
        
            # Add the resulting pieces to the piece dictionary
            for edge in result['edges']:
                edge_id = edge['id']
                try:
                    new_coords = edge_shapes[edge_id]
                except:
                    break
                
                if edge_id not in edge_dict: # If we already saw this edge, just add new info
                    edge_dict[edge_id] = Edge(edge['way_id'])
                    
                edge_dict = update_edge(edge_dict, edge_id, new_coords, stop_pair, route)
    
        elapsed_time = time.time() - start_time
        if count % 100 == 0: print('Edges matched for', count, 'of', len(segment_dict), 'patterns', "Elapsed time:", round(elapsed_time,0))
    
    
    # Get dictionary of way shapes from OSM
    shapefile = gpd.read_file(road_inpath, crs='EPSG:4326')
    way_dict = dict(zip(shapefile['osm_id'], shapefile['geometry']))
    shapefile = None

    # Set up function to calculate line lengths in feet
    geod = Geod(ellps="WGS84")
    
    # Now split edges into "pieces" at any mid-block bus stops
    piece_dict = {}
    for edge in edge_dict:
        
        # Keep only unique break points
        break_points = edge_dict[edge].break_points
        unique_breaks = list(set(break_points))
        
        # If all break points are the same, the edge is a point and we can skip
        if len(unique_breaks) == 1:
            print('Edge is a point: ', edge)
            continue
        
        way_id = str(edge_dict[edge].way)
        try:
            full_line = way_dict[way_id]
            line_length_ft = geod.geometry_length(full_line) * 3.28084 # meters to ft
        except KeyError:
            print('Error, No way available for ', way_id)
            continue
        
        # Discard break points that are at the ends of the line
        int_points = []
        distances = []
        line_start = False
        line_end = False
        for point in unique_breaks:
            point_geom = Point(point)
            distance = full_line.project(point_geom, normalized = True)
            
            if distance * line_length_ft <= midblock_tolerance:
                line_start = True
            elif (1 - distance) * line_length_ft < midblock_tolerance:
                line_end = True
            else:
                int_points.append(point_geom)
                distances.append(distance)
    
        # If there are no break points, create the piece and continue
        if len(distances) == 0:
            if line_start and line_end:
                
                bounds = edge_dict[edge].bounds
                segments = edge_dict[edge].segments
                routes = edge_dict[edge].routes
                
                piece_dict[(edge, 0)] = Piece(edge, full_line)
                
                for seg_index, segment in enumerate(bounds):
                    stops = segments[seg_index]
                    route = routes[seg_index]
                    piece_dict[(edge, 0)].segments.append(stops)
                    piece_dict[(edge, 0)].routes.append(route)
                
                continue
            
            # Otherwise the edge is within the tolerance, and we don't need it
            else:
                print('Mismatch for: ', edge)
                continue
            
        sorted_points = [x for _,x in sorted(zip(distances, int_points), key=lambda distance: distance[0])]
        sorted_distances = sorted(distances)
        piece_count = 0
        
        # If edge starts at first line in the way, then just split it normally
        if line_start:
            remainder = full_line
            for point in sorted_points:
                piece_geom, remainder = cut(remainder, point)
                piece_dict[(edge, piece_count)] = Piece(edge, piece_geom)
                piece_count += 1
                if remainder == None:
                    break
        
        # Otherwise, ignore the section before the first break point
        else:
            sorted_distances = sorted_distances[1:]
            _, remainder = cut(full_line, sorted_points[0])
            if remainder != None: 
                for index, point in enumerate(sorted_points[1:]):
                    piece_geom, remainder = cut(remainder, point)
                    piece_dict[(edge, piece_count)] = Piece(edge, piece_geom)
                    piece_count += 1
                    if remainder == None:
                        # piece_dict[(edge, piece_count)].segments.append(stops)
                        # piece_dict[(edge, piece_count)].routes.append(route)
                        break
            else:
                continue
    
        # If edge continues to the end of the way, then add the remainder as a new piece
        if line_end:
            piece_dict[(edge, piece_count)] = Piece(edge, remainder)
        else:
            sorted_distances = sorted_distances[:-1]
        
        # Associate each unique segment with one or more pieces using bounds
        bounds = edge_dict[edge].bounds
        segments = edge_dict[edge].segments
        routes = edge_dict[edge].routes
        
        for seg_index, segment in enumerate(bounds):
            stops = segments[seg_index]
            route = routes[seg_index]
            
            if len(sorted_distances) == 0:
                piece_dict[(edge, 0)].segments.append(stops)
                piece_dict[(edge, 0)].routes.append(route)
            else:
                start = full_line.project(Point(segment[0]), normalized=True)
                end = full_line.project(Point(segment[1]), normalized=True)
                
                if start > end: # Switch directions
                    start, end = [end, start]
                
                for index, piece_dist in enumerate(sorted_distances):
                    if start < piece_dist and end >= piece_dist:
                        piece_dict[(edge, index)].segments.append(stops)
                        piece_dict[(edge, index)].routes.append(route)
                
                if end > piece_dist:
                    piece_dict[(edge, index + 1)].segments.append(stops)
                    piece_dict[(edge, index + 1)].routes.append(route)
                
    # Save pieces as a geoJSON with relevant properties
    edge_list = []
    route_list = []
    segment_list = []
    index_list = []
    start_list = []
    end_list = []
    polyline_list = []
    geom_list = []
    tup_list = []
    
    for piece in piece_dict:
        piece_object = piece_dict[piece]
        routes = piece_object.routes
        
        # If a piece was created from geometry but isn't served, ignore it
        if len(routes) == 0:
            continue
        
        edge = piece_object.edge
        segments = piece_object.segments
        shape = piece_object.shape
        start = shape.coords[0]
        end = shape.coords[-1]
        piece_polyline = polyline.encode(shape.coords, precision = 6)
                    
        seg_indices = {}
        stop_indices = {}
        route_dict = {}
        seg_index_list = []
        for index, seg in enumerate(segments):
            start_stop = seg[0]
            end_stop = seg[1]
            route = routes[index]
            
            route_dict[index] = route
            stop_indices[index] = route + '-' + start_stop + '-' + end_stop
            seg_indices[index] = start_stop + '-' + end_stop
            seg_index_list.append(route + '-' + start_stop + '-' + end_stop)
            
        tup_list.append(tuple(seg_index_list))
                
        edge_list.append(edge)
        route_list.append(route_dict)
        segment_list.append(seg_indices)
        index_list.append(stop_indices)
        start_list.append(str(start))
        end_list.append(str(end))
        polyline_list.append(piece_polyline)
        geom_list.append(shape)
         
    # Build geodataframe for each piece       
    piece_gdf = gpd.GeoDataFrame(geometry = geom_list)
    piece_gdf['edge'] = edge_list
    piece_gdf['route_id'] = route_list
    piece_gdf['segments'] = segment_list
    piece_gdf['indices'] = index_list
    piece_gdf['polyline'] = polyline_list
    
    gdf = gpd.GeoDataFrame(geometry = geom_list)
    gdf['edge'] = edge_list
    gdf['route_id'] = route_list
    gdf['segments'] = segment_list
    gdf['indices'] = index_list
    gdf['polyline'] = polyline_list
    
    # Export to file
    gdf = gdf.sort_values(by = ['edge'])
    gdf.to_file("output/edge_shapes.geojson", driver='GeoJSON')         
    total_time = time.time() - origin_time
    print("Total elapsed time:", round(total_time,0))