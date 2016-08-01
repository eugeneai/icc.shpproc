from lxml import etree
import shapefile
from icc.shpproc.proj import GKConverter, WGS_84, get_proj
import numpy as np
import pyproj
import os.path
import itertools
import matplotlib.path as mplPath

HTTP_Q = "http://api.wikimapia.org/?key={api_key}&id={id}&function=place.getbyid"


class WikimapiaLoader(object):
    """Loads shapes from wikimapia and constructs shapes.
    """

    def __init__(self,
                 xml=None,
                 shp=None,
                 layers=None,
                 shapeType=shapefile.POLYGON,
                 features=None,
                 api_key=None):
        """
        """
        self.api_key = api_key
        self.shapeType = shapeType
        self.layers = layers
        self.shp = shp
        self.xml = xml
        if features != None:
            self.features = features
        else:
            self.default_features()

    def default_features(self):
        self.features = ("id", "title")

    def parse_xml(self, xml):
        return etree.parse(xml)

    def parse_by_id(self, id):
        if self.api_key == None:
            raise RuntimeError("api key did not set up")
        URL = HTTP_Q.format(api_key=self.api_key, id=id)
        return self.parse_xml(URL)

    def load_from_etree(self, tree, writer, **kwargs):
        # database structure must be already set up
        objid = int(tree.find("id").text)
        objtitle = tree.find("title").text.replace("\n", " ")
        polys = tree.iterfind("polygon")
        polyParts = []
        for i, poly in enumerate(polys):
            fx = fy = None
            polyPart = []
            for x, y in zip(poly.iterfind("*/x"), poly.iterfind("*/y")):
                x, y = map(float, [x.text, y.text])
                if fx == None:
                    fx = x
                    fy = y
                polyPart.append([x, y])
            polyPart.append([fx, fy])
            polyParts.append(polyPart)
        writer.record(ID=objid, TITLE=objtitle, **kwargs)

        if len(polyParts) > 1:
            writer.poly(
                parts=polyParts,
                shapeType=shapefile.MULTIPOINT,
                partTypes=[shapefile.POLYGON] * len(polyParts))
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
            writer = shapefile.Writer()
            self.setup_default_fields(writer)
        else:
            writer = self.shp
        self.load_from_xml(self.xml, writer)
        if type(self.shp) is not str:
            writer.save(self.shp)
        return writer

    def load_layers(self, layers, shp):
        script = open(layers, "r")
        writer = None
        template = HTTP_Q
        layer_name = ""
        for line in script:
            line = line.strip()
            if line.startswith("#"):
                if writer is not None:
                    writer.save(layer_name)
                layer_name = line[1:].strip().replace(" ", "_")
                layer_name = os.path.join(shp, layer_name)
                writer = shapefile.Writer()
                self.setup_default_fields(writer)
                writer.field("NAME")
                continue
            elif line.startswith("http"):
                template = line
                continue

            objid, name = line.split(" ", maxsplit=1)

            tree = self.parse_by_id(int(objid))

            self.load_from_etree(tree, writer, NAME=name)

        if writer is not None:
            writer.save(layer_name)

        return True

    def load_from_xml(self, xml, writer):
        tree = self.parse_xml(xml)
        self.load_from_etree(tree, writer)
        return writer

    def setup_default_fields(self, writer):
        writer.field("ID", "N", "10")
        writer.field("TITLE", "C", size="100")


def wikimapia(xml=None,
              shp=None,
              layers=None,
              shapeType=shapefile.POLYGON,
              features=None,
              api_key=None,
              target=None):
    wm = WikimapiaLoader(
        xml=xml,
        shp=shp,
        layers=layers,
        shapeType=shapeType,
        features=features,
        api_key=api_key)
    return wm.load()


class ReProjection:
    def __init__(self, in_proj=WGS_84, to_proj=None):
        if to_proj == None:
            raise ValueError("a target projection must be set")
        self.in_proj = in_proj
        self.to_proj = to_proj

    def shapes_convert(self, reader, backward=False):
        if backward:
            cfrom = self.to_proj
            cto = self.in_proj
        else:
            cfrom = self.in_proj
            cto = self.to_proj

        writer = shapefile.Writer()
        self.prepare_writer(reader, writer)
        shapes = reader.shapes()

        for feature in shapes:

            points = np.array(feature.points, dtype=float)
            new_points = np.zeros(points.shape, dtype=float)

            new_points[:, 0], new_points[:, 1] = pyproj.transform(
                cfrom, cto, x=points[:, 0], y=points[:, 1])
            pshape2 = points.shape[1]
            if pshape2 > 2:
                new_points[:, 2:
                           pshape2] = points[:, 2:
                                             pshape2]  # FIXME Can we project z-axis?

            if len(feature.parts) == 1:
                #print("::",points.shape, new_points.shape)
                #print(points[:10,:])
                #print(new_points[:3,:])
                writer.poly(
                    parts=[new_points.tolist()], shapeType=feature.shapeType)
            else:

                indexes = list(feature.parts[:]) + [len(feature.points)]
                poly_list = [new_points[a:b, :].tolist()
                             for a, b in zip(indexes[:-1], indexes[1:])]

                partTypes = []
                if feature.shapeType == shapefile.MULTIPATCH:
                    partTypes = feature.partTypes

                writer.poly(
                    parts=poly_list,
                    partTypes=partTypes,
                    shapeType=feature.shapeType)
        return writer

    def forward(self, reader):
        return self.shapes_convert(reader)

    def backward(self, reader):
        return self.shapes_convert(reader, backward=True)

    def prepare_writer(self, reader, writer):
        writer.shapeType = reader.shapeType
        writer.autoBalance = 1

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
        self.zone = zone

    def to_wgs(self, reader):
        return self.backward(reader)

    def to_gk(self, reader):
        return self.forward(reader)

def as_grad(x):
    gr=int(x)
    x-=gr
    mins=int(x*60)
    x-=mins/60.
    secs=int(x*60*60 +0.5)
    if gr!=0:
        return "{:-04d} {:02d}'{:03d}".format(gr, mins, secs)
    return "{:02d}'{:03d}".format(mins, secs)


class PointGenerator(object):
    def __init__(self,
                 source,
                 stepx=None,
                 stepy=None,
                 rond=True,
                 envelope=False,
                 target=None,
                 coords=None,   # Add coordinate data to the generated layer database in the coords projection
                 proj=None,     # Original projection (which points generated in)
                 diff=(0,0),    # This values are subtracted from coords to be shown, reducing amount of info to be printed
                 only_local_part=True,  #Show in data only local (.#####) part of the coordinate
    ):
        self.stepx = stepx
        if stepy is None:
            stepy = stepx
        self.stepy = stepy
        if target is None:
            self.writer = shapefile.Writer(shapeType=shapefile.POINT)
            self.prepare(self.writer)
        else:
            self.writer = target

        if type(source) == str:
            self.reader = shapefile.Reader(source)
        else:
            self.reader = source

        self.source = source
        self.target = target
        self.envelope = envelope
        self.script = stepx is None
        self.coords = coords
        if coords and proj is None:
            raise ValueError("original projection data needed")
        self.proj=proj
        self.diff=diff

    def generate(self):
        if self.script:
            return self.gen_for_script()
        grid = set()
        for feature in self.reader.shapes():
            self.gen_for_feature(feature, grid)
        return self.save(grid)

    def save(self, grid):
        grid=list(grid)
        grid.sort()
        NSMAP={
            None:"http://www.topografix.com/GPX/1/1",
        }
        gpx=etree.Element("gpx", nsmap=NSMAP)
        tree=etree.ElementTree(element=gpx)
        gpx.set("creator","https://github.com/eugeneai/icc.shpproc/blob/master/src/icc/shpproc/xmltoshp.py#PointGenerator")
        gpx.set("{http://www.w3.org/2001/XMLSchema-instance}schemaLocation", "http://www.topografix.com/GPX/1/1 \
        http://www.topografix.com/GPX/1/1/gpx.xsd \
        http://www.garmin.com/xmlschemas/GpxExtensions/v3 \
        http://www8.garmin.com/xmlschemas/GpxExtensionsv3.xsd \
        http://www.garmin.com/xmlschemas/WaypointExtension/v1 \
        http://www8.garmin.com/xmlschemas/WaypointExtensionv1.xsd \
        http://www.garmin.com/xmlschemas/TrackPointExtension/v1 \
        http://www.garmin.com/xmlschemas/TrackPointExtensionv1.xsd")
        md=etree.SubElement(gpx,"metadata")
        l=etree.SubElement(md,"link", href="http://www.garmin.com")
        text=etree.SubElement(l,"text")
        text.text="Garmin International"
        etree.SubElement(md,"time").text="2016-08-01T01:22:18Z"
        def save_point(x,y,name, ele=None, sym=None, gpx=gpx, time=None):
            wpt=etree.SubElement(gpx, "wpt", lat="{:-9.6f}".format(y), lon="{:-10.6f}".format(x))
            if ele:
                etree.SubElement(wpt,"ele").text=str(ele)
            if time:
                etree.SubElement(wpt,"time").text=time
            etree.SubElement(wpt,"name").text=name
            esym=etree.SubElement(wpt,"sym").text="Flag, Blue"
            if sym:
                esym.text=sym
        self.gpx=tree

        serial=301
        if grid:
            if type(self.target) == str:
                writer = shapefile.Writer(shapeType=shapefile.POINT)
                self.prepare(writer)
            else:
                writer = self.writer
            for i, p in enumerate(grid):
                x, y = p
                writer.point(x=x, y=y)
                LONGLAT=""
                LOCAL=""
                if self.coords:
                    px,py=pyproj.transform(self.proj,self.coords, x=x, y=y)
                    # LONGLAT="{}-{}".format(as_grad(px-self.diff[0]), as_grad(py-self.diff[1]))
                    LONGLAT="{:05.0f}-{:05.0f}".format((py-self.diff[0])*100000, (px-self.diff[1])*100000)
                    dpy=py-int(py)
                    dpx=px-int(px)
                    LOCAL="{:05.0f}-{:05.0f}".format(dpy*100000, dpx*100000)
                    lat=py
                    long=px
                    save_point(x=px, y=py, name="z{:03d}".format(serial), ele=455, time="2016-08-01T01:22:18Z")
                    serial+=1
                writer.record(
                    ID=i,
                    ID_SHAPE=-1,
                    LONGLAT=LONGLAT,
                    LOCAL=LOCAL,
                    COORD="{}, {}".format(x, y))
            writer.save(self.target)
        else:
            print("WARNING: no points generated")
        return grid

    def gen_for_script(self):
        grid = set()
        fields = self.reader.fields

        fld = {}
        for i, f in enumerate(fields):
            fld[f[0]] = i - 1

        reader = self.reader

        ID = fld["id"]
        E = fld["envelope"]
        D = fld["density"]
        for inst in reader.iterShapeRecords():
            feature = inst.shape
            rec = inst.record
            envelope = rec[E]
            density = eval(str(rec[D]))

            if density <= 0: continue
            if type(density) == tuple:
                if 0 in density: continue
                if 0.0 in density: continue

            self.gen_for_feature(
                feature, grid, density=density, envelope=envelope)

        self.save(grid)
        return grid

    def gen_for_feature(self, feature, grid, density=None, envelope=None):
        if feature.shapeType not in [3, 5, 13, 15, 23, 25, 28, 31]:
            raise ValueError("feature is not polyline neither polygon")
        points = np.array(feature.points)
        if feature.parts == 1:
            self.gen_for_points(
                points, grid, density=density, envelope=envelope)
        else:
            index = feature.parts[:]
            index.append(len(feature.points))
            for a, b in zip(index[:-1], index[1:]):
                self.gen_for_points(
                    points[a:b], grid, density=density, envelope=envelope)

    def gen_for_points(self, points, grid, density=None, envelope=None):
        def rnd(v, g, app=0):
            """Rounds to a mesh.
            If app is 0 then the left point of the mesh is taken.
            If app is 1 the right point taken.
            If app is 0.5 then nearest is taken.
            """
            vv = int(v)
            gv = int(v / g) * g
            if vv == gv:
                return gv
            else:
                if app == 0:
                    return gv
                if app == 1:
                    return gv + g
                gv = int(v / grid + app) * g

        if density is not None:
            if type(density) == tuple:
                sx, sy = density
            else:
                sx = sy = density
        else:
            sx, sy = self.stepx, self.stepy

        assert sx > 0 and sy > 0
        assert sx > 100 and sy > 100
        if envelope is None:
            envelope = self.envelope

        mi = np.amin(points, 0)
        ma = np.amax(points, 0)
        mi[0], mi[1] = rnd(mi[0], sx), rnd(mi[1], sy)
        ma[0], ma[1] = rnd(ma[0], sx, app=1), rnd(ma[1], sy, app=1)
        ma = ma.astype(int)
        mi = mi.astype(int)
        poly = mplPath.Path(points)
        for x, y in itertools.product(
                range(mi[0], ma[0], sx), range(mi[1], ma[1], sy)):
            if poly.contains_point((x, y)):
                grid.add((x, y))
        if envelope:
            sx2, sy2 = int(sx / 2), int(sy / 2)
            mi -= [sx2, sy2]
            ma += [sx2, sy2]
            for x, y in itertools.product(
                    range(mi[0], ma[0], sx), range(mi[1], ma[1], sy)):
                if poly.contains_point((x, y)):
                    grid.add((x, y))

    def prepare(self, writer):
        writer.field("ID", "N", size=5)
        writer.field("ID_SHAPE", "N", size=5)
        writer.field("LONGLAT", size=50)
        writer.field("LOCAL", size=50)
        writer.field("COORD", size=50)
