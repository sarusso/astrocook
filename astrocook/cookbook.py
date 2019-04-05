from .syst_list import SystList
from .syst_model import SystModel
from astropy import units as au
import numpy as np

class Cookbook(object):
    """ Class for cookbook.

    A Cookbook contains all procedures called by Session."""

    def __init__(self,
                 sess):
        self.sess = sess
        #self.spec = sess.spec
        #self.systs = sess.systs

    def _append_syst(self):
        systs = self.sess.systs
        if systs != None:
            systs._append(SystList(id_start=len(systs._t)))
        else:
            setattr(self.sess, 'systs', SystList())

    def _create_doubl(self, series='Ly_a', z_mean=2.0, logN=14, b=10,
                      resol=70000):

        spec = self.sess.spec
        systs = self.sess.systs
        spec._shift_rf(z_mean)
        mod = SystModel(spec, systs, z0=0)
        mod._new_voigt(series, 0, logN, b, resol)
        spec._shift_rf(0.0)
        xm = mod._xf
        hlenm = len(xm)//2
        ym = mod.eval(x=xm, params=mod._pars)
        ym_0 = np.ones(len(xm))
        ym_1 = np.concatenate([ym[:-hlenm], np.ones(hlenm)])
        ym_2 = np.concatenate([np.ones(hlenm), ym[hlenm:]])

        return xm, ym, ym_0, ym_1, ym_2

    def _fit_syst(self, series='CIV', z=2, logN=13, b=10, resol=70000,
                  maxfev=100):

        spec = self.sess.spec
        systs = self.sess.systs
        systs._add(series, z, logN, b, resol)
        mod = SystModel(spec, systs, z0=z)
        mod._new_voigt(series, z, logN, b, resol)
        mod._fit(fit_kws={'maxfev': maxfev})
        systs._update(mod)
        return 0

    def _test_doubl(self, xm, ym, ym_0, ym_1, ym_2, col='y'):

        spec = self.sess.spec
        ys = np.interp(xm, spec.x.to(au.nm), spec._t[col]/spec._t['cont'])
        dys = np.interp(xm, spec.x.to(au.nm), spec.dy/spec._t['cont'])
        chi2 = np.sum(((ys-ym)/dys)**2)
        chi2_0 = np.sum(((ys-ym_0)/dys)**2)
        chi2_1 = np.sum(((ys-ym_1)/dys)**2)
        chi2_2 = np.sum(((ys-ym_2)/dys)**2)
        if chi2 < np.min([chi2_0-3, chi2_1, chi2_2]):
            return True, chi2, chi2_0
        else:
            return False, chi2, chi2_0

    def _update_spec(self):
        spec = self.sess.spec
        systs = self.sess.systs

        systs._xs = np.array(spec._safe(spec.x).to(au.nm))
        s = spec._where_safe

        y = spec.y
        if 'model' not in spec._t.colnames:
            spec._t['model'] = np.empty(len(spec.x), dtype=float)*y.unit
        if 'deabs' not in spec._t.colnames:
            spec._t['deabs'] = y

        cont = spec._t['cont']
        model = spec._t['model']
        deabs = spec._t['deabs']

        model[s] = cont[s]
        for i, r in enumerate(systs._mods_t):
            mod = r['mod']
            model[s] = mod.eval(x=systs._xs, params=mod._pars) * model[s]
        deabs[s] = cont[s] + y[s] - model[s]