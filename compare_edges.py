"""

This program takes two shapefiles representing "pieces", a block or partial
block shape served by a bus route. Each shapefile should represent a different
period of service. It also takes two dictionaries containing some performance
metric for the bus service represented by each of the shapefiles. 

The output is a combined shapefile containins all of the unique pieces across
both input shapefiles. A new property is appended: the difference in the
performance metric between the baseline period and the comparison period.

"""

from shapely.geometry import MultiLineString
import partridge as ptg
import pandas as pd
import geopandas as gpd
import time

def compare_edges(base_gtfs_path, comp_gtfs_path, base_shapes_path, comp_shapes_path, metrics = False):
    
    origin_time = time.time()
    
    # Maximum distance between two lines for them to be considered the same line (in feet)
    distance_threshold = 15
    
    # Function to convert route_id from GTFS into route_short_name from GTFS, which is useful in some applications
    def convert_route_ids(df, feed):
        
        feed_routes = feed.routes
        route_dict = dict(zip(feed_routes['route_id'], feed_routes['route_short_name']))
        new_ids = []
        for i in df['route_id'].values.tolist():
            new_ids.append(route_dict[i])
            
        df['route_id'] = new_ids
        
        return df
    
    # Function to find average daily trips for each segment using GTFS
    def average_daily_trips(inpath, base_indicator):
        
        # Import GTFS feed and filter down to normal bus routes only
        route_type = ['3']
        view = {'routes.txt': {'route_type': route_type}}
        feed = ptg.load_feed(inpath, view)
        feed_stop_events = feed.stop_times[['trip_id', 'stop_id', 'stop_sequence']]
        
        feed_trips = feed.trips[['route_id','trip_id']]
        feed_trips = convert_route_ids(feed_trips, feed)
        all_stops = pd.merge(feed_trips, feed_stop_events, on='trip_id', how='inner')
        all_stops = all_stops.sort_values(by=['trip_id', 'stop_sequence'])
        
        arrivals_dict = {}
        
        stop_events = all_stops.values.tolist()
        for index, stop_event in enumerate(stop_events[:-1]):
            sequence = stop_event[3]
            if sequence == 1:
                continue
            
            next_stop = index + 1
            
            stop_id = stop_event[2]
            next_stop_id = stop_events[next_stop][2]
            route = stop_event[0]
            
            segment = str(route) + '-' + str(stop_id) + '-' + str(next_stop_id)
            
            if segment not in arrivals_dict:
                arrivals_dict[segment] = 1
            else:
                arrivals_dict[segment] += 1
        
        return arrivals_dict 
    
    if metrics:
        base_metrics = average_daily_trips(base_gtfs_path, True)
        comp_metrics = average_daily_trips(comp_gtfs_path, False)
      
    base_shapes = gpd.read_file(base_shapes_path, crs='EPSG:4326').to_crs('EPSG:2249')
    comp_shapes = gpd.read_file(comp_shapes_path, crs='EPSG:4326').to_crs('EPSG:2249')
    comp_shapes['index'] = range(len(comp_shapes))
    
    # Cycle through base shapes first, find matches and append metrics
    geom_index = base_shapes.columns.get_loc("geometry")
    seg_index = base_shapes.columns.get_loc("indices")
    edge_index = base_shapes.columns.get_loc("edge")
    poly_index = base_shapes.columns.get_loc("polyline")
    index_index = comp_shapes.columns.get_loc("index")
    
    segment_list = []
    geometry_list = []
    metric_list = []
    polyline_list = []
    edge_list = []
    indicator_list = [] # 0 = dropped service; 1 = new service; 2 = maintained service
    comp_matched = []
    
    for piece in base_shapes.values.tolist():
        keep_base = True
        match = False
        indicator = 0
        base_total = 0
        comp_total = 0
        comp_segments = None
        
        edge = piece[edge_index]
        base_segments = piece[seg_index]
        base_polyline = piece[poly_index]
        base_line = piece[geom_index]
    
        if metrics:
            for segment in base_segments:
                segment_key = base_segments[segment]
                try:
                    base_total += base_metrics[segment_key]
                except KeyError:
                    continue
        
        # Check potential matches using edge numbers
        potential_matches = comp_shapes[comp_shapes['edge'] == edge].values.tolist()
        
        # Check if this is a split (i.e. edge in the base is two edges in the comp)
        if len(potential_matches) > 1:
            
            # Are there strictly more edges with this way ID in the comp network than the base?
            if len(base_shapes[base_shapes['edge'] == edge]) < len(potential_matches):
                
                # Is there a minimal distance between the large line and the two (or more) smaller lines?
                combined_line = MultiLineString([i[geom_index] for i in potential_matches])
                if base_line.hausdorff_distance(combined_line) < distance_threshold:
                    
                    # Add the two smaller lines to the match dict and drop the larger line
                    match = True
                    keep_base = False
                    indicator = 2
                    for match in potential_matches:
                        comp_matched.append(match[index_index])
                        comp_segments = match[seg_index]
    
        # Check for matches using the edge ID
        if not match:
            for potential_match in potential_matches:
                comp_line = potential_match[geom_index]
                if base_line.hausdorff_distance(comp_line) < distance_threshold:
                    match = True
                    indicator = 2
                    comp_matched.append(potential_match[index_index])
                    if metrics: 
                        comp_segments = potential_match[seg_index]
                        for segment in comp_segments:
                            segment_key = comp_segments[segment]
                            try:
                                comp_total += comp_metrics[segment_key]
                            except KeyError:
                                continue
                    break
        
        # If edge match is unsuccessful, try matching using polylines
        if not match:
            potential_matches = comp_shapes[comp_shapes['polyline'] == base_polyline].values.tolist()
    
            for potential_match in potential_matches:
                comp_line = potential_match[geom_index]
                if base_line.hausdorff_distance(comp_line) < distance_threshold:
                    match = True
                    
                    print(edge, potential_match[edge_index])
                    
                    indicator = 2
                    comp_matched.append(potential_match[index_index])
                    if metrics:
                        comp_segments = potential_match[seg_index]
                        for segment in comp_segments:
                            segment_key = comp_segments[segment]
                            try:
                                comp_total += comp_metrics[segment_key]
                            except KeyError:
                                continue
                    break
    
        # If both are unsuccessful, try matching using spatial intersection
        if not match: 
            # Any lines that overlap
            inter = comp_shapes.intersects(base_line)
            potential_matches = comp_shapes[inter].values.tolist()
            
            for potential_match in potential_matches:
                comp_line = potential_match[geom_index]
                if base_line.hausdorff_distance(comp_line) < distance_threshold:
                    match = True
                    indicator = 2
                    comp_matched.append(potential_match[index_index])
                    if metrics:
                        comp_segments = potential_match[seg_index]
                        for segment in comp_segments:
                            segment_key = comp_segments[segment]
                            try:
                                comp_total += comp_metrics[segment_key]
                            except KeyError:
                                continue
                    break
        
        # If this is a conventional match
        if keep_base:
            geometry_list.append(base_line)
            polyline_list.append(base_polyline)
            edge_list.append(edge)
            indicator_list.append(indicator)
            output_segments = {}
            output_segments['base'] = base_segments
            output_segments['comp'] = comp_segments
            segment_list.append(output_segments)
            metric_list.append(comp_total - base_total)
        
        else: # If it is a split match, keep the smaller comparison segments
            for potential_match in potential_matches:
                geometry_list.append(potential_match[geom_index])
                polyline_list.append(potential_match[poly_index])
                edge_list.append(potential_match[edge_index])
                indicator_list.append(indicator)
                output_segments = {}
                output_segments['base'] = base_segments
                output_segments['comp'] = comp_segments
                segment_list.append(output_segments)
                metric_list.append(comp_total - base_total)
        
    # Add metrics to any leftover comparison shapes and add to combined dict
    for piece in comp_shapes.values.tolist():
        comp_polyline = piece[poly_index]
        edge = piece[edge_index]
        index = piece[index_index]
        comp_total = 0
    
        if index in comp_matched: # if the polyline has been matched within given tolerance, ignore
            continue
        
        if metrics:
            comp_segments = piece[seg_index]
            for segment in comp_segments:
                segment_key = comp_segments[segment]
                try:
                    comp_total += comp_metrics[segment_key]
                except KeyError:
                    continue
        
        geometry_list.append(piece[geom_index])
        polyline_list.append(comp_polyline)
        edge_list.append(edge)
        indicator_list.append(1)
        output_segments = {}
        output_segments['base'] = None
        output_segments['comp'] = comp_segments
        segment_list.append(output_segments)
        metric_list.append(comp_total)
    
    gdf = gpd.GeoDataFrame(geometry = geometry_list)
    gdf['polyline'] = polyline_list
    gdf['segments'] = segment_list
    gdf['metric'] = metric_list
    gdf['edge'] = edge_list
    gdf['service_indicator'] = indicator_list
    
    gdf = gdf.sort_values(by = ['edge'])
    gdf = gdf.set_crs('EPSG:2249')
    gdf = gdf.to_crs('EPSG:4326')
    
    basefilename = base_gtfs_path.split('/')[-1]
    compfilename = comp_gtfs_path.split('/')[-1]
    outpath = '../output/' + basefilename[:-4] + "_vs_" + compfilename[:-4] + ".geojson"
    gdf.to_file(outpath, driver='GeoJSON')         
    
    total_time = time.time() - origin_time
    print("Total elapsed time:", round(total_time,0))
