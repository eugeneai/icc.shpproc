from nose.tools import *
import icc.shpproc as shp

import pkg_resources

def res(filename):
    return pkg_resources.resource_filename("icc.shpproc", "../../tests/data/"+filename)

OLKHON=res("Olkhon.xml")

class TestBasic:
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_self(self):
        assert True

    def test_resource(self):
        i=open(OLKHON)
        l=i.readline()
        print(l)
        i.close()
        assert l.startswith('<?xml version="1.0" encoding="UTF-8"?>')
