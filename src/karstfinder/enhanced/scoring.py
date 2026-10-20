"""Ordinal evidence, separate confidence, and the exact continuous sRGB ramp."""
import math
from .common import config

STOPS=((0.,'#440154'),(.25,'#3b528b'),(.5,'#21918c'),(.75,'#5ec962'),(1.,'#fde725'))


def color(value):
    if not math.isfinite(value) or not 0<=value<=1:raise ValueError('Strength must be finite in [0,1]')
    for (lo,left),(hi,right) in zip(STOPS,STOPS[1:]):
        if value<=hi:
            f=(value-lo)/(hi-lo)
            rgb=[int(math.floor(int(left[i:i+2],16)*(1-f)+int(right[i:i+2],16)*f+.5)) for i in (1,3,5)]
            return '#'+''.join(f'{c:02x}' for c in rgb)
    return STOPS[-1][1]


def combine(components,weights=None):
    """Missing is NULL, zero is measured absence. Correlated components use max.

    Coverage never renormalizes the sum. A single supported method is retained;
    score is neither a retention gate nor a cave probability.
    """
    weights=weights or config()['scoring']['family_weights']
    contributions={};coverage={}
    for family,weight in weights.items():
        values=[v for v in components.get(family,{}).values() if v is not None]
        if any(not math.isfinite(v) or not 0<=v<=1 for v in values):raise ValueError('Invalid component')
        coverage[family]=bool(values)
        contributions[family]=weight*max(values) if values else None
    return sum(v for v in contributions.values() if v is not None),contributions,coverage


def morphology(kind,depth,q10_residuals):
    if kind=='depression':return min(1,max(0,depth or 0)/3)
    if kind=='cliff':
        # Detection supplies weak support; robust negative relief adds support.
        valid=[v for v in q10_residuals if v is not None]
        return .2+.8*min(1,max([max(0,-v)/2 for v in valid],default=0))
    return None
