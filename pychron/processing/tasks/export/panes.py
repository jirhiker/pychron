#===============================================================================
# Copyright 2014 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#============= enthought library imports =======================
from pyface.tasks.traits_dock_pane import TraitsDockPane
from pyface.tasks.traits_task_pane import TraitsTaskPane
from traitsui.api import View, UItem, TabularEditor, HGroup

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.envisage.tasks.pane_helpers import icon_button_editor


class ExportAnalysisAdapter(TabularAdapter):
    columns = [('Sample', 'sample'), ('RunID', 'record_id'), ('Tag', 'tag')]
    font = 'modern 10'


class ExportCentralPane(TraitsTaskPane):
    def traits_view(self):
        editor = TabularEditor(adapter=ExportAnalysisAdapter(),
                               operations=['delete'],
                               multi_select=True)
        v = View(
            HGroup(icon_button_editor('append_button', 'add'),
                   icon_button_editor('replace_button', 'arrow_refresh')),
            UItem('export_analyses', editor=editor))
        return v


class DestinationPane(TraitsDockPane):
    name = 'Destination'
    id = 'pychron.export.destination'

    def traits_view(self):
        v = View(
            UItem('kind'),
            UItem('object.exporter.destination', style='custom'))
        return v

    #============= EOF =============================================

