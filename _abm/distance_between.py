import configparser
import os
import sys
from math import radians, cos, sin, asin, sqrt
from shapely.geometry import Point
import shapely
import random
import geopandas as gpd

config = configparser.ConfigParser()
# change the root directory to where CONFIG is kept
os.chdir(os.path.dirname(sys.path[0]))
config.read(r'CONFIG.txt')
# read iris shapefile, transform to WGS84 and get the bounding box of each iris
# for irises
bas_rhin_iris = config['Shapefile']['bas_rhin_iris']
gdf_iris = gpd.read_file(bas_rhin_iris)
gdf_iris = gdf_iris.to_crs(epsg=4326)
gdf_iris['centroid'] = gdf_iris['geometry'].centroid
# for zones
bas_rhin_zone = config['Shapefile']['bas_rhin_zone']
gdf_zone = gpd.read_file(bas_rhin_zone)
gdf_zone = gdf_zone.to_crs(epsg = 4326)
gdf_zone['centroid'] = gdf_zone['geometry'].centroid

def _get_euclidean_distance_iris(iris_1: str, iris_2: str):
    """
    this function uses the haversine method to calculate the centroid euclidean distance between any two contour irises.
    @param iris_1: the origin contour iris
    @param iris_2: the destination contour iris
    @return: returns the distance based on haversine method
    """

    ci = gdf_iris[gdf_iris['DCOMIRIS'] == iris_1]['centroid']
    cj = gdf_iris[gdf_iris['DCOMIRIS'] == iris_2]['centroid']
    if ci.empty == True or cj.empty == True:
        # if the iris is not in the shapefile
        return 9999
    else:
        return round(haversine(ci.x, ci.y, cj.x, cj.y), 2)

def _get_euclidean_distance_zone(zone_1: str, zone_2: str):
    """
    this function uses the haversine method to calculate the centroid euclidean distance between any two EMD zones.
    @param zone_1: the origin EMD zone
    @param zone_2: the destination EMD zone
    @return: returns the distance based on haversine method
    """
    ci = gdf_zone[gdf_zone['code_sec_1'] == zone_1[1:]]['centroid']
    cj = gdf_zone[gdf_zone['code_sec_1'] == zone_2[1:]]['centroid']
    if ci.empty == True or cj.empty == True:
        # if the iris is not in the shapefile
        return 9999
    else:
        return round(haversine(ci.x, ci.y, cj.x, cj.y), 2)

def _get_distance_random_points(zone_1: str, zone_2: str):
    """
    this function uses the haversine method to calculate the distance between random point in any two EMD zones.
    @param zone_1: the origin EMD zone
    @param zone_2: the destination EMD zone
    @return: returns the distance based on haversine method
    """
    if zone_1[1:] not in gdf_zone['code_sec_1'].unique() or zone_2[1:] not in gdf_zone['code_sec_1'].unique():
        return 9999
    def random_points_in_polygon(number: int, polygon: shapely.geometry.Polygon):
        """
        this function generates a random point in a polygon and returns it
        @param number: number of points required
        @param polygon: the feature in a shapefile
        @return: random point
        """
        points = []
        min_x, min_y, max_x, max_y = polygon.bounds
        i = 0
        while i < number:
            point = Point(random.uniform(min_x, max_x), random.uniform(min_y, max_y))
            if polygon.contains(point):
                points.append(point)
                i += 1
        return points
    ri = random_points_in_polygon(1, gdf_zone[gdf_zone['code_sec_1'] == zone_1[1:]]['geometry'].values[0])
    rj = random_points_in_polygon(1, gdf_zone[gdf_zone['code_sec_1'] == zone_2[1:]]['geometry'].values[0])
    if ri[0].empty == True or rj[0].empty == True:
        # if the iris is not in the shapefile
        return 9999
    else:
        return round(haversine(ri[0].x, ri[0].y, rj[0].x, rj[0].y), 2)



# from internet (to get the distance in km taking earth's spherical shape into consideration)
def haversine(x1: float, y1: float, x2: float, y2: float):
    """
    Calculates the great circle distance between two points
    on the earth (specified in decimal degrees)
    @param x1: the x coordinate of the first point
    @param y1: the y coordinate of the first point
    @param x2: the x coordinate of the second point
    @param y2: the y coordinate of the second point
    """
    # convert decimal degrees to radians
    x1, y1, x2, y2 = map(radians, [x1, y1, x2, y2])
    # haversine formula
    dx = x2 - x1
    dy = y2 - y1

    a = sin(dy/2) ** 2 + cos(y1) * cos(y2) * sin(dx / 2) ** 2
    c = 2 * asin(sqrt(a))
    # Radius of earth in kilometers. Use 3956 for miles
    r = 6371

    return c * r