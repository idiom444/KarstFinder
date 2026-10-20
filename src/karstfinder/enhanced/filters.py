"""Reversible QGIS subsets; never mutate scientific registries or scores."""
import math


def literal(value):return "'"+str(value).replace("'","''")+"'"


def subset(min_strength=None,method=None,geology=None,zone=None,status=None,availability=None,min_geological_confidence=None):
    clauses=[]
    if min_strength is not None:
        if not math.isfinite(min_strength) or not 0<=min_strength<=1:raise ValueError('Strength outside [0,1]')
        clauses.append(f'"evidence_strength" >= {min_strength:.17g}')
    if min_geological_confidence is not None:
        if not math.isfinite(min_geological_confidence) or not 0<=min_geological_confidence<=1:raise ValueError('Confidence outside [0,1]')
        clauses.append(f'"geological_confidence" >= {min_geological_confidence:.17g}')
    if method:
        # Delimiter-aware exact token match, not a wildcard user expression.
        if any(c not in 'abcdefghijklmnopqrstuvwxyz_0123456789' for c in method):raise ValueError('Invalid method')
        clauses.append(f"('|' || \"methods\" || '|') LIKE {literal('%|'+method+'|%')}")
    for field,value in [('geo_class',geology),('zone_id',zone),('fieldwork_status',status)]:
        if value is not None:clauses.append(f'"{field}" = {literal(value)}')
    if availability:
        if availability not in ('terrain','imagery','pointcloud'):raise ValueError('Unknown availability flag')
        clauses.append(f'"has_{availability}" = 1')
    return ' AND '.join(clauses)
