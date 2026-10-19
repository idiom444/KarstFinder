import json
from pathlib import Path
import numpy as np
from karstfinder.model import score_landscape

CFG=json.loads((Path(__file__).parents[1]/'configs/blind_v001.json').read_text())


def evaluate(dev=0.,slope=30.,geo=1.,valid=True):
    return score_landscape(np.full((3,2,2),dev),np.full((2,2),slope),np.full((2,2),geo),np.full((2,2),valid),CFG)


def test_scores_have_explicit_components():
    r=evaluate()
    np.testing.assert_allclose(r['mid_slope_votes'],3)
    np.testing.assert_allclose(r['terrain_score'],.8)
    np.testing.assert_allclose(r['combined_score'],.8)


def test_geology_scales_index_without_creating_probability():
    np.testing.assert_allclose(evaluate(geo=.35)['combined_score'],.28)
    np.testing.assert_allclose(evaluate(geo=0)['combined_score'],0)


def test_missing_support_stays_nodata_not_zero():
    assert np.isnan(evaluate(valid=False)['combined_score']).all()
    assert np.isnan(evaluate(dev=np.nan)['terrain_score']).all()


def test_mid_slope_threshold_is_symmetric_and_inclusive():
    assert evaluate(dev=.5)['mid_slope_votes'][0,0]==3
    assert evaluate(dev=-.5)['mid_slope_votes'][0,0]==3
    assert evaluate(dev=.50001)['mid_slope_votes'][0,0]==0


def test_exposure_clips_at_configured_endpoints():
    assert evaluate(slope=0)['exposure'][0,0]==0
    assert evaluate(slope=90)['exposure'][0,0]==1


def test_three_scales_are_voted_independently():
    dev=np.array([np.full((2,2),v) for v in [0.,1.,-1.]])
    r=score_landscape(dev,np.zeros((2,2)),np.ones((2,2)),np.ones((2,2),bool),CFG)
    np.testing.assert_allclose(r['combined_score'],.2)
