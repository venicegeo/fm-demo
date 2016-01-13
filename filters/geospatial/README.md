# US Geospatial Filter
A course geometry filter to identify data sets that lie within the boundaries of the United States.


## Boundary Geometry
The boundary data is sourced from: `https://raw.githubusercontent.com/johan/world.geo.json/master/countries/USA.geo.json`.


## Example Usage
This service accepts `GET` and `POST` requests taking an array and returns an JSON containing two arrays, one of those that "passed" the filter (i.e. lies outside the US boundaries) and the other that"failed". <br>
`http://localhost:8080/us-geospatial-filter/home?[{latitude:<number>,longitude:<number>},{latitude:<number>,longitude:<number>},...]` 
<br>
`http://localhost:8080/us-geospatial-filter/home?[<geojson>,<geojson>,...]`


## Service Standup

