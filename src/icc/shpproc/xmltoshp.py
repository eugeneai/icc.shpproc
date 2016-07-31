from lxml import etree

import shapefile

def convert(xml, shp, shapeType=shapefile.POLYGON, features={}):
    tree=etree.parse(xml)
    sw=shapefile.Writer(shapeType=shapeType)
    sw.autoBalance = 1
    sw.field("ID", "N", "3")
    polys=tree.iterfind("polygon")
    ll=[]
    for i, poly in enumerate(polys):
        fx=fy=None
        l=[]
        for x,y in zip(poly.iterfind("*/x"),poly.iterfind("*/y")):
            x,y=map(float, [x.text,y.text])
            if fx==None:
                fx=x
                fy=y
            l.append([x,y])
        l.append([fx,fy])
        sw.record(ID=i)
        ll.append(l)

    sw.poly(parts=ll, shapeType=3)
    sw.save(target=shp)
    return fx!=None
