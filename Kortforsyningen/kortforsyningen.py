# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Kortforsyningen
                                 A QGIS plugin
 Easy access to WMS from Kortforsyningen (A service by The Danish geodataservice. Styrelsen for Dataforsyning og Effektivisering)
                              -------------------
        begin                : 2015-05-01
        git sha              : $Format:%H$
        copyright            : (C) 2015 Agency for Data supply and Efficiency
        email                : kortforsyningen@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import absolute_import
from builtins import str
from builtins import object
import codecs
import os.path
import datetime
from urllib.request import (
    urlopen
)
from urllib.error import (
    URLError,
    HTTPError
)
from qgis.gui import QgsMessageBar
from qgis.core import *

from qgis.PyQt.QtCore import QCoreApplication, QFileInfo, QUrl, QSettings, QTranslator, qVersion

from qgis.PyQt.QtWidgets import QAction, QMenu, QPushButton
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt import QtXml
from .mysettings import *
from .qlr_file import QlrFile
from .config import Config

from .layerlocatorfilter import LayerLocatorFilter
ABOUT_FILE_URL = 'https://apps2.kortforsyningen.dk/qgis_knap_config/QGIS3/About/qgis3about.html'
FILE_MAX_AGE = datetime.timedelta(hours=12)

def log_message(message):
    QgsMessageLog.logMessage(message, 'Kortforsyningen plugin')

class Kortforsyningen(object):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize options
        self.settings = Settings()
        self.settings.settings_updated.connect(self.reloadMenu)
        self.options_factory = OptionsFactory(self.settings)
        self.options_factory.setTitle(self.tr('Kortforsyningen'))
        iface.registerOptionsWidgetFactory(self.options_factory)
        
        self.layer_locator_filter = LayerLocatorFilter()
        self.iface.registerLocatorFilter(self.layer_locator_filter)
        # An error menu object, set to None.
        self.error_menu = None
        # Categories
        self.categories = []
        self.nodes_by_index = {}
        self.node_count = 0

        # initialize locale
        path = QFileInfo(os.path.realpath(__file__)).path()
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
             path,
            'i18n',
            '{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

    def initGui(self):
        self.createMenu()
        
    def show_kf_error(self):
        message = u'Check connection and click menu Settings -> Options - > Kortforsyningen -> OK'
        self.iface.messageBar().pushMessage("No contact to Kortforsyningen", message, level=Qgis.Warning, duration=5)
        log_message(message)

    def show_kf_settings_warning(self):
        message = u'Username/Password not set or wrong. Select menu Settings -> Options - > Kortforsyningen'
        self.iface.messageBar().pushMessage("Kortforsyningen", message, level=Qgis.Warning, duration=5)
        log_message(message)

    def createMenu(self):
        self.config = Config(self.settings)
        self.config.kf_con_error.connect(self.show_kf_error)
        self.config.kf_settings_warning.connect(self.show_kf_settings_warning)
        self.config.load()
        self.categories = self.config.get_categories()
        self.category_lists = self.config.get_category_lists()
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        self.menu = QMenu(self.iface.mainWindow().menuBar())
        self.menu.setObjectName(self.tr('Kortforsyningen'))
        self.menu.setTitle(self.tr('Kortforsyningen'))
        
        searchable_layers = []

        if self.error_menu:
            self.menu.addAction(self.error_menu)

        # Add menu object for each theme
        self.category_menus = []
        kf_helper = lambda _id: lambda: self.open_kf_node(_id)
        local_helper = lambda _id: lambda: self.open_local_node(_id)
        
        for category_list in self.category_lists:
            list_categorymenus = []
            for category in category_list:
                category_menu = QMenu()
                category_menu.setTitle(category['name'])
                for selectable in category['selectables']:
                    q_action = QAction(
                        selectable['name'], self.iface.mainWindow()
                    )
                    if selectable['source'] == 'kf':
                        q_action.triggered.connect(
                            kf_helper(selectable['id'])
                        )
                    else:
                        q_action.triggered.connect(
                            local_helper(selectable['id'])
                        )
                    category_menu.addAction(q_action)
                    searchable_layers.append(
                        {
                            'title': selectable['name'],
                            'category': category['name'],
                            'action': q_action
                        }
                    )
                list_categorymenus.append(category_menu)
                self.category_menus.append(category_menu)
            for category_menukuf in list_categorymenus:
                self.menu.addMenu(category_menukuf)
            self.menu.addSeparator()
        self.layer_locator_filter.set_searchable_layers(searchable_layers)
        # Add about
        icon_path_info = os.path.join(os.path.dirname(__file__), 'images/icon_about.png')
        self.about_menu = QAction(
            QIcon(icon_path_info),
            self.tr('About the plugin') + '...',
            self.iface.mainWindow()
        )
        self.about_menu.setObjectName(self.tr('About the plugin'))
        self.about_menu.triggered.connect(self.about_dialog)
        self.menu.addAction(self.about_menu)

        menu_bar = self.iface.mainWindow().menuBar()
        menu_bar.insertMenu(
            self.iface.firstRightStandardMenu().menuAction(), self.menu
        )
        
    def open_local_node(self, id):
        node = self.config.get_local_maplayer_node(id)
        self.open_node(node, id)

    def open_kf_node(self, id):
        node = self.config.get_kf_maplayer_node(id)
        layer = self.open_node(node, id)

    def open_node(self, node, id):
        QgsProject.instance().readLayer(node)
        layer = QgsProject.instance().mapLayer(id)
        #if layer:
            #self.iface.legendInterface().refreshLayerSymbology(layer)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Kortforsyningen', message)

    # Taken directly from menu_from_project
    def getFirstChildByTagNameValue(self, elt, tagName, key, value):
        nodes = elt.elementsByTagName(tagName)
        i = 0
        while i < nodes.count():
            node = nodes.at(i)
            idNode = node.namedItem(key)
            if idNode is not None:
                child = idNode.firstChild().toText().data()
                # layer found
                if child == value:
                    return node
            i += 1
        return None

    def about_dialog(self):
        lang = ''
        try:
            locale = QSettings().value('locale/userLocale')
            if locale != None:
                lang = '#' + locale[:2]
        except:
            pass
        self.iface.openURL(ABOUT_FILE_URL + lang, False)

    def unload(self):
        self.iface.unregisterOptionsWidgetFactory(self.options_factory)
        self.iface.deregisterLocatorFilter(self.layer_locator_filter)
        self.clearMenu();
        
    def reloadMenu(self):
        self.clearMenu()
        self.createMenu()
    
    def clearMenu(self):
        # Remove the submenus
        for submenu in self.category_menus:
            if submenu:
                submenu.deleteLater()
        # remove the menu bar item
        if self.menu:
            self.menu.deleteLater()