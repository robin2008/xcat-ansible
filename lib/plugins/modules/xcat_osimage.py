#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# IBM(c) 2018 EPL license http://www.eclipse.org/legal/epl-v10.html
#

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: xcat_osimage
author:
- Bin Xu (@robin2008)
version_added: "0.1"
short_description:  Manage xCAT osimage resources
description:
    - Deploy xCAT managed OS image on remote hosts.
options:
    name:
        description:
            - Name of the OS image to manage.
    repo:
        description:
            - The server which serve the repository for installing packages.
        default: '127.0.0.1'
    excludes:
        description:
            - Whether the sub-actions (package, script) are disabled.
    osimage_dir:
        description:
            - Directory for OS image inventory
        default: /osimages
    osimage_src:
        description:
            - Inventory file where OS images are defined.
    script_root:
        description:
            - Directory which contains the scripts for OS image
        default: /install/postscripts
'''

EXAMPLES = '''
- name: Deploying xCAT osimage
  xcat_osimage:
    name: my-osimage
    osimage_src: /tmp/xcat.redhat.full.install.osimage.yaml
    repo: 10.3.5.20
    script_root: /install/xcat_clusters
'''

