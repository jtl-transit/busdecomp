# Spatial Decomposition of Bus Transit Networks (`busdecomp`)

This is the main repository for the bus transit decomposition method described
in a recent submission to Environment and Planning B. 

It takes as an input the filepath for a standard GTFS feed, and returns
a geoJSON file containing the edge-level representation of the bus transit
network, including the route ID and stop ID pair for each route traversing
the edge. 

Two public transit analysis use cases are included in this repository and described in detail below. 
Jupyter notebooks and sample data are provided in the [Examples](examples) for new users to recreate these examples. 

Note that this program requires the Valhalla map matching engine to be
configured for the appropriate region and running locally. Instructions
for installing and configuring Valhalla are included in a [readme file](valhalla_readme.md). 

This program was written for Python 3.9, and required packages are available in [requirements.txt](requirements.txt).

## Installation Instructions

There are three main steps to setting up `busdecomp` for local use.
1. Clone this repository to the desired machine.
2. Install the required software packages and Python libraries. 
3. Install and configure Valhalla. 

### 1. Clone the repository.

Instructions on how to clone a repository from GitHub are available [here.](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository)

### 2. Install the requirements

These instructions assume you have already installed Anaconda. An Anaconda distribution can be downloaded [here.]( https://www.anaconda.com/products/distribution)

Open the Anaconda Prompt command line interface. Install a virtual environment using Anaconda and activate it (replace @ENV_NAME with the name of your virtual environment):

```
conda create --name @ENV_NAME python=3.9
conda activate @ENV_NAME
```

For example:

```
conda create --name busdecomp python=3.9
conda activate rove
```

Import dependencies via requirements.txt (replace @DIRECTORY with the location of your cloned repo from step 1):

```
cd @DIRECTORY
pip install -r requirements.txt
```

### 3. Install and configure Valhalla. 

Valhalla is a separate program for running the map matching component of `busdecomp`. Instructions for installing and configuring Valhalla are included in a [readme file](valhalla_readme.md). 
