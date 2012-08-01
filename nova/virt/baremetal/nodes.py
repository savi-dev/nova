# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 University of Southern California / ISI
# Copyright (c) 2012 NTT DOCOMO, INC.
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
#

from nova import exception
from nova import flags
from nova.openstack.common import cfg
from nova.virt.baremetal import fake
from nova.virt.baremetal import ipmi
from nova.virt.baremetal import pxe
from nova.virt.baremetal import tilera
from nova.virt.baremetal import tilera_pdu

FLAGS = flags.FLAGS

baremetal_opts = [
    cfg.StrOpt('baremetal_driver',
               default='tilera',
               help='Bare-metal driver runs on'),
    cfg.StrOpt('power_manager',
               default='ipmi',
               help='power management method'),
    cfg.StrOpt('baremetal_tftp_root',
               default='/tftpboot',
               help='BareMetal compute node\'s tftp root path'),
    ]

FLAGS.register_opts(baremetal_opts)


def get_baremetal_nodes():
    d = FLAGS.baremetal_driver
    if d == 'tilera':
        return tilera.get_baremetal_nodes()
    elif d == 'pxe':
        return pxe.get_baremetal_nodes()
    elif d == 'fake':
        return fake.get_baremetal_nodes()
    else:
        raise exception.NovaException(_("Unknown baremetal driver %(d)s"))


def get_power_manager(node, **kwargs):
    d = FLAGS.power_manager
    if d == 'ipmi':
        return ipmi.get_power_manager(node, **kwargs)
    if d == 'tilera_pdu':
        return tilera_pdu.get_power_manager(node, **kwargs)
    if d == 'dummy':
        return ipmi.get_power_manager_dummy(node, **kwargs)
    else:
        raise exception.NovaException(_("Unknown power manager %(d)s"))
