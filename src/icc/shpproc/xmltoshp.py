from lxml import etree

import shapefile

def convert(xml, shp, shapeType=shapefile.POLYGON, features={}):
    tree=etree.parse(xml)
    sw=shapefile.Writer(shapeType=shapeType)
    sw.autoBalance = 1
    return True
