from lxml import etree
import shapefile
from icc.shpproc.proj import GKConverter, WGS_84
import numpy as np
import pyproj

def convert(xml, shp, shapeType=shapefile.POLYGON, features={}):
    tree=etree.parse(xml)
    sw=shapefile.Writer(shapeType=shapeType)
    sw.autoBalance = 1
    return True

class GKProjection(GKConverter):
    def shapes_convert(self, reader, writer, cfrom, cto):
        self.prepare_writer(reader,writer)
        shapes=reader.shapes()

        for feature in shapes:

            points=np.array(feature.points, dtype=float)
            new_points=np.zeros(points.shape, dtype=float)

            new_points[:,0],new_points[:,1]=pyproj.transform(cfrom, cto, x=points[:,0], y=points[:,1])
            new_points[:,2:4]=points[:,2:4] # FIXME Can we project z-axis?

            if len(feature.parts) == 1:
                writer.poly(parts=[new_points], shapeType=feature.shapeType)
            else:

                indexes = feture.parts[:]+[len(feature.points)]
                poly_list=[new_points[a:b,:] for a,b in zip(indexes[1:], indexes[:-1])]

                partTypes=[]
                if feature.shapeType==shapefile.MULTIPATCH:
                    partTypes=feature.partTypes

                writer.poly(parts=poly_list, partTypes=partTypes, shapeType=feature.shapeType)


    def shapes_to_gk(self, reader, writer):
        return self.shapes_convert(reader, writer, cfrom=WGS_84, cto=self.gk)

    def shapes_to_wgs(self, reader, writer):
        return self.shapes_convert(reader, writer, cfrom=self.gk, cto=WGS_84)

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
