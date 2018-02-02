# -*- coding: utf-8 -*-
from qgis.core import (QgsLocatorFilter,
                       QgsLocatorResult)

class LayerLocatorFilter(QgsLocatorFilter):

    def __init__(self, parent=None):
        super(LayerLocatorFilter, self).__init__(parent)
        self.searchable_layers = []
            
    def name(self):
        return 'kortforsyningen'

    def displayName(self):
        return self.tr('Kortforsyningen')

    def priority(self):
        return QgsLocatorFilter.Low

    def prefix(self):
        return 'kortforsyningen'

    def set_searchable_layers(self, searchable_layers):
        self.searchable_layers = searchable_layers
        i=0
        self.actions = []
        for layer in self.searchable_layers:
            self.actions.append(layer['action'])
            layer['actionindex'] = i
            i = i+1
            self.make_searchable(layer)
            layer['title'] += ' (' + layer['category'] + ', Kortforsyningen)'

    def make_searchable(self, layer):
        search_string = layer['category'] + ' ' + layer['title']
        search_string = search_string.replace('/', ' ')
        search_string = search_string.replace('-', ' ')
        search_string = search_string.replace('navn', ' ')
        layer['searchstring'] = ' ' + search_string.lower()

    def fetchResults(self, string, context, feedback):
        search_terms = string.lower().split()
        term_count = len(search_terms)
        for layer in self.searchable_layers:
            layer['points'] = 0
            for term in search_terms:
                if layer['searchstring'].find(' ' + term) > -1:
                    layer['points'] += 1
            if layer['points'] == term_count:
                result = QgsLocatorResult()
                result.filter = self
                result.displayString = layer['title']
                #result.icon = a.icon()
                result.userData = layer['actionindex']
                result.score = 0
                
                self.resultFetched.emit(result)

    def triggerResult(self, result):
         self.actions[result.userData].activate(0)

