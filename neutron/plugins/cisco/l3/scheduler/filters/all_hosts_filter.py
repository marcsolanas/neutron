from neutron.plugins.cisco.l3.scheduler.filters import filters_base

__author__ = 'nalle'


class AllHostsFilter(filters_base.BaseHostFilter):

    run_filter_once_per_request = True

    def host_passes(self, host_state, resource):
        return True