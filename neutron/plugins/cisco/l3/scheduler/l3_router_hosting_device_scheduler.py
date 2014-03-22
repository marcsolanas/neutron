# Copyright 2014 Cisco Systems, Inc.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# @author: Bob Melander, Cisco Systems, Inc.

from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy import or_

from neutron.openstack.common import log as logging
from neutron.plugins.cisco.l3.common import constants as cl3_const
from neutron.plugins.cisco.l3.db import hosting_device_manager_db
from neutron.plugins.cisco.l3.db import l3_models

LOG = logging.getLogger(__name__)


class L3RouterHostingDeviceScheduler(object):
    """Slot-aware scheduler of Neutron routers on hosting devices."""

    def schedule_router_on_hosting_device(self, plugin, context, r_hd_binding):
#    def _schedule(self, context, router, host_type=cl3_const.CSR1KV_HOST):
        """Schedules a Neutron router on a hosting device.

        Returns a tuple with selected hosting device and the number of
        routers it hosts, i.e., the number of slots that are occupied.
        """
        # mysql> SELECT *, COUNT(router_id) as num_alloc
        # FROM hostingdevices AS he
        # LEFT OUTER JOIN routerhostingentitybindings AS rhe
        # ON he.id=rhe.hosting_device_id
        # WHERE host_type='CSR1kv' AND admin_state_up=TRUE AND
        # (tenant_bound='t2' OR tenant_bound IS NULL)
        # GROUP BY id HAVING (num_alloc < 4)
        # ORDER BY created_at, num_alloc;
        max_routers = (self._dev_mgr.get_hosting_device_capacity(
            context, host_type) or {}).get('num_routers', 0)
        stmt = context.session.query(
            l3_models.HostingDevice,
            func.count(l3_models.RouterHostingDeviceBinding.router_id).
            label('num_alloc'))
        stmt = stmt.outerjoin(
            l3_models.RouterHostingDeviceBinding,
            l3_models.HostingDevice.id ==
            l3_models.RouterHostingDeviceBinding.hosting_device_id)
        stmt = stmt.filter(l3_models.HostingDevice.host_type == host_type,
                           l3_models.HostingDevice.admin_state_up == True)
        stmt = stmt.filter(
            or_(l3_models.HostingDevice.tenant_bound == None,
                l3_models.HostingDevice.tenant_bound == router['tenant_id']))
        stmt = stmt.group_by(l3_models.HostingDevice.id)
        if router.get('share_host', True):
            query = stmt.having(func.count(
                l3_models.RouterHostingDeviceBinding.router_id) < max_routers)
            query = query.order_by(
                l3_models.HostingDevice.created_at,
                func.count(l3_models.RouterHostingDeviceBinding.router_id))
        else:
            # TODO(bobmel): enhance so that tenant unbound hosting devices
            # that only host routers for this tenant are also included
            stmt = stmt.subquery()
            query = context.session.query(stmt)
            query = query.filter(or_(and_(stmt.c.tenant_bound == None,
                                          stmt.c.num_alloc == 0),
                                     and_(stmt.c.tenant_bound ==
                                          router['tenant_id'],
                                          stmt.c.num_alloc < max_routers)))
            query = query.order_by(stmt.c.created_at, stmt.c.num_alloc)
        candidate_hosting_devices = query.all()
        if len(candidate_hosting_devices) == 0:
            # Inform device manager that no suitable hosting device was found
            # so that it can take appropriate measures, e.g., spin up more
            # hosting device VMs.
            self._dev_mgr.report_hosting_device_shortage(
                context.elevated(), host_type, cl3_const.VM_CATEGORY)
            return
        else:
            # Choose the hosting device that has been running for the
            # longest time. If more than one exists, then pick the one
            # with the least occupied slots.
            return candidate_hosting_devices[0]

    def unschedule_router_from_hosting_device(self, plugin, context,
                                              r_hd_binding):
        pass

    #TODO(bobmel): change to get Device-aaS service plugin instead
    @property
    def _dev_mgr(self):
        return hosting_device_manager_db.HostingDeviceManager.get_instance()
