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
x0=6
y0=6
mx=mm
my=(1+(259.5-255.25)/259.5)*mm
sx=50
sy=20


def label(code,c,x,y):
    xx=x*sx*mx
    yy=y*sy*my
    bx=(x0+0)*mx
    by=(y0+0)*my
    xx0=x0*my
    yy0=y0*my

    # draw a QR code
    qr_code = qr.QrCodeWidget(code)
    bounds = qr_code.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    sc=57 #45
    d = Drawing(sc, sc, transform=[sc/width,0,0,sc/height,0,0])
    d.add(qr_code)

    renderPDF.draw(d, c, xx+bx, yy+by)   # Ajustenment is -1mm, -3mm
    #c.roundRect(xx0+xx, yy0+yy, 20*mx, 20*my, 1*mx, stroke=1, fill=0)
    c.roundRect(xx0+xx, yy0+yy, 49*mx, 20*my, 1*mx, stroke=1, fill=0)
    textobject = c.beginText()
    dx=xx0+20*mx
    dy=yy0+13*my
    textobject.setTextOrigin(dx+xx,dy+yy)
    textobject.setFont("Helvetica-Bold", 14)
    textobject.textLine(code)
    c.drawText(textobject)

    bs=5
    size=5
    def field(x,y, size=size, bs=bs):
        for b in range(size):
            yield x+b*bs*mx,y, bs*mx, bs*my

    fx=fy=None
    for x,y,w,h in field(xx0+xx+20*mx, yy0+yy+2*my):
        if fy is None:
            fx,fy=x,y
        c.roundRect(x,y,w,h,1*mx, stroke=1, fill=0)
        c.roundRect(x,y+5*my,w,h,1*mx, stroke=1, fill=0)
    c.setFillColorRGB(1.,1.,1.)
    c.roundRect(fx+mx,fy+my, bs*(size)*mx-2*mx, 2*bs*my/2-2*my, stroke=0, fill=1, radius=1*mx)
    c.roundRect(fx+mx,fy+my+bs*my, bs*(size)*mx-2*mx, 2*bs*my/2-2*my, stroke=0, fill=1, radius=1*mx)
    c.setFillColorRGB(0,0,0)

def probegen(numlen=4):
    C=choice
    num=400
    for p,count in zip(PLACE,[78,130,130]):  # zip(PLACE,[70,110,110]):
        while count>0:
            for m in MEDIA:
                for r in PROBE:
                    for N in range(2): # 130 khuzir 130 haran 80
                        c=p+m+r+"-{:0{}d}".format(num,numlen)
                        yield c
            count-=1
            num+=1

#----------------------------------------------------------------------
def createBarCodes():
    """
    Create barcode examples and embed in a PDF
    """
    c = canvas.Canvas("barcodes.pdf", pagesize=A4)

    barcode_value = probegen()

    pg=probegen()
    stop=False
    scount=0
    tot=0
    page=0
    while 1:
        for _ in range(14):
            y=13-_
            for x in range(4):
                try:
                    d=next(pg)
                except StopIteration:
                    stop=True
                    break
                label(d,c, x,y)
                scount+=1
                tot+=1
                if scount==14*4:
                    scount=0
            if stop:
                break
        if stop:
            break
        page+=1
        print ("Page:{}".format(page), end="\r")
        c.showPage()
    c.save()
    print ("Totally {} labels generated.".format(tot))

if __name__ == "__main__":
    createBarCodes()
