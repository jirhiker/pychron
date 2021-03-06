# ===============================================================================
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
from traits.api import Instance, List, on_trait_change, Bool, Event
#============= standard library imports ========================
from itertools import groupby
#============= local library imports  ==========================
from pychron.experiment.queue.experiment_queue import ExperimentQueue
from pychron.experiment.factory import ExperimentFactory
from pychron.experiment.utilities.aliquot_numbering import renumber_aliquots
from pychron.experiment.stats import StatsGroup
from pychron.experiment.experiment_executor import ExperimentExecutor
from pychron.experiment.utilities.identifier import convert_identifier
from pychron.database.isotope_database_manager import IsotopeDatabaseManager


class Experimentor(IsotopeDatabaseManager):
    experiment_factory = Instance(ExperimentFactory)
    experiment_queue = Instance(ExperimentQueue)
    executor = Instance(ExperimentExecutor)
    experiment_queues = List
    stats = Instance(StatsGroup, ())

    mode = None
    # unique_executor_db = False

    save_enabled = Bool

    #===========================================================================
    # permissions
    #===========================================================================
    #    max_allowable_runs = 10000
    #    can_edit_scripts = True
    #    _last_ver_time = None
    #    _ver_timeout = 10

    #===========================================================================
    # task events
    #===========================================================================
    execute_event = Event

    activate_editor_event = Event
    save_event = Event
    #    clear_display_event = Event
    def reset_run_generator(self):
        if self.executor.isAlive():
            self.debug('Queue modified. Reset run generator')
            #             self.executor.queue_modified = True
            self.executor.set_queue_modified()

    def refresh_executable(self, qs=None):
        if qs is None:
            qs = self.experiment_queues

        if self.executor.isAlive():
            qs = (self.executor.experiment_queue, )

        self.executor.executable = all([ei.is_executable() for ei in qs])
        self.debug('setting executable {}'.format(self.executor.executable))

    def update_queues(self):
        self._update_queues()

    # def test_connections(self):
    #     if not self.db:
    #         return
    #
    #     if not self.db.connect():
    #         self.warning_dialog('Failed connecting to database. {}'.format(self.db.url))
    #         return
    #
    #     return True

    def update_info(self):
        self._update()

    #===============================================================================
    # info update
    #===============================================================================
    def _get_all_runs(self, queues=None):
        if queues is None:
            queues = self.experiment_queues

        return [ai for ei in queues
                for ai in ei.executed_runs + ei.automated_runs
                if ai.executable and not ai.skip]

    def _get_all_automated_runs(self, qs=None):
        if qs is None:
            qs = self.experiment_queues

        return [ai for ei in qs
                for ai in ei.automated_runs
                if ai.executable]

    def _update(self, queues=None):

        self.debug('update runs')
        if queues is None:
            queues = self.experiment_queues

        queues = [qi for qi in queues if qi.is_updateable()]
        if not queues:
            return

        self.debug('updating stats')
        self.stats.calculate()
        self.refresh_executable(queues)

        self.debug('executor executable {}'.format(self.executor.executable))
        self.debug('stats calculated')

        ans = self._get_all_runs(queues)
        self.stats.nruns = len(ans)

        self.debug('get all runs n={}'.format(len(ans)))

        for qi in self.experiment_queues:
            aruns = self._get_all_automated_runs([qi])
            renumber_aliquots(aruns)

        self._set_analysis_metatata()

        self.debug('info updated')
        for qi in queues:
            qi.refresh_table_needed = True

    def _get_labnumber(self, ln):
        """
           return gen_labtable object
        """
        db = self.db
        ln = convert_identifier(ln)
        dbln = db.get_labnumber(ln)

        return dbln

    def _group_analyses(self, ans, exclude=None):
        """
            sort, group and filter by labnumber
        """
        if exclude is None:
            exclude = tuple()
        key = lambda x: x.labnumber

        return ((ln, group) for ln, group in groupby(sorted(ans, key=key), key)
                if ln not in exclude)

    def _get_analysis_info(self, li):
        dbln = self.db.get_labnumber(li)
        if not dbln:
            return None
        else:
            project, sample, material, irradiation = '', '', '', ''
            sample = dbln.sample
            if sample:
                if sample.project:
                    project = sample.project.name

                if sample.material:
                    material = sample.material.name
                sample = sample.name

            dbpos = dbln.irradiation_position
            if dbpos:
                level = dbpos.level
                irradiation = '{} {}:{}'.format(level.irradiation.name,
                                                level.name, dbpos.position)

        return project, sample, material, irradiation

    def _set_analysis_metatata(self):
        cache = dict()
        db = self.db
        aruns = self._get_all_automated_runs()

        with db.session_ctx():
            for ai in aruns:
                if ai.skip:
                    continue

                ln = ai.labnumber
                if ln == 'dg':
                    continue

                # is run in cache
                if not ln in cache:
                    info = self._get_analysis_info(ln)
                    if not info:
                        cache[ln] = dict(identifier_error=True)
                    else:
                        project, sample, material, irrad = info

                        cache[ln] = dict(project=project, sample=sample,
                                         material=material,
                                         irradiation=irrad, identifier_error=False)

                ai.trait_set(**cache[ln])

    def execute_queues(self, queues):
        self.debug('setup executor')

        names = ','.join([e.name for e in queues])
        self.debug('queues: n={}, names={}'.format(len(queues), names))

        self.executor.trait_set(
            experiment_queues=queues,
            experiment_queue=queues[0],
            stats=self.stats)

        return self.executor.execute()

    #===============================================================================
    # handlers
    #===============================================================================
    @on_trait_change('executor:experiment_queue')
    def _activate_editor(self, eq):
        self.activate_editor_event = id(eq)

    @on_trait_change('executor:stop_button')
    def _stop(self):
        self.debug('%%%%%%%%%%%%%%%%%% Stop fired')
        if self.executor.isAlive():
            self.info('stop execution')
            '''
                if the executor is delaying then stop but dont cancel
                otherwise cancel
            '''
            self.executor.stop()

    @on_trait_change('executor:start_button')
    def _execute(self):
        """
            trigger the experiment task to assemble current queues.
            the queues are then passed back to execute_queues()
        """
        self.debug('%%%%%%%%%%%%%%%%%% Start fired')
        if not self.executor.isAlive():
            self.debug('%%%%%%%%%%%%%%%%%% Execute event true')
            self.execute_event = True

    @on_trait_change('experiment_queues[]')
    def _update_queues(self):
        qs = self.experiment_queues
        self.stats.experiment_queues = qs
        # try:
        #     self.stats.calculate()
        # except PyscriptError, e:
        #     self.warning_dialog(str(e))
        # self.refresh_executable(qs)
        #
        # self.debug('executor executable {}'.format(self.executor.executable))

    @on_trait_change('experiment_factory:run_factory:changed')
    def _queue_dirty(self):
        self.experiment_queue.changed = True

    #         executor = self.executor
    #         executor.executable = False

    #         if executor.isAlive():
    #             executor.prev_end_at_run_completion = executor.end_at_run_completion
    #             executor.end_at_run_completion = True
    #             executor.changed_flag = True

    @on_trait_change('experiment_queue:dclicked')
    def _dclicked_changed(self, new):
        self.experiment_factory.run_factory.edit_mode = True
        self._set_factory_runs(self.experiment_queue.selected)

    # @on_trait_change('executor:non_clear_update_needed')
    # def _refresh2(self):
    #     self.debug('non clear update needed fired')
    #     self.update_info()

    @on_trait_change('experiment_factory:run_factory:update_info_needed')
    def _refresh3(self):
        self.debug('update info needed fired')
        self.update_info()

    @on_trait_change('executor:queue_modified')
    def _refresh5(self, new):
        if new:
            self.debug('queue modified fired')
            self.update_info()

    @on_trait_change('experiment_factory:run_factory:refresh_table_needed')
    def _refresh4(self):
        for qi in self.experiment_queues:
            qi.refresh_table_needed = True

    @on_trait_change('experiment_factory:save_button')
    def _save_update(self):
        self.save_event = True

    def _experiment_queue_changed(self, eq):
        if eq:
            self.experiment_factory.queue = eq
            self.experiment_factory.sync_queue_meta()


            # for a in ('username', 'mass_spectrometer', 'extract_device',
            #           'load_name',
            #           'delay_before_analyses', 'delay_between_analyses'):
            #     qf.sync_
            #     if not self._sync_queue_to_factory(eq, qf, a):
            #         self._sync_factory_to_queue(eq, qf, a)
            # fv = getattr(eq, a)
            #sync queue values to experiment factory
            # if fv is not None:
            #     if isinstance(v, str):
            #         v = v.strip()
            #         if v:
            #             self._sync_queue_to_factory(qf, a, v)
            #         else:
            #             self._sync_factory_to_queue(eq, a, v)
            # else:
            #     setattr(qf, a, v)
            #sync experiment factory values to queue
            # else:

    @on_trait_change('experiment_queue:refresh_info_needed')
    def _handle_refresh(self):
        self.update_info()

    @on_trait_change('experiment_queue:selected')
    def _selected_changed(self, new):
        ef = self.experiment_factory
        rf = ef.run_factory
        rf.edit_mode = False
        if new:

            self._set_factory_runs(new)

            a = new[-1]
            if not a.skip:
                self.stats.calculate_at(a)
                self.stats.calculate()

    @on_trait_change('experiment_factory:queue_factory:delay_between_analyses')
    def handle_delay_between_analyses(self, new):
        if self.executor.isAlive():
            self.executor.experiment_queue.delay_between_analyses = new

    def _set_factory_runs(self, new):
        ef = self.experiment_factory
        rf = ef.run_factory
        rf.special_labnumber = 'Special Labnumber'

        rf.suppress_update = True
        rf.set_selected_runs(new)

    #===============================================================================
    # property get/set
    #===============================================================================
    #     def _get_title(self):
    #         if self.experiment_queue:
    #             return 'Experiment {}'.format(self.experiment_queue.name)

    def _executor_factory(self):
        p1 = 'pychron.extraction_line.extraction_line_manager.ExtractionLineManager'
        p2 = 'pychron.spectrometer.base_spectrometer_manager.BaseSpectrometerManager'
        p3 = 'pychron.spectrometer.ion_optics_manager.IonOpticsManager'
        kw = dict()
        if self.application:
            spec = self.application.get_service(p2)
            kw = dict(extraction_line_manager=self.application.get_service(p1),
                      spectrometer_manager=spec,
                      ion_optics_manager=self.application.get_service(p3), )

        # if not self.unique_executor_db:
        #     kw['db'] = self.db
        #     kw['connect'] = False

        e = ExperimentExecutor(
            mode=self.mode,
            application=self.application,
            **kw)
        e.bind_preferences()

        return e

    #===============================================================================
    # defaults
    #===============================================================================
    def _executor_default(self):
        return self._executor_factory()

    def _experiment_factory_default(self):
        dms = 'Spectrometer'
        if self.application:
            p2 = 'pychron.spectrometer.base_spectrometer_manager.BaseSpectrometerManager'
            spec = self.application.get_service(p2)
            if spec:
                dms = spec.name.capitalize()

        e = ExperimentFactory(application=self.application,
                              db=self.db)
        e.default_mass_spectrometer = dms

        return e

#============= EOF =============================================
