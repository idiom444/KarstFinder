"""Exact continuous colors shared by markers, rasters and legends."""
from qgis.core import QgsGradientColorRamp,QgsGradientStop,QgsProperty,QgsSymbolLayer,QgsMarkerSymbol,QgsRuleBasedRenderer
from qgis.PyQt.QtGui import QColor
from .scoring import STOPS

COLOR_EXPRESSION="ramp_color(create_ramp(map(0,'#440154',0.25,'#3b528b',0.5,'#21918c',0.75,'#5ec962',1,'#fde725')),\"evidence_strength\")"


def ramp():
    return QgsGradientColorRamp(QColor(STOPS[0][1]),QColor(STOPS[-1][1]),False,[QgsGradientStop(v,QColor(c)) for v,c in STOPS[1:-1]])


def renderer():
    root=QgsRuleBasedRenderer.Rule(None)
    for kind,shape in [('cliff','triangle'),('depression','diamond'),('hydrology','circle'),('structure','square')]:
        symbol=QgsMarkerSymbol.createSimple({'name':shape,'size':'1.9','color':'#440154','outline_color':'#444444','outline_width':'.15'})
        layer=symbol.symbolLayer(0);layer.setDataDefinedProperty(QgsSymbolLayer.PropertyFillColor,QgsProperty.fromExpression(COLOR_EXPRESSION))
        layer.setDataDefinedProperty(QgsSymbolLayer.PropertyStrokeColor,QgsProperty.fromExpression("CASE WHEN \"geological_confidence\" < 0.3 THEN '#111111' ELSE '#444444' END"))
        layer.setDataDefinedProperty(QgsSymbolLayer.PropertyStrokeWidth,QgsProperty.fromExpression('CASE WHEN "geological_confidence" < 0.3 THEN 0.32 ELSE 0.15 END'))
        rule=QgsRuleBasedRenderer.Rule(symbol);rule.setFilterExpression(f'"kind" = \'{kind}\'');rule.setLabel(kind+' feature representative');root.appendChild(rule)
    return QgsRuleBasedRenderer(root)
