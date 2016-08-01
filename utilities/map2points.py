#!/usr/bin/env python3

import os, os.path, sys


USAGE="""{argv0} <input-file-name>.map [<output-file-name>.points]
"""

def convert(infile, outfile):
    inf=open(infile,"rb")
    ouf=open(outfile,"wb")
    ouf.write(b"mapX,mapY,pixelX,pixelY,enable\n")
    for line in inf:
        line=line.strip()
        if not line.startswith(b"Point"):
            continue
        v=line.split(b",")
        v=[_.strip() for _ in v]
        _,_,x,y,_,_,lat_g,lat_m,_,lon_g,lon_m,_ = v[:12]
        print(x,y,lat_g,lat_m,lon_g,lon_m)
        if x:
            lat_g,lat_m,lon_g,lon_m=map(float, [lat_g,lat_m,lon_g,lon_m])
            x,y=int(x),int(y)
            ouf.write(("{},{},{},{},1\n".format(lat_g+lat_m/60., lon_g+lon_m/60.,x,-y)).encode("utf-8"))


def main():
    if len(sys.argv)==1:
        print (USAGE.format(argv0=sys.argv[0]))
        return
    infile=sys.argv[1]
    if len(sys.argv)==2:
        name,ext=os.path.splitext(infile)
        outfile=name+".points"
    return convert(infile,outfile)



if __name__=="__main__":
    main()
    quit()
