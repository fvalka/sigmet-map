# Plot SIGMETs, AIRMETs and METARs on a map
This program retrieves the US SIGMETS, US CWAs, international SIGMETS and  METARs from the 
aviationweather.gov GeoJSON web services and plots a map containing  the SIGMETs, AIRMETs and 
METARs fligth category received.  

<p align="center" style="padding: 6em;">
    <img src="tests/reference/na.png">
</p>

## Features
The map contains many features. A base map of 10m resolution containing countries, lakes, land 
and oceans. On top of this all METARs available for the region are plotted, colour coded for 
their current flight categories. 

SIGMETs are added on top of this. Both polygon based and point based SIGMETs are supported. 
All SIGMETs which could not be correctly parsed by the aviationweather.gov webservice are shown
in a lighter tone with a different border. 

## Architecture
Cartopy is used for plotting the base map and for projecting the map data onto a matplotlib plot. 
This is served up by a tiny Flask webservice. Images are not included in the result of the web service
call but stored in Flasks static folder. 

These images are automatically deleted by a clean up process which runs every two hours. 

