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

import os.path
import configparser
from datetime import datetime

# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    from .plugin import MainPlugin
    return MainPlugin(iface)

# Define plugin wide constants
PLUGIN_NAME = 'QRightAngle'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_PREFIX = ':plugins/{}/'.format(PLUGIN_NAME)

# Read metadata.txt
METADATA = configparser.ConfigParser()
METADATA.read(os.path.join(BASE_DIR, 'metadata.txt'), encoding='utf-8')
today = datetime.today()

__version__ = METADATA['general']['version']
__author__ = METADATA['general']['author']
__email__ = METADATA['general']['email']
__web__ = METADATA['general']['homepage']
__help__ = METADATA['general']['help']
__date__ = today.strftime('%Y-%m-%d')
__copyright__ = '(C) {} by {}'.format(today.year, __author__)