from reportlab.graphics.barcode import code39, code128, code93
from reportlab.graphics.barcode import eanbc, qr, usps
from reportlab.graphics.shapes import Drawing
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF
from random import choice, randrange

PLACE="BAU"
MEDIA="G"
PROBE="WSP"

dx=50
dy=20
x0=4
y0=3
mx=mm
my=(1+(259.5-255.25)/259.5)*mm
sx=50
sy=20


def probegen(numlen=4):
    C=choice
    c=C(PLACE)+C(MEDIA)+C(PROBE)+"-{}".format(randrange(10000))
    return c

def label(d,c,x,y):
    xx=x*sx*mx
    yy=y*sy*my
    bx=(x0+0)*mx
    by=(y0+0)*my
    xx0=x0*my
    yy0=y0*my
    renderPDF.draw(d, c, xx+bx, yy+by)   # Ajustenment is -1mm, -3mm
    c.roundRect(xx0+xx, yy0+yy, 20*mx, 20*my, 1*mx, stroke=1, fill=0)
    c.roundRect(xx0+xx, yy0+yy, 48*mx, 20*my, 1*mx, stroke=1, fill=0)

#----------------------------------------------------------------------
def createBarCodes():
    """
    Create barcode examples and embed in a PDF
    """
    c = canvas.Canvas("barcodes.pdf", pagesize=A4)

    barcode_value = probegen()


    # draw a QR code
    qr_code = qr.QrCodeWidget(barcode_value)
    bounds = qr_code.getBounds()
    print (bounds)
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    sc=57 #45
    d = Drawing(sc, sc, transform=[sc/width,0,0,sc/height,0,0])
    d.add(qr_code)

    for x in range(4):
        label(d,c, x,0)
        label(d,c, x,13)
    for y in range(13):
        label(d,c, 0,y)
        label(d,c, 3,y)


    c.save()

if __name__ == "__main__":
    createBarCodes()
