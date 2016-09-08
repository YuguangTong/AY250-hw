# keep track of attempts that failed ...

# super resolution imaging

prob 1
# i don't know why the correlation does not peak at correct pixel shifts...
from skimage.feature import register_translation
from scipy.interpolate import RectBivariateSpline
from scipy.optimize import minimize

import os
from skimage.io import imread
import matplotlib.pyplot as plt
import scipy, skimage
import numpy as np

def find_shift(corr):
    """
    find the peak of correlation function by 
    1, bivariate spline approximation over a rectangular mesh.
    2, then use optimziation function to find the peak
    """
    corr = np.array(corr)
    m, n = corr.shape
    
    # x and y index for 0 shift:
    x0 = int((m-1)/2)
    y0 = int((n-1)/2)
    
    # x and y index for integral part of the shift
    indmax = np.argmax(corr)
    xint = int(indmax/n)
    yint = indmax % n 
    
    # interpolate coor(x, y) near (xint, yint)
    # to avoid slow interpolation, examine 20 pixels near (xint, yint)
    r = 10
    xgrid = np.arange(-r, r, 1)
    ygrid = np.arange(-r, r, 1)
    zgrid = corr[xint-r:xint+r, yint-r:yint+r].T - corr[xint, yint]
    interp_f= RectBivariateSpline(xgrid, ygrid, zgrid)
    f2minimize = lambda x: -float(interp_f.ev(x[0], x[1]))
    
    # add small perturbation in starting point 
    delta = 0.01
    guess = [delta, delta]
    min_result = minimize(f2minimize, guess)
    
    if not min_result.success:
        raise RuntimeError('failed to converge to the peak of the correlation function')
    
    xfrac, yfrac = min_result.x
    
    # round to 2 decimal points
    return np.round((xint+xfrac-x0, yint+yfrac-y0), 2)
