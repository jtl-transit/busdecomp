## Valhalla Installation and Configuration Instructions

To run the shape generation file, you will need to install and configure the open source map matching service [Valhalla](https://github.com/valhalla/valhalla).

These instructions were generated while running the Windows Subsystem for Linux (WSL) with Ubuntu 18.04 LTS distribution. It can be downloaded for free at the Microsoft Store. These instructions worked for the latest version of Valhalla (3.0.9).

### Installation

I followed the impressive two-part tutorial written by Justin Pisotta available at the links below. It explains each step in simple language which was very helpful. Note that it is not specifically designed for WSL, but it seems to work regardless. Some of the checks resulted in errors, but I just kept going without any further problems.

Over time the static tutorial has not entirely kept up with changes to Valhalla. I needed two deviations from the entire two-part tutorial: 1) One additional dependency is needed. Enter `sudo apt-get install -y libluajit-5.1-dev` after the "Install the remaining dependencies" step in Part 1, and 2) the very last command in part 1 is `make install`, but that raised a permissions error for me, so I ran `sudo make install` instead which executed successfully. I did not follow any of the optional steps as they were not relevant to map matching.
  
Part 1: https://gis-ops.com/valhalla-part-1-how-to-install-on-ubuntu-18-04/

Part 2: https://gis-ops.com/valhalla-how-to-run-with-docker-on-ubuntu-18-04/

I ran Valhalla and successfully passed the test in Part 2, Step 4. If you follow those steps, ending with the `valhalla_service ~/valhalla/scripts/conf/valhalla.json 1` command, Valhalla will be running on localhost:8002. The Python code for map matching available in this repo assumes that Valhalla is running on 8002.

### Configuration

Following the steps in Part 2, the service will be set up with the OSM street network for Albania. Presumably you are not trying to map match bus routes in Tirana, so you'll need to backtrack a little bit to run Valhalla with your preferred street network. The first step is to delete the files that you've created relating to the Albanian road network:

```
cd ~/valhalla/scripts
rm -rfv conf
rm -rfv valhalla_tiles
rm valhalla_tiles.tar
```

Then re-run some of Part 2 to download and configure the new OSM network. This example uses the Massachusetts network, but you can replace it with any region - just browse https://download.geofabrik.de/ to find the appropriate url.


```
mkdir valhalla_tiles && mkdir conf
valhalla_build_config --mjolnir-tile-dir ${PWD}/valhalla_tiles --mjolnir-tile-extract ${PWD}/valhalla_tiles.tar --mjolnir-timezone ${PWD}/valhalla_tiles/timezones.sqlite --mjolnir-admin ${PWD}/valhalla_tiles/admins.sqlite > ${PWD}/conf/valhalla.json
curl -O https://download.geofabrik.de/north-america/us/massachusetts-latest.osm.pbf
valhalla_build_tiles -c ./conf/valhalla.json massachusetts-latest.osm.pbf
find valhalla_tiles | sort -n | tar -cf "valhalla_tiles.tar" --no-recursion -T -
valhalla_service ~/valhalla/scripts/conf/valhalla.json 1
```

After entering the commands above, I was successfully able to pass requests from the shape generation script to Valhalla and get the map matched coordinates in return.

### Use for Map Matching

First, review the documentation here: https://valhalla.readthedocs.io/

For the specific map matching case, I used the following code to make Valhalla requests and parse the results:

```
to_count = 1
while to_count < 4:
    try:
        # Use Valhalla map matching engine to snap shapes to the road network
        req = requests.post('http://localhost:8002/trace_route',
                            data=json.dumps(
                              {'shape': coords[start_point:],
                               'costing': 'bus',
                               'shape_match': 'map_snap',
                               'trace_options.search_radius': '100',
                               'trace_options.interpolation_distance': '100',
                               'trace_options.turn_penalty_factor': '500'}),
        timeout=10)
        to_count = 10
    except:
        print("Timeout #", to_count)
        to_count += 1
    if to_count == 4:
        raise Exception('Request ', mm_count,' timed out 3x')

    # Extract encoded polyline from Valhalla response and store
    result = req.json()
```
There are a few things about this code block worth discussing. Any details of the Valhalla request missing from the below can be found in the documentation. 

First, I wrapped the entire thing in a try/except block because the Valhalla requests will occasionally stall (about 1 in 500). This block simply repeats the call when that happens, and so far I have never had any request stall more than twice. 

Second, I use the `trace_route` request. This works best for long routes with many segments. There's also a `trace_attribute` request, which has its pros and cons and might be appropriate for other applications. You should review the documentation and decide which works best for your needs.

Third, the units of the `trace_options.search_radius` and `trace_options.interpolation_distance` settings is meters. 

Finally, the `trace_options.turn_penalty_factor` is very important. It penalizes route options that make too many turns. If you're dealing with a GPS trace that doesn't match the road network closely, the routing algorithm might make some random turns on to side streets to try to connect all of your input coordinates. Setting it to 500 was recommended in the Valhalla docs and I found it to work well at that setting.
