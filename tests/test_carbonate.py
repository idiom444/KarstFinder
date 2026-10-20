"""Geological eligibility and small, interpretable carbonate sites."""
from pathlib import Path
import json
import pytest
from osgeo import ogr,gdal,osr
import numpy as np
from karstfinder.carbonate.common import config
from karstfinder.carbonate.priority import priority,terrain_strength
from karstfinder.carbonate.grouping import related,group_observations
from karstfinder.carbonate.scope import polygons,geometry_key
from karstfinder.carbonate.pipeline import burn,stable_id


def box(a,b,c,d):return ogr.CreateGeometryFromWkt(f'POLYGON(({a} {b},{c} {b},{c} {d},{a} {d},{a} {b}))')


def obs(ident,geom,kind='cliff',formation='unit-a'):
    return {'object_id':ident,'_geom':geom,'kind':kind,'formation_id':formation}


def test_terrain_cannot_create_candidate_without_carbonate():
    settings=config()['scoring']
    assert priority(False,0,1,settings)==(None,None)
    score,factor=priority(True,0,1,settings)
    assert score==factor==.35  # only explicitly admitted contact margin
    assert priority(True,1,1,settings)==(1,1)
    with pytest.raises(ValueError):priority(True,1.1,1,settings)


def test_local_quantiles_and_single_method_survive():
    s=config()['scoring']
    assert terrain_strength('cliff',{},s)==.2
    assert terrain_strength('depression',{'depression_depth':{'max':1.5}},s)==.5
    assert terrain_strength('hydrology',{},s)==.4
    assert priority(True,1,.2,s)[0]==.2
    measured={f'residual_{n}m':{'q10':0} for n in [11,31,61]}
    measured['residual_11m']['min']=-100
    assert terrain_strength('cliff',measured,s)==.2


def test_nearby_features_need_eligible_geological_connector():
    left=box(0,0,2,2);right=box(4,0,6,2)
    assert related(left,right,box(0,0,6,2),10)[0]
    assert not related(left,right,left.Union(right),10)[0]
    assert not related(left,box(20,0,22,2),box(0,0,22,2),10)[0]


def test_different_formations_do_not_merge():
    rows=[obs('a',box(0,0,2,2)),obs('b',box(1,0,3,2),formation='unit-b')]
    assert len(group_observations(rows,box(0,0,10,10),10))==2


def test_hydrology_can_support_but_not_bridge_two_sites():
    rows=[obs('left',box(0,0,2,2)),obs('right',box(40,0,42,2)),obs('drain',box(0,0,42,1),kind='hydrology')]
    result=group_observations(rows,box(0,0,42,2),10)
    assert len(result)==2
    assert all('drain' in [m['object_id'] for m in g['members']] for g in result)
    assert all(len(g['surface_ids'])==1 for g in result)


def test_grouping_is_order_independent():
    rows=[obs('a',box(0,0,2,2)),obs('b',box(4,0,6,2)),obs('c',box(40,0,42,2))]
    ids=lambda groups:sorted(tuple(m['object_id'] for m in g['members']) for g in groups)
    assert ids(group_observations(rows,box(0,0,50,5),10))==ids(group_observations(rows[::-1],box(0,0,50,5),10))
    assert stable_id('x:', ['a','b'])==stable_id('x:',['b','a'])


def test_gdal_mask_does_not_admit_unknown_landscape():
    s=osr.SpatialReference();s.ImportFromEPSG(26910)
    ref=gdal.GetDriverByName('MEM').Create('',100,100,1,gdal.GDT_Byte);ref.SetGeoTransform([0,1,0,100,0,-1]);ref.SetProjection(s.ExportToWkt())
    core=box(45,45,55,55);mask=burn(core,ref)
    assert mask.sum()==100 and not mask[0,0]
    assert burn(core.Buffer(25),ref).sum()<4000


def test_unit_names_and_melange_not_eligibility_shortcuts():
    cfg=config()
    assert set(cfg['eligible_units'])=={'PMmb(e)','TRmb(e)'}
    assert 'JTRmt(e)' not in cfg['eligible_units']
    assert 'Marble Creek' not in cfg['eligible_units']
    assert cfg['boundary_margin_m']==25


def test_ordinary_drainage_cannot_seed_a_prospecting_destination():
    rows=[obs('drain',box(0,0,20,2),kind='hydrology')]
    assert group_observations(rows,box(0,0,30,10),10)==[]
