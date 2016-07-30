from nose.tools import *
import pkg_resources
from icc.shpproc import get_proj, gk_to_wgs, wgs_to_gk
from icc.shpproc import GKProjection, convert
import shapefile


def res(filename):
    return pkg_resources.resource_filename("icc.shpproc",
                                           "../../tests/data/" + filename)


OLKHON = res("Olkhon.xml")
B_OLKHON = res("Olkhon-beauty.xml")
SHP = res("Olkhon")
SHP_OUT = res("Olkhon-transformed")
SHP_GRID =res("OlkhonGrid1km")
SHP_GRID_OUT =res("OlkhonGrid1km-WGS")

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

        assert convert(OLKHON,SHP)


    def test_project_wgs_to_gk(self):
        r=shapefile.Reader(SHP_GRID)
        w=shapefile.Writer(SHP_GRID_OUT)

        self.proj.shapes_to_wgs(r,w)

if __name__=="__main__":
    t=TestConvertSimple()
    t.setUp()
    t.test_covert_basic()
    t.tearDown()
