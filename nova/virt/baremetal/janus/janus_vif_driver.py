# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2013, The SAVI Project.
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

from webob import exc

from nova import exception
from nova import flags
from nova.openstack.common import log as logging
from nova.openstack.common import cfg

from nova.virt.baremetal import vif_driver

FLAGS = flags.FLAGS

LOG = logging.getLogger(__name__)

# For connecting with Janus API
import httplib
from janus.network.network import JanusNetworkDriver

janus_libvirt_ovs_driver_opt = cfg.StrOpt('libvirt_ovs_janus_api_host',
                                        default='127.0.0.1:8091',
                                        help='OpenFlow Janus REST API host:port')
FLAGS.register_opt(janus_libvirt_ovs_driver_opt)

class JanusVIFDriver(vif_driver.BareMetalVIFDriver):
    def __init__(self, **kwargs):
        super(JanusVIFDriver, self).__init__()
        LOG.debug('Janus REST host %s', FLAGS.libvirt_ovs_janus_api_host)
        host, port = FLAGS.libvirt_ovs_janus_api_host.split(':')
        self.client = JanusNetworkDriver(host, port)

    def _after_plug(self, instance, network, mapping, pif):
        dpid = pif['datapath_id']
        if dpid.find("0x") == 0:
            dpid = dpid[2:]

        # Register MAC with network first, then try to register port
        try:
            self.client.addMAC(network['id'], mapping['mac'])
            self.client.createPort(network['id'], dpid, pif['port_no'])
        except httplib.HTTPException as e:
            res = e.args[0]
            if res.status != httplib.CONFLICT:
                raise

    def _after_unplug(self, instance, network, mapping, pif):
        dpid = pif['datapath_id']
        if dpid.find("0x") == 0:
            dpid = dpid[2:]

        try:
            self.client.deletePort(network['id'], dpid, pif['port_no'])
            self.client.delMAC(network['id'], mapping['mac'])
        except httplib.HTTPException as e:
            res = e.args[0]
            if res.status != httplib.NOT_FOUND:
                raise

