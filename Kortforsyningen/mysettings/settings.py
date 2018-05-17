# -*- coding: utf-8 -*-
import os
from PyQt5.QtCore import QFileInfo, QObject
from qgis.PyQt import QtCore

from .qgissettingmanager import *
#CONFIG_FILE_URL ='https://apps2.kortforsyningen.dk/qgis_knap_config/Kortforsyningen/kf/kortforsyning_data.qlr'
CONFIG_FILE_URL ='https://labs.septima.dk/qgis-kf-knap/kortforsyning_data_token.qlr'

class Settings(SettingManager):
    settings_updated = QtCore.pyqtSignal()

    def __init__(self):
        SettingManager.__init__(self, 'Kortforsyningen')
        self.add_setting(String('token', Scope.Global, ''))
        self.add_setting(Bool('use_custom_file', Scope.Global, False))
        self.add_setting(String('custom_qlr_file', Scope.Global, ''))
        self.add_setting(Bool('only_background', Scope.Global, False))
        path = QFileInfo(os.path.realpath(__file__)).path()
        kf_path = path + '/kf/'
        if not os.path.exists(kf_path):
            os.makedirs(kf_path)
            
        self.add_setting(String('cache_path', Scope.Global, kf_path))
        self.add_setting(String('kf_qlr_url', Scope.Global, CONFIG_FILE_URL))
        
    def is_set(self):
        if self.value('token'):
            return True
        return False
    
    def emit_updated(self):
        self.settings_updated.emit()

