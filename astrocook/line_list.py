from .frame import Frame
from astropy import units as au

class LineList(Frame):
    """Class for line lists

    A LineList is a Frame with methods for handling spectral lines."""

    def __init__(self,
                 x=[],
                 xmin=[],
                 xmax=[],
                 y=[],
                 dy=[],
                 xunit=au.nm,
                 yunit=au.erg/au.cm**2/au.s/au.nm,
                 meta={},
                 dtype=float):
        super(LineList, self).__init__(x, xmin, xmax, y, dy, xunit, yunit, meta,
                                       dtype)

    def _copy(self, sel=None):
        copy = super(LineList, self)._copy(sel)
        cols = [c for c in self._t.colnames \
                if c not in ['x', 'xmin', 'xmax', 'y', 'dy']]
        for c in cols:
            copy._t[c] = self._t[c][sel]
        return copy