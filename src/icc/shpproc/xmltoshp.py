from lxml import etree
import shapefile
from icc.shpproc.proj import GKConverter, WGS_84, get_proj
import numpy as np
import pyproj

def convert(xml, shp, shapeType=shapefile.POLYGON, features={}):
    tree=etree.parse(xml)
    sw=shapefile.Writer(shapeType=shapeType)
    sw.autoBalance = 1
    return True

class ReProjection:
    def __init__(self, in_proj=WGS_84, to_proj=None):
        if to_proj==None:
            raise ValueError("a target projection must be set")
        self.in_proj=in_proj
        self.to_proj=to_proj

    def shapes_convert(self, reader, backward=False):
        if backward:
            cfrom=self.to_proj
            cto=self.in_proj
        else:
            cfrom=self.in_proj
            cto=self.to_proj

        writer=shapefile.Writer()
        self.prepare_writer(reader,writer)
        shapes=reader.shapes()

        for feature in shapes:

            points=np.array(feature.points, dtype=float)
            new_points=np.zeros(points.shape, dtype=float)

            new_points[:,0],new_points[:,1]=pyproj.transform(cfrom, cto, x=points[:,0], y=points[:,1])
            pshape2=points.shape[1]
            if pshape2>2:
                new_points[:,2:pshape2]=points[:,2:pshape2] # FIXME Can we project z-axis?

            if len(feature.parts) == 1:
                #print("::",points.shape, new_points.shape)
                #print(points[:10,:])
                #print(new_points[:3,:])
                writer.poly(parts=[new_points.tolist()], shapeType=feature.shapeType)
            else:

                indexes = list(feature.parts[:])+[len(feature.points)]
                poly_list=[new_points[a:b,:].tolist() for a,b in zip(indexes[:-1], indexes[1:])]

                partTypes=[]
                if feature.shapeType==shapefile.MULTIPATCH:
                    partTypes=feature.partTypes

                writer.poly(parts=poly_list, partTypes=partTypes, shapeType=feature.shapeType)
        return writer

    def forward(self, reader):
        return self.shapes_convert(reader)

    def backward(self, reader):
        return self.shapes_convert(reader, backward=True)

    def prepare_writer(self, reader, writer):
        writer.shapeType=reader.shapeType
        writer.autoBalance=1

        fields = reader.fields
        wgs_fields = writer.fields
        for name in fields:
            if type(name) == tuple:
                continue
            else:
                args = name
                writer.field(*args)

        records = reader.records()
        for row in records:
            args = row
            writer.record(*args)

class GKProjection(ReProjection):
    def __init__(self, zone=18):
        ReProjection.__init__(self, WGS_84, get_proj(zone=zone))
        self.zone=zone

    def to_wgs(self, reader):
        return self.backward(reader)

    def to_gk(self, reader):
        return self.forward(reader)
