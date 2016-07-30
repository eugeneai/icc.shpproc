from nose.tools import *
import pkg_resources
from icc.shpproc import get_proj, gk_to_wgs, wgs_to_gk


def res(filename):
    return pkg_resources.resource_filename("icc.shpproc",
                                           "../../tests/data/" + filename)


OLKHON = res("Olkhon.xml")
B_OLKHON = res("Olkhon-beauty.xml")
SHP = res("Olkhon")


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
        pass

    def tearDown(self):
        pass
