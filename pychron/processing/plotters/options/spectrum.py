#===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import Str, Int, Property, Bool, Enum, Float, Color, Range
from traitsui.api import Item, Group, HGroup, UItem, EnumEditor, spring, VGroup

#============= standard library imports ========================
import re
#============= local library imports  ==========================

from pychron.processing.plotters.options.age import AgeOptions
from pychron.processing.plotters.options.option import SpectrumPlotOptions
from pychron.pychron_constants import ERROR_TYPES

plat_regex = re.compile(r'\w{1,2}-{1}\w{1,2}$')


class SpectrumOptions(AgeOptions):
    step_nsigma = Int(2)
    plot_option_klass = SpectrumPlotOptions

    include_j_error_in_plateau = Bool(True)
    plateau_age_error_kind = Enum(*ERROR_TYPES)
    force_plateau = Bool(False)
    plateau_steps = Property(Str)
    _plateau_steps = Str
    plot_option_name = 'Age'
    display_extract_value = Bool(False)
    display_step = Bool(False)
    display_plateau_info = Bool(True)
    display_integrated_info = Bool(True)
    plateau_sig_figs = Int

    plateau_font_size = Enum(6, 7, 8, 10, 11, 12, 14, 15, 18, 24, 28, 32)
    integrated_font_size = Enum(6, 7, 8, 10, 11, 12, 14, 15, 18, 24, 28, 32)
    step_label_font_size = Enum(6, 7, 8, 10, 11, 12, 14, 15, 18, 24, 28, 32)
    envelope_alpha = Range(0, 100, style='simple')
    center_line_style = Enum('solid', 'dash', 'dot dash', 'dot', 'long dash')
    extend_plateau_end_caps = Bool(True)
    plateau_line_width = Float
    plateau_line_color = Color
    plateau_method = Enum('Fleck 1977', 'Mahon 1996')
    error_calc_method = Property

    def _get_error_calc_method(self):
        return self.plateau_age_error_kind

    def _set_error_calc_method(self, v):
        self.plateau_age_error_kind = v

    # def _get_info_group(self):
    #     g = VGroup(
    #         HGroup(Item('show_info', label='Display Info'),
    #                Item('show_mean_info', label='Mean', enabled_when='show_info'),
    #                Item('show_error_type_info', label='Error Type', enabled_when='show_info')
    #         ),
    #         HGroup(Item('display_step'), Item('display_extract_value'),
    #                Item('display_plateau_info')),
    #         show_border=True, label='Info')

    # return g

    def _get_plateau_steps(self):
        return self._plateau_steps

    def _set_plateau_steps(self, v):
        self._plateau_steps = v

    def _validate_plateau_steps(self, v):
        if plat_regex.match(v):
            s, e = v.split('-')
            try:
                assert s < e
                return v
            except AssertionError:
                pass

    def _get_dump_attrs(self):
        attrs = super(SpectrumOptions, self)._get_dump_attrs()
        return attrs + ['step_nsigma',
                        'force_plateau',
                        'display_extract_value',
                        'display_step',
                        'display_plateau_info',
                        'display_integrated_info',
                        'plateau_font_size',
                        'integrated_font_size',
                        'step_label_font_size',
                        'envelope_alpha',
                        '_plateau_steps', 'center_line_style',
                        'extend_plateau_end_caps',
                        'plateau_line_width', 'plateau_line_color',
                        'include_j_error_in_plateau',
                        'plateau_age_error_kind',
                        'plateau_sig_figs',
                        # 'plateau_error_sig_figs',
                        'plateau_method']

    def _get_groups(self):

        plat_grp = Group(
            Item('plateau_method', label='Method'),
            Item('center_line_style'),
            Item('extend_plateau_end_caps'),
            Item('plateau_line_width'),
            Item('plateau_line_color'),
            Item('nsigma'),
            Item('plateau_age_error_kind',
                 width=-100,
                 label='Error Type'),
            Item('include_j_error_in_plateau', label='Include J Error'),
            HGroup(
                Item('force_plateau',
                     tooltip='Force a plateau over provided steps'),
                UItem('plateau_steps',
                      enabled_when='force_plateau',
                      tooltip='Enter start and end steps. e.g A-C ')),
            show_border=True,
            label='Plateau')

        error_grp = Group(HGroup(Item('step_nsigma',
                                      editor=EnumEditor(values=[1, 2, 3]),
                                      tooltip='Set the size of the error envelope in standard deviations',
                                      label='N. Sigma'),
                                 Item('envelope_alpha',
                                      label='Opacity',
                                      tooltip='Set the opacity (alpha-value) for the error envelope')),
                          show_border=True,
                          label='Error Envelope')

        display_grp = Group(HGroup(UItem('show_info',
                                         tooltip='Show general info in the upper right corner'),
                                   label='General'),
                            HGroup(Item('display_step', label='Step'),
                                   Item('display_extract_value', label='Power/Temp'),
                                   spring,
                                   Item('step_label_font_size', label='Size'),
                                   label='Labels'),
                            VGroup(HGroup(UItem('display_plateau_info',
                                                tooltip='Display plateau info'),
                                          spring,
                                          Item('plateau_font_size', label='Size',
                                               enabled_when='display_plateau_info')),
                                   HGroup(Item('plateau_sig_figs', label='Age'),
                                          # Item('plateau_error_sig_figs', label='Error'),
                                          show_border=True, label='SigFigs'),
                                   label='Plateau'),
                            HGroup(UItem('display_integrated_info',
                                         tooltip='Display integrated age info'),
                                   spring,
                                   Item('integrated_font_size', label='Size',
                                        enabled_when='display_integrated_info'),
                                   label='Integrated'),
                            show_border=True,
                            label='Display')
        g = Group(
            self._get_title_group(),
            plat_grp,
            error_grp,
            display_grp,
            # self._get_info_group(),
            label='Options')

        label_grp = VGroup(self._get_x_axis_group(),
                           self._get_y_axis_group(),
                           label='Fonts')
        return g, label_grp


#============= EOF =============================================
