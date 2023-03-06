# Spatial Decomposition of Bus Transit Networks (`busdecomp`)

This is the main repository for the bus transit decomposition method described
in a recent submission to Environment and Planning B. 

It takes as an input the filepath for a standard GTFS feed, and returns
a geoJSON file containing the edge-level representation of the bus transit
network, including the route ID and stop ID pair for each route traversing
the edge. 

Two public transit analysis use cases are included in this repository and described in detail below. 
Jupyter notebooks and sample data are provided in the [examples](examples) folder for new users to recreate these examples. 

Note that this program requires the Valhalla map matching engine to be
configured for the appropriate region and running locally. Instructions
for installing and configuring Valhalla are included in a [readme file](valhalla_readme.md). 

This program was written for Python 3.7, and required packages are available in [requirements.txt](requirements.txt).

## Installation Instructions

There are three main steps to setting up `busdecomp` for local use.
1. Clone this repository to the desired machine.
2. Install the required software packages and Python libraries. 
3. Install and configure Valhalla. 

#### 1. Clone the repository.

Instructions on how to clone a repository from GitHub are available [here.](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)

#### 2. Install the requirements

These instructions assume you have already installed Anaconda. An Anaconda distribution can be downloaded [here.]( https://www.anaconda.com/products/distribution)

Open the Anaconda Prompt command line interface. Install a virtual environment using Anaconda and activate it (replace @ENV_NAME with the name of your virtual environment):

```
conda create --name @ENV_NAME python=3.7
conda activate @ENV_NAME
```

For example:

```
conda create --name busdecomp python=3.7
conda activate busdecomp
```

Import dependencies via requirements.txt (replace @DIRECTORY with the location of your cloned repo from step 1):

```
cd @DIRECTORY
pip install -r requirements.txt
```

#### 3. Install and configure Valhalla. 

Valhalla is a separate program for running the map matching component of `busdecomp`. Instructions for installing and configuring Valhalla are included in a [readme file](valhalla_readme.md). 

## Using `busdecomp`

To run a new `busdecomp` analysis, first collect the compliant GTFS feeds that will be used for the baseline and the comparison scenarios. 
One possible source for GTFS feeds from transit agencies around the world is [The Mobility Database](https://database.mobilitydata.org/). 
Save both GTFS feeds (as .zip files) in the [/data](data) folder of the directory that you chose for the `busdecomp` local clone. 

Next, ensure that Valhalla is running on a local port. If it is configured to run on a port other than the default `localhost:8002`, check which port it is running on.

Finally, run `busdecomp` using the Anaconda prompt. It takes two positional arguments and one optional keyword argument. The positional arguments `baseline_filename` and `comparison_filename` are the names of the GTFS .zip files to be used for the baseline and comparison scenarios, respectively.
The keyword argument `port=8002` will allow the user to change the Valhalla port if set to something other than the default `localhost:8002`. 

``` 
from main import busdecomp
busdecomp_gtfs(base_filename, comparison_filename, road_filename, port=8002)
```

Once the program has finished running, the output .geoJSON file will be saved to the [/output](output) folder with an output filename that is a concatenation of the two input filenames. 

## Use Cases

These use cases demonstrate the utility of `busdecomp` for analyzing changes in bus transit service over long periods of time or between cities with nothing but a pair of GTFS feeds. 
Note that neither example includes analysis of a full bus network due to GitHub file size constraints. 
Extended, full-scale versions of these examples and discussion of the results are available in the Supplemental Materials section of the paper. 

#### Example 1: MBTA Network and Ridership Evolution

This case study demonstrates how block-based representation, rather than identifier-based or aggregate geographic representation, enables a simple yet thorough comparison of transit service between two distant time periods. The type of comparison highlighted in this case study could be used by transit planners or advocacy groups to identify spatial disparities in transit service changes.

Publicly available GTFS feeds from January 2011 and January 2021 are used to visualize service changes over the course of a decade, even under changing route and stop identifiers. 
The notebook code and data for running a reduced version of this example can be found in the [examples](examples) folder. 
The output can easily be visualized as shown in the figure below by loading the output file into a GIS program (such as QGIS) and adding a basemap layer.

![service_changes](https://user-images.githubusercontent.com/56656229/221449671-65b9317e-ef2f-4b48-b019-3d77fab0ab8e.PNG)

This figure hows how service has evolved by highlighting segments that were served in 2011 but no longer served in 2021, regardless of route ID. This includes elimination of several routes in the northwestern part of the region, as well as consolidation of routes along fewer corridors near downtown Boston. The decomposition method identifies several service changes without any a priori knowledge on the part of the analyst, such as the elimination of bus service on Long Island in Boston Harbor after the Long Island Bridge was demolished in 2014. Other changes can also be observed, such as the discontinuation of Route 90 service to Wellington Station and the addition of Route 714.

#### Case Study 2: Visual Comparison of COVID-19 Policies

The second case study demonstrates how `busdecomp` enables a straightforward visual policy comparison, in this case the approach to transit service provision during the COVID-19 pandemic. 
It also shows how to add schedule-based performance data to the analysis using additional `busdecomp` functions. 
The case study also emphasizes the generalizability of `busdecomp` to a range of geographic contexts. 

For this analysis, publicly available GTFS feeds from October 2019 and October 2020 were collected for a group of eight geographically diverse and large transit agencies in the U.S.: the MBTA, the Chicago Transit Authority (CTA), Los Angeles Metro (LA Metro), King County Metro in Seattle, the Metropolitan Atlanta Rapid Transit Authority (MARTA), the Washington Metro Area Transit Authority (WMATA) in Washington DC, Miami-Dade Transit and Houston Metro. October 2020 was chosen as a representative month for pandemic service patterns as it was sufficiently removed from the onset of the pandemic to allow agencies to plan service adjustments, but well before vaccines became available and transit ridership began to rebound.

The notebook code and data for running a smaller version of this example for LA Metro can be found in the [examples](examples) folder. 
The figures below show the stark differences in approaches to service delivery during COVID-19 across agencies by visualizing the number of scheduled weekday trips for each edge in October 2019 and October 2020.

**CTA**: 
![cta](https://user-images.githubusercontent.com/56656229/221449729-a2bfca83-2da6-4db4-b429-3cdbcd887e6c.PNG)

**Houston**: 
![houston](https://user-images.githubusercontent.com/56656229/221449740-e6287088-7648-467d-a767-cbf01f19b767.PNG)

**King County Metro**:
![kcmetro](https://user-images.githubusercontent.com/56656229/221449773-627cb8a2-117c-4dbb-a8ef-0b04a214aafc.PNG)
