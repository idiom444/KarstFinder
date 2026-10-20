"""Separate, versioned ranking AFTER the documented-carbonate eligibility gate."""


def terrain_strength(kind,measurements,settings):
    def value(name,key):return (measurements.get(name) or {}).get(key)
    if kind=='cliff':
        residuals=[value(f'residual_{w}m','q10') for w in (11,31,61)]
        valid=[v for v in residuals if v is not None]
        if not valid:return settings['cliff_floor']
        relief=min(1,max(max(0,-v) for v in valid)/settings['robust_recess_scale_m'])
        return settings['cliff_floor']+(1-settings['cliff_floor'])*relief
    if kind=='depression':
        depth=value('depression_depth','max')
        return None if depth is None else min(1,max(0,depth)/settings['depression_depth_scale_m'])
    if kind=='hydrology':return settings['hydrology_support']
    raise ValueError('Unsupported detector: '+kind)


def priority(eligible,carbonate_fraction,terrain,settings):
    """Outside geology is ineligible, not a terrain-only prospecting candidate."""
    if not eligible:return None,None
    if not 0<=carbonate_fraction<=1:raise ValueError('Invalid carbonate fraction')
    factor=settings['boundary_support_factor']+(1-settings['boundary_support_factor'])*carbonate_fraction
    return (None if terrain is None else factor*terrain),factor
