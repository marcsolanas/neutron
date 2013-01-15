# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack LLC.
# All Rights Reserved.
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

from quantum.api.v2 import attributes as attr
from quantum.common import exceptions as qexception


class ExternalNetworkInUse(qexception.InUse):
    message = _("External network %(net_id)s cannot be updated to be made "
                "non-external, since it has existing gateway ports")


EXTERNAL = 'externalnet:external'
EXTENDED_ATTRIBUTES_2_0 = {
    'networks': {EXTERNAL: {'allow_post': True,
                            'allow_put': True,
                            'default': attr.ATTR_NOT_SPECIFIED,
                            'is_visible': True,
                            'convert_to': attr.convert_to_boolean,
                            'enforce_policy': True,
                            'required_by_policy': True}}}


class Ext_net(object):

    @classmethod
    def get_name(cls):
        return "Quantum external network"

    @classmethod
    def get_alias(cls):
        return "externalnet"

    @classmethod
    def get_description(cls):
        return ("Adds external network attribute to network resource.")

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/quantum/external_net/api/v1.0"

    @classmethod
    def get_updated(cls):
        return "2013-01-14T10:00:00-00:00"

    def get_extended_resources(self, version):
        if version == "2.0":
            return EXTENDED_ATTRIBUTES_2_0
        else:
            return {}
