"""Manage a collection of Valves."""

# Copyright (C) 2013 Nippon Telegraph and Telephone Corporation.
# Copyright (C) 2015 Brad Cowie, Christopher Lorier and Joe Stringer.
# Copyright (C) 2015 Research and Education Advanced Network New Zealand Ltd.
# Copyright (C) 2015--2017 The Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from faucet.conf import InvalidConfigError
from faucet.config_parser_util import config_changed
from faucet.config_parser import dp_parser
from faucet.valve_util import stat_config_files


class ValvesManager(object):
    """Manage a collection of Valves."""

    valves = {} # type: dict
    config_hashes = None
    config_file_stats = None

    def __init__(self, logname, logger, metrics, notifier, bgp): # pylint: disable=too-many-arguments
        self.logname = logname
        self.logger = logger
        self.metrics = metrics
        self.notifier = notifier
        self.bgp = bgp

    def config_files_changed(self):
        """Return True if any config files changed."""
        changed = False
        if self.config_hashes:
            new_config_file_stats = stat_config_files(self.config_hashes)
            if self.config_file_stats:
                if new_config_file_stats != self.config_file_stats:
                    self.logger.info('config file(s) changed on disk')
                    changed = True
            self.config_file_stats = new_config_file_stats
        return changed

    def config_changed(self, config_file, new_config_file):
        """Return True if config file content actually changed."""
        return config_changed(config_file, new_config_file, self.config_hashes)

    def parse_configs(self, config_file):
        """Return parsed configs for Valves, or None."""
        try:
            new_config_hashes, new_dps = dp_parser(config_file, self.logname)
        except InvalidConfigError as err:
            self.logger.error('New config bad (%s) - rejecting', err)
            return None
        self.config_hashes = new_config_hashes
        return new_dps

    def update_metrics(self):
        """Update metrics in all Valves."""
        self.bgp.update_metrics()
        for valve in list(self.valves.values()):
            valve.update_metrics(self.metrics)

    def update_configs(self):
        """Update configs in all Valves."""
        self.bgp.reset(self.valves)
