"""Area-controlled metrics; no coordinate acquisition or cave-specific knowledge."""
import numpy as np


def select_area(scores,universe,fraction,seed=20261019):
    """Select an exact cell budget; ties use a fixed random order independent of labels."""
    if not 0<fraction<=1:raise ValueError('Area fraction must be in (0,1]')
    indices=np.flatnonzero(universe & np.isfinite(scores));n=int(np.floor(len(indices)*fraction+1e-9))
    selected=np.zeros(scores.shape,bool)
    if n==0:return selected
    order=np.random.default_rng(seed).permutation(len(indices))
    values=scores.ravel()[indices[order]]
    ranking=np.argsort(-values,kind='stable');chosen=indices[order[ranking[:n]]]
    selected.ravel()[chosen]=True
    return selected


def uncertainty_coverage(selected,region):
    n=int(region.sum())
    if not n:return {'coverage_fraction':None,'possible':False,'robust':False}
    hits=int((selected&region).sum())
    return {'coverage_fraction':hits/n,'possible':hits>0,'robust':hits==n}


def prediction_gain(recall,area_fraction):
    return recall/area_fraction if area_fraction>0 else None


def kvamme_gain(recall,area_fraction):
    return 1-area_fraction/recall if recall>0 else None


def qualifies_for_localization(properties,max_uncertainty_m):
    """An assumed small radius cannot substitute for verified source accuracy."""
    radius=properties.get('uncertainty_m')
    return (properties.get('accuracy_verified') is True and
            isinstance(radius,(int,float)) and np.isfinite(radius) and
            0<radius<=max_uncertainty_m)
