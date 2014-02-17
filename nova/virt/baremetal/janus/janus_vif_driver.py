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
from nova.openstack.common import log as logging

from oslo.config import cfg

from nova.virt.baremetal import vif_driver

CONF = cfg.CONF

LOG = logging.getLogger(__name__)

# For connecting with Janus API
import httplib
from janus.network.network import JanusNetworkDriver

janus_libvirt_ovs_driver_opt = cfg.StrOpt('libvirt_ovs_janus_api_host',
                                        default='127.0.0.1:8091',
                                        help='OpenFlow Janus REST API host:port')
CONF.register_opt(janus_libvirt_ovs_driver_opt)

class JanusVIFDriver(vif_driver.BareMetalVIFDriver):
    def __init__(self, **kwargs):
        super(JanusVIFDriver, self).__init__()
        LOG.debug('Janus REST host %s', FLAGS.libvirt_ovs_janus_api_host)
        host, port = CONF.libvirt_ovs_janus_api_host.split(':')
        self.client = JanusNetworkDriver(host, port)

    def _after_plug(self, instance, vif, pif):
        datapath_id = dpid = pif['datapath_id']
        if dpid.find("0x") == 0:
            dpid = dpid[2:]
        
        mac_address = vif.get('address', None)      
        net = vif.get('network')
        subnets = net.get('subnets')
        network_id = net['id']  
        of_port_no = pif['port_no']
        # Register MAC with network first, then try to register port
        try:
            self.client.createPort(network_id, datapath_id, of_port_no, migrating = False)
            self.client.addMAC(network_id, mac_address)
            for subnet in subnets:
                ips = subnet['ips']
                for ip in ips:
                    ip_address = ip['address']
                    self.client.ip_mac_mapping(network_id, datapath_id,
                                           mac_address, ip_address,
                                           of_port_no,
                                           migrating = False)

        except httplib.HTTPException as e:
            res = e.args[0]
            if res.status != httplib.CONFLICT:
                raise

    def _after_unplug(self, instance, vif, pif):
        datapath_id = dpid = pif['datapath_id']
        if dpid.find("0x") == 0:
            dpid = dpid[2:]

        mac_address = vif.get('address', None)      
        net = vif.get('network')
        subnets = net.get('subnets')
        network_id = net['id']  
        of_port_no = pif['port_no']
        try:
            self.client.deletePort(network_id, datapath_id, of_port_no)
            # To do: Un-mapping of ip to mac?
        except httplib.HTTPException as e:
            res = e.args[0]
            if res.status != httplib.NOT_FOUND:
                traceback.print_exc()
                raise
        try:
            self.client.delMAC(network_id, mac_address)
        except httplib.HTTPException as e:
            res = e.args[0]
            if res.status != httplib.NOT_FOUND:
                traceback.print_exc()
                raise
