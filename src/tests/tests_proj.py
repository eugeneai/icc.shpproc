from nose.tools import *
import pkg_resources
from icc.shpproc import get_proj, gk_to_wgs, wgs_to_gk
from icc.shpproc import GKProjection, wikimapia, ReProjection
import shapefile, os
from icc.shpproc.proj import WGS_84, WGS_84_S, GK_18
from pyproj import Proj

def res(filename):
    return pkg_resources.resource_filename("icc.shpproc",
                                           "../../tests/data/" + filename)

OLKHON = res("Olkhon.xml")
B_OLKHON = res("Olkhon-beauty.xml")

SHP = res("Olkhon")
SHP_OUT = res("Olkhon-transformed")
SHP_OUT_S = res("Olkhon-transformed-spheric")
SHP_GRID =res("OlkhonGrid1km")
SHP_GRID_OUT =res("OlkhonGrid1km-WGS")
IRELAND = res("Ireland_LA_wgs.prj")
IRELAND_SHP = res("Census2011_Admin_Counties_generalised20m")
IRELAND_SHP_OUT=res("Census2011_Admin_Counties_generalised20m_wgs")
IRELAND_PROJ=Proj(init="epsg:29902")
AREALS=res("Areals")

def getWKT_PRJ (epsg_code):
    from urllib.request import urlopen

    with urlopen("http://spatialreference.org/ref/epsg/{}/ogcwkt/".format(epsg_code)) as wkt:

        remove_spaces = wkt.read().replace(b" ",b"")
        output = remove_spaces.replace(b"\n", b"")
        return output

def get_Ireland():
    epsg = getWKT_PRJ("4326")
    if epsg:
        prj = open(IRELAND, "wb")
        prj.write(epsg)
        prj.close()
    else:
        raise RuntimeError("could not load Ireland map")

try:
    os.stat(IRELAND)
except FileNotFoundError:
    get_Ireland()

class TestBasic:
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_self(self):
        assert True

    def test_get_proj_cached(self):
        assert get_proj(18) != None

    def test_get_proj_ok(self):
        assert get_proj(19) != None

    @raises(ValueError)
    def test_get_proj_non_exists(self):
        assert get_proj(0) != None


class TestConvertSimple:
    def setUp(self):
        #self.tree = etree.parse(OLKHON)
        self.proj=GKProjection(zone=18)
        pass

    def tearDown(self):
        pass

    def test_covert_basic(self):
        assert wikimapia(OLKHON,SHP)

    def test_project_wgs_to_gk(self):
        r=shapefile.Reader(SHP_GRID)
        w=self.proj.to_wgs(r)
        w.save(SHP_GRID_OUT)

class TestWithIrelandData:
    def setUp(self):
        self.proj=ReProjection(IRELAND_PROJ, WGS_84)
        pass

    def tearDown(self):
        pass

    def test_project_ITM_WGS(self):
        r=shapefile.Reader(IRELAND_SHP)
        w=self.proj.forward(r)
        w.save(IRELAND_SHP_OUT)


class TestWithOlkhonData1:
    def setUp(self):
        self.proj=ReProjection(WGS_84_S, GK_18)
        pass

    def tearDown(self):
        pass

    def test_reproject_sheric_to_pulkovo_olkhon(self):
        r=shapefile.Reader(SHP)
        w=self.proj.forward(r)
        w.save(SHP+"-GK18")

    def test_area_to_pulkovo(self):
        r=shapefile.Reader(AREALS)
        w=self.proj.forward(r)
        w.save(AREALS+"-GK18")


if __name__=="__main__":
    t=TestConvertSimple()
    t.setUp()
    t.test_covert_basic()
    t.tearDown()
