"""Coordenadas dinamicas podem ser negativas em monitores secundarios."""
import math


def valid_bounds(bounds):
    return (all(isinstance(bounds.get(k),(int,float)) and math.isfinite(bounds[k]) for k in ('x','y','width','height'))
            and bounds['width']>0 and bounds['height']>0)


def in_desktop(point,rectangle):
    left,top,width,height=rectangle
    return width>0 and height>0 and left<=point[0]<left+width and top<=point[1]<top+height
