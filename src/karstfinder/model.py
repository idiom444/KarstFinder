"""Explicit hypothesis indices; no fit to cave locations, no probabilities."""
import numpy as np


def score_landscape(deviations, slope, geology, valid, cfg):
    """Return independent terrain evidence and a lithology-weighted index."""
    dev = np.asarray(deviations)
    votes = (np.abs(dev) <= cfg['mid_slope_z_threshold']).sum(axis=0).astype(float)
    midslope = votes / dev.shape[0]
    lo, hi = cfg['exposure_slope_start_degrees'], cfg['exposure_slope_full_degrees']
    if hi <= lo:
        raise ValueError('Slope ramp must have positive width')
    exposure = np.clip((slope - lo) / (hi - lo), 0, 1)
    terrain = cfg['weights']['mid_slope'] * midslope + cfg['weights']['exposure'] * exposure
    combined = geology * terrain
    mask = valid & np.isfinite(slope) & np.all(np.isfinite(dev), axis=0)
    return {name: np.where(mask, value, np.nan) for name, value in
            [('mid_slope_votes', votes), ('exposure', exposure), ('terrain_score', terrain), ('combined_score', combined)]}
