from math import pi, sqrt, sin, cos, atan2, radians
from dataclasses import dataclass

@dataclass
class Point:
    lat: float
    lon: float

def haversine(pos1: Point, pos2: Point) -> float:
    ''' Return distance between two pairs of coordinates. '''
    
    R = 6367 # Mean radius of earth in km
    lat1 = pos1.lat
    lon1 = pos1.lon
    lat2 = pos2.lat
    lon2 = pos2.lon

    dist_lat = radians(lat2-lat1)
    dist_lon = radians(lon2-lon1)

    a = pow(sin(dist_lat / 2), 2) + cos(radians(lat1)) * cos(radians(lat2)) * pow(sin(dist_lon / 2), 2)
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c
