import numpy as np
from karstfinder.evaluation import select_area,uncertainty_coverage,prediction_gain,kvamme_gain
from karstfinder.evaluation import qualifies_for_localization


def test_area_budget_ties_are_exact_and_reproducible():
    scores=np.ones((10,10));universe=np.ones_like(scores,bool)
    a=select_area(scores,universe,.1);assert a.sum()==10
    np.testing.assert_array_equal(a,select_area(scores,universe,.1))


def test_high_scores_selected_and_invalid_cells_excluded():
    scores=np.arange(100,dtype=float).reshape(10,10);scores[-1,-1]=np.nan
    universe=np.ones_like(scores,bool);universe[-1,:]=False
    selected=select_area(scores,universe,1/9)
    assert selected.sum()==10 and selected[8].all() and not selected[9].any()


def test_uncertainty_overlap_does_not_become_robust_success():
    region=np.ones((2,2),bool);selected=np.array([[1,0],[0,0]],bool)
    result=uncertainty_coverage(selected,region)
    assert result=={'coverage_fraction':.25,'possible':True,'robust':False}


def test_gains_handle_zero_recall_explicitly():
    assert prediction_gain(.5,.1)==5
    assert kvamme_gain(.5,.1)==.8
    assert kvamme_gain(0,.1) is None


def test_assumed_accuracy_never_qualifies_for_entrance_localization():
    assert not qualifies_for_localization({'uncertainty_m':5,'accuracy_verified':False},25)
    assert not qualifies_for_localization({'uncertainty_m':5},25)
    assert not qualifies_for_localization({'uncertainty_m':100,'accuracy_verified':True},25)
    assert not qualifies_for_localization({'uncertainty_m':float('nan'),'accuracy_verified':True},25)
    assert qualifies_for_localization({'uncertainty_m':25,'accuracy_verified':True},25)
