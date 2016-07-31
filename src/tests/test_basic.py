from nose.tools import *
import icc.shpproc as shp
from lxml import etree



import pkg_resources

def res(filename):
    return pkg_resources.resource_filename("icc.shpproc", "../../tests/data/"+filename)

OLKHON=res("Olkhon.xml")
B_OLKHON=res("Olkhon-beauty.xml")
SHP=res("Olkhon")

API_KEY="36C85854-8B2CB53B-C2FA4526-45F47111-0B87CFD5-9DEFE93F-49743DDD-2AE78978"
LAYERS=res("wikimapia_olkhon.txt")

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

class TestConvertSimple:

    def setUp(self):
        self.tree=etree.parse(OLKHON)

    def tearDown(self):
        pass

    def test_save(self):
        self.tree.write(B_OLKHON, encoding="utf8", pretty_print=True, xml_declaration=True)

    def test_convert(self):
        pass

class TestConvertToSHP:

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_covert_basic(self):
        assert shp.wikimapia(OLKHON,SHP)

    def test_convert_layers(self):
        assert shp.wikimapia(layers=LAYERS, shp=res(""), api_key=API_KEY)
