# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QRightAngle
                                 A QGIS plugin
 The plugin for right angle processing of vector features
                              -------------------
        begin                : 2020-04-03
        copyright            : (C) 2020 by DHui Jiang
        email                : dhuijiang@163.com
        git                  : https://github.com/dhuijiang/QRightAngle
 ***************************************************************************/
"""

import os
import math
from datetime import datetime
from qgis.core import *
from qgis.PyQt.QtCore import Qt, QRect
from qgis.PyQt.QtGui import QColor
from qgis.gui import QgsMapToolEdit, QgsRubberBand
import qgis.utils

class QRightAngle(QgsMapToolEdit):

    CanDoTypes = [
        QgsWkbTypes.Polygon,
        QgsWkbTypes.LineString,
    ]

    def __init__(self, mapCanvas):
        self.canvas = mapCanvas
        QgsMapToolEdit.__init__(self, self.canvas)
        self.isDragging = False
        self.selectionRubberBand = QgsRubberBand(self.canvas, True)
        color = QColor(Qt.blue)
        color.setAlpha(63)
        self.selectionRubberBand.setColor(color)
        self.selectionRect = QRect()
        self.selectedFeatures = []
        self.rubberBands = []

    def clearSelection(self):
        self.selectedFeatures.clear()
        self.rubberBands.clear()
        self.selectionRubberBand.reset(True)

    def canvasPressEvent(self, e):
        if e.buttons() != Qt.LeftButton:
            return
        if not self.currentVectorLayer():
            self.notifyNotVectorLayer()
            return
        self.clearSelection()
        self.selectionRect.setRect(0,0,0,0)

    def canvasMoveEvent(self, e):
        if e.buttons() != Qt.LeftButton:
            return
        if not self.isDragging:
            self.isDragging = True
            self.selectionRect.setTopLeft(e.pos())
        self.selectionRect.setBottomRight(e.pos())
        self.selectionRubberBand.setToCanvasRectangle(self.selectionRect)
        self.selectionRubberBand.show()

    def canvasReleaseEvent(self, e):
        if e.buttons() == Qt.RightButton:
            self.clearSelection()
            return
        vlayer = self.currentVectorLayer()
        if e.button() != Qt.LeftButton or not vlayer:
            return

        self.selectionRubberBand.reset(True)
        
        if self.isDragging and self.selectionRect.topLeft() != self.selectionRect.bottomRight():
            self.isDragging = False
            # store the rectangle
            self.selectionRect.setRight(e.pos().x())
            self.selectionRect.setBottom(e.pos().y())

            self.selectFeaturesInRect()
        else:
            self.selectOneFeature(e.pos())

        self.isDragging = False

        self.messageEmitted.emit(self.tr('{0} features in layer {1} selected.'.format(len(self.selectedFeatures), vlayer.name())))

        if not self.selectedFeatures:
            return

        # count vertices, prepare rubber bands
        for f in self.selectedFeatures:
            rb = self.createRubberBand()
            rb.show()
            self.rubberBands.append(rb)

        vlayer = self.currentVectorLayer()
        if vlayer.isEditable():
            self.storeRightAngled()
        else:
            self.updateRightAnglePreview()

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.clearSelection()
            return
        e.accept()

    def selectOneFeature(self, canvasPoint):
        vlayer = self.currentVectorLayer()
        layerCoords = self.toLayerCoordinates(vlayer, canvasPoint)
        r = QgsTolerance.vertexSearchRadius(vlayer, self.canvas.mapSettings())
        selectRect = QgsRectangle(layerCoords.x() - r, layerCoords.y() - r,
                                  layerCoords.x() + r, layerCoords.y() + r)
        selectedFeatures = vlayer.getFeatures(QgsFeatureRequest().setFilterRect(selectRect).setNoAttributes())

        geometry = QgsGeometry.fromPointXY(layerCoords)
        minDistance = float('inf')
        currentDistance = float('inf')
        minDistanceFeature = QgsFeature()
        for f in selectedFeatures:
            if f.geometry().wkbType() in self.CanDoTypes:
                currentDistance = geometry.distance(f.geometry())
                if currentDistance < minDistance:
                    minDistance = currentDistance
                    minDistanceFeature = f

        if minDistanceFeature.isValid():
            self.selectedFeatures.append(minDistanceFeature)

    def selectFeaturesInRect(self):
        vlayer = self.currentVectorLayer()
        pt1 = self.toMapCoordinates(self.selectionRect.topLeft())
        pt2 = self.toMapCoordinates(self.selectionRect.bottomRight())
        rect = self.toLayerCoordinates(vlayer, QgsRectangle(pt1, pt2))

        request = QgsFeatureRequest()
        request.setFilterRect(rect)
        request.setFlags(QgsFeatureRequest.ExactIntersect)
        request.setNoAttributes()
        selectedFeatures = vlayer.getFeatures(request)
        for f in selectedFeatures:
            if f.geometry().wkbType() in self.CanDoTypes:
                self.selectedFeatures.append(f)

    def updateRightAnglePreview(self):
        vlayer = self.currentVectorLayer()
        i = 0
        for f in self.selectedFeatures:
            g = self.processGeometry(f.geometry().constGet())
            if not g.isNull():
                self.rubberBands[i].setToGeometry(g, vlayer)
            else:
                # error
                pass
            i += 1

    def calculateLengthSquared2D(self, x1, y1, x2, y2):
        vx = x2 - x1
        vy = y2 - y1
        return ( vx * vx ) + ( vy * vy ) if vx != 0 or vy != 0 else 1

    def processGeometry(self, geometry, isaLinearRing = False):
        wkbType = geometry.wkbType()
        flatType = QgsWkbTypes.flatType(wkbType)

        if flatType == QgsWkbTypes.LineString:
            srcCurve = geometry
            numPoints = srcCurve.numPoints()

            lineStringX = []
            lineStringY = []

            # Check whether the LinearRing is really closed.
            if isaLinearRing:
                isaLinearRing = qgsDoubleNear(srcCurve.xAt(0), srcCurve.xAt(numPoints - 1)) and \
                                qgsDoubleNear(srcCurve.yAt(0), srcCurve.yAt(numPoints - 1))
            
            x = 0.0; y = 0.0; lastX = 0.0; lastY = 0.0; startX = 0.0; startY = 0.0; endX = 0.0; endY = 0.0

            # Do RightAngle
            for i in range(numPoints):
                x = srcCurve.xAt(i)
                y = srcCurve.yAt(i)

                if i > 0:
                    startX = endX
                    startY = endY
                    endX = lastX
                    endY = lastY
                    lastX = srcCurve.xAt((i + 1) % numPoints)
                    lastY = srcCurve.yAt((i + 1) % numPoints)
                    lastX = (lastX + x) / 2
                    lastY = (lastY + y) / 2
                    magnitude2 = self.calculateLengthSquared2D(startX, startY, endX, endY)
                    u = ((lastX - startX) * (endX - startX) + (lastY - startY) * (endY - startY)) / magnitude2
                    endX = startX + u * (endX - startX)
                    endY = startY + u * (endY - startY)

                else:
                    startX = x
                    startY = y
                    endX = x
                    endY = y
                    lastX = srcCurve.xAt((i + 1) % numPoints)
                    lastY = srcCurve.yAt((i + 1) % numPoints)

                lineStringX.append(endX)
                lineStringY.append(endY)

            if isaLinearRing:
                lineStringX[0] = endX
                lineStringY[0] = endY

            output = QgsLineString(lineStringX, lineStringY)

            return QgsGeometry(output)

        elif flatType == QgsWkbTypes.Polygon:
            srcPolygon = geometry
            polygon = QgsPolygon()
            extRing = self.processGeometry(srcPolygon.exteriorRing(), True)
            polygon.setExteriorRing(extRing.constGet().clone())
            for i in range(srcPolygon.numInteriorRings()):
                sub = srcPolygon.interiorRing(i)
                ring = self.processGeometry(sub, True)
                polygon.addInteriorRing(ring.constGet().clone())
            return QgsGeometry(polygon)

        return QgsGeometry()

    def storeRightAngled(self):
        vlayer = self.currentVectorLayer()
        vlayer.beginEditCommand(self.tr('Geometry RightAngle'))
        numOfRightAngled = 0
        for f in self.selectedFeatures:
            g = self.processGeometry(f.geometry().constGet())
            if not g.isNull():
                vlayer.changeGeometry(f.id(), g)
                numOfRightAngled += 1
        self.messageEmitted.emit(self.tr('{0} features on layer {1} RightAngled.'.format(numOfRightAngled, vlayer.name())))
        vlayer.endEditCommand()
        self.clearSelection()
        vlayer.triggerRepaint()

    def deactivate(self):
        super(QRightAngle, self).deactivate()
        self.deactivated.emit()
        self.clearSelection()
