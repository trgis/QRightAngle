from qgis.core import QgsVectorLayer, QgsWkbTypes
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from . import resources
from .QRightAngle import QRightAngle

class MainPlugin:
    mapTool = None

    def __init__(self, iface):
        self.iface = iface   

    def initGui(self):
        self.action = QAction('Right Angle')
        self.action.triggered.connect(self.onClick)
        self.action.setIcon(QIcon(':/plugins/QRightAngle/icon.png'))
        self.action.setCheckable(True)
        self.action.setStatusTip("Select vector features for right angle processing ...")
        self.iface.addToolBarIcon(self.action)

        self.iface.currentLayerChanged.connect(self.currentLayerChanged)

        self.enableTool()

    def unload(self):
        self.iface.removeToolBarIcon(self.action)

    def currentLayerChanged(self):
        self.enableTool()

    def onClick(self):
        if not self.action.isChecked():
            self.iface.mapCanvas().unsetMapTool(self.mapTool)
            self.mapTool = None
            return

        self.action.setChecked(True)
        self.mapTool = QRightAngle(self.iface.mapCanvas())
        self.mapTool.setAction(self.action)
        self.iface.mapCanvas().setMapTool(self.mapTool)

    def enableTool(self):
        self.action.setEnabled(False)
        layer = self.iface.activeLayer()
        if layer != None and isinstance(layer, QgsVectorLayer):
            if layer.wkbType() in [QgsWkbTypes.Polygon, QgsWkbTypes.LineString]:
                self.action.setEnabled(True)
