# pykarta/draw/shapes.py
# Copyright 2013, 2014, Trinity College
# Last modified: 21 August 2014

import cairo

# Add a rectangle with rounded corners to the path.
def rounded_rectangle(cr, x, y, w, h, r=20):
    # This is just one of the samples from 
    # http://www.cairographics.org/cookbook/roundedrectangles/
    #   A****BQ
    #  H      C
    #  *      *
    #  G      D
    #   F****E

    cr.move_to(x+r,y)                      # Move to A
    cr.line_to(x+w-r,y)                    # Straight line to B
    cr.curve_to(x+w,y,x+w,y,x+w,y+r)       # Curve to C, Control points are both at Q
    cr.line_to(x+w,y+h-r)                  # Move to D
    cr.curve_to(x+w,y+h,x+w,y+h,x+w-r,y+h) # Curve to E
    cr.line_to(x+r,y+h)                    # Line to F
    cr.curve_to(x,y+h,x,y+h,x,y+h-r)       # Curve to G
    cr.line_to(x,y+r)                      # Line to H
    cr.curve_to(x,y,x,y,x+r,y)             # Curve to A

def draw_rounded_rectangle(cr, x, y, w, h, r=20):
    """ draws rectangles with rounded (circular arc) corners """
    from math import pi
    cr.arc(x + r,     y + r,     r, 2*(pi/2), 3*(pi/2))
    cr.arc(x + w - r, y + r,     r, 3*(pi/2), 4*(pi/2))
    cr.arc(x + w - r, y + h - r, r, 0*(pi/2), 1*(pi/2))
    cr.arc(x + r,     y + h - r, r, 1*(pi/2), 2*(pi/2))
    cr.close_path()
    cr.stroke()

"""
if __name__ == '__main__':
    import cairo, Image

    w,h = 800, 600
    offset = 100
    fig_size = (w,h)

    # an area with coordinates of
    # (top, bottom, left, right) edges in absolute coordinates:
    inside_area = (offset, w-offset, offset, h-offset)

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, *fig_size)
    cr = cairo.Context(surface)
    cr.set_line_width(3)
    cr.set_source_rgb(1,1,1)

    draw_rounded(cr, offset, offset, w - 2 * offset, h - 2 * offset, 50)

    im = Image.frombuffer("RGBA",
                           fig_size,
                           surface.get_data(),
                           "raw",
                           "BGRA",
                           0,1)
    im.show()
"""

