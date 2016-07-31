from lxml import etree
import shapefile
from icc.shpproc.proj import GKConverter, WGS_84, get_proj
import numpy as np
import pyproj
import os.path

HTTP_Q="http://api.wikimapia.org/?key={api_key}&id={id}&function=place.getbyid"

class WikimapiaLoader(object):
    """Loads shapes from wikimapia and constructs shapes.
    """

    def __init__(self, xml=None, shp=None, layers=None, shapeType=shapefile.POLYGON, features=None, api_key=None):
        """
        """
        self.api_key=api_key
        self.shapeType=shapeType
        self.layers=layers
        self.shp=shp
        self.xml=xml
        if features != None:
            self.features=features
        else:
            self.default_features()

    def default_features(self):
        self.features=("id","title")

    def parse_xml(self, xml):
        return etree.parse(xml)

    def parse_by_id(self, id):
        if self.api_key==None:
            raise RuntimeError("api key did not set up")
        URL=HTTP_Q.format(api_key=self.api_key, id=id)
        return self.parse_xml(URL)

    def load_from_etree(self, tree, writer, **kwargs):
        # database structure must be already set up
        objid=int(tree.find("wm/id").text)
        objtitle=tree.find("wm/title").text.replace("\n"," ")
        polys=tree.iterfind("polygon")
        polyParts=[]
        for i, poly in enumerate(polys):
            fx=fy=None
            polyPart=[]
            for x,y in zip(poly.iterfind("*/x"),poly.iterfind("*/y")):
                x,y=map(float, [x.text,y.text])
                if fx==None:
                    fx=x
                    fy=y
                poly_part.append([x,y])
            polyPart.append([fx,fy])
            polyParts.append(polyPart)
        writer.record(ID=objid, TITLE=objtitle, **kwargs)

        if len(polyParts)>1:
            writer.poly(parts=polyParts, shapeType=shapefile.MULTIPOINT,
                    partTypes=[shapefile.POLYGON]*len(polyParts))
        else:
            writer.poly(parts=polyParts, shapeType=shapefile.POLYGON)

    def load(self, target=None):
        if self.layers is not None:
            if type(self.shp) is not str:
                raise ValueError("shp must be a directory name, a string")
            #if target is None:
            #    raise ValueError("target directory is not specified")
            return self.load_layers(self.layers, self.shp)

        if type(self.shp) is str:
            writer=shapefile.Writer()
            self.setup_default_fields(writer)
        else:
            writer=self.shp
        self.load_from_xml(self.xml, writer)
        if type(self.shp) is not str:
            writer.save(self.shp)
        return writer

    def load_layers(self, layers, shp):
        script=open(layers, "r")
        writer=None
        template=HTTP_Q
        layer_name=""
        for line in script:
            line=line.strip()
            if line.startswith("#"):
                if writer is not None:
                    writer.save(layer_name)
                layer_name=line[1:].strip().replace(" ","_")
                layer_name=os.path.join(shp, layer_name)
                writer=shapefile.Writer()
                self.setup_default_fields(writer)
                writer.field("NAME")
                continue
            elif line.startswith("http"):
                template=line
                continue

            objid, name=line.split(" ", maxsplit=1)

            tree=self.parse_by_id(int(objid))

            self.load_from_etree(tree, writer, NAME=name)

        if writer is not None:
            writer.save(layer_name)

    def load_from_xml(self, xml, writer):
        tree=self.parse_xml(xml)
        self.load_from_etree(tree, writer)
        return writer

    def setup_default_fields(self, writer):
        writer.field("ID", "N", "3")
        writer.field("TITLE", "C", size="100")


def wikimapia(xml=None, shp=None, layers=None, shapeType=shapefile.POLYGON, features=None, api_key=None, target=None):
    wm=WikimapiaLoader(xml=xml, shp=shp, layers=layers, shapeType=shapeType, features=features, api_key=api_key)
    return wm.load()

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
