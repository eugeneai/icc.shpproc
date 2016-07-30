# import icc.shpproc as shp
from pyproj import Proj, transform

WGS_84 = Proj(init="epsg:3857")
GK_18 = Proj(init="epsg:2534")

GK_CACHE = {18: GK_18, "18": GK_18}


def get_proj(zone):
    if zone in GK_CACHE:
        return GK_CACHE[zone]

    zone = int(zone)
    s = None
    if zone >= 3 and zone <= 5:
        s = 2397 + zone - 3
    elif zone >= 7 and zone <= 33:
        s = 2523 + zone - 7
    elif zone >= 34 and zone <= 64:
        s = 2551 + zone - 34

    if s == None:
        raise ValueError("unknown Pulkovo 1942 Gauss-Kruger zone.")
    p = Proj(init="epsg:{:4d}".format(s))
    GK_CACHE[zone] = p
    GK_CACHE[str(zone)] = p
    return p


def gk_to_wgs(x, y, z=None, zone=18):
    gk = get_proj(zone=zone)
    return transform(gk, WGS_84, x=x, y=x, z=z)


def wgs_to_gk(x, y, z=None, zone=18):
    gk = get_proj(zone=zone)
    return transform(WGS_84, gk, x=x, y=x, z=z)


class GKConverter(object):
    def __init__(self, zone=18):
        self.gk = get_proj(zone=zone)

    def from_gk(self, x, y, z=None):
        return transform(self.gk, WGS_84, x=x, y=x, z=z)

    def to_gk(self, x, y, z=None):
        return transform(WGS_84, self.gk, x=x, y=x, z=z)
