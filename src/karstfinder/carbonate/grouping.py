"""Small local exposure systems, using GIS geometry rather than proximity alone."""
from osgeo import ogr
from qgis.core import QgsGeometry
from .scope import union,geometry_key


def related(left,right,eligible,max_gap):
    if left.Intersects(right):return True,0.,'overlapping or touching eligible footprints'
    distance=left.Distance(right)
    if distance>max_gap:return False,distance,'separate footprints'
    a=QgsGeometry();a.fromWkb(bytes(left.ExportToWkb()));b=QgsGeometry();b.fromWkb(bytes(right.ExportToWkb()))
    shortest=a.shortestLine(b)
    if shortest.isEmpty():return False,distance,'no GIS shortest connector'
    line=ogr.CreateGeometryFromWkb(bytes(shortest.asWkb()))
    # Numerical tolerance only, not a second geological uncertainty margin.
    inside=line.Difference(eligible.Buffer(.001)).Length()<=.002
    return inside,distance,f'same formation; <={max_gap:g} m gap with connector inside eligible geology' if inside else 'connector crosses ineligible geology'


def group_observations(observations,eligible,max_gap):
    ordered=sorted(observations,key=lambda o:o['object_id']);surface=[o for o in ordered if o['kind']!='hydrology'];hydro=[o for o in ordered if o['kind']=='hydrology']
    parents=list(range(len(surface)))
    def root(i):
        while parents[i]!=i:parents[i]=parents[parents[i]];i=parents[i]
        return i
    edges=[]
    for i,left in enumerate(surface):
        for j in range(i):
            right=surface[j]
            if left['formation_id']!=right['formation_id']:continue
            ok,distance,reason=related(left['_geom'],right['_geom'],eligible,max_gap)
            if ok:
                a,b=root(i),root(j)
                if a!=b:parents[max(a,b)]=min(a,b)
                edges.append({'left':left['object_id'],'right':right['object_id'],'gap_m':distance,'relationship':reason})
    groups={}
    for i,obj in enumerate(surface):groups.setdefault(root(i),[]).append(obj)
    result=[{'members':members,'surface_ids':[m['object_id'] for m in members],'attachments':[]} for members in groups.values()]
    # Hydrological setting masks can support several exposure systems, but
    # never join otherwise distinct cliff/depression sites into a mega-site.
    for obj in hydro:
        for group in result:
            if not group['surface_ids']:continue
            matches=[]
            for member in group['members']:
                if member['kind']=='hydrology' or member['formation_id']!=obj['formation_id']:continue
                ok,distance,reason=related(obj['_geom'],member['_geom'],eligible,max_gap)
                if ok:matches.append((distance,member['object_id'],reason))
            if matches:
                distance,ident,reason=min(matches);group['members'].append(obj);group['attachments'].append({'object_id':obj['object_id'],'supports':ident,'gap_m':distance,'relationship':reason})
        # Unattached modeled drainage remains inspectable context, never a destination.
    for group in result:
        ids=sorted(m['object_id'] for m in group['members']);group['members']=sorted(group['members'],key=lambda m:m['object_id'])
        group['edges']=[e for e in edges if e['left'] in ids and e['right'] in ids]
    return result
