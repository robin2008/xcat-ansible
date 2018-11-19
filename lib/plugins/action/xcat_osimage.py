#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# IBM(c) 2018 EPL license http://www.eclipse.org/legal/epl-v10.html
#

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os
import re
import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from ansible.errors import AnsibleError
from ansible.plugins.action import ActionBase
from ansible.utils.vars import merge_hash

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display

    display = Display()


class ActionModule(ActionBase):
    # Make sure runs once per play only
    # BYPASS_HOST_LOOP = True

    TRANSFERS_FILES = False

    VALID_ARGUMENTS = ['name', 'excludes', 'osimage_dir', 'osimage_src', 'repo', 'script_root']
    INCLUDE_PATTERN = re.compile(r'^#INCLUDE:(.*)#$')

    def _parse_pkglist(self, pkglist, other=False):

        pkgs_dict = dict()
        repo_dict = dict()
        display.v("Handling package list: %s" % pkglist)

        with open(pkglist) as f:
            for line in f.readlines():
                line = line.strip()
                if line.startswith('#'):
                    m = self.INCLUDE_PATTERN.match(line)
                    if not m:
                        continue
                    display.vvv("Including: %s" % m.group(1))
                    d1, d2 = self._parse_pkglist(m.group(1), other)
                    pkgs_dict.update(d1)
                    if other:
                        repo_dict.update(d2)
                else:
                    if other:
                        repo_dir = os.path.dirname(line) or ''
                        if repo_dir:
                            repo_dict[repo_dir] = 1

                    pkgname = os.path.basename(line)
                    if pkgname.startswith('@ '):
                        # it is a group, get rid of the space
                        pkgname = "@%s" % pkgname[1:].strip()
                    pkgs_dict[pkgname] = 1

        return pkgs_dict, repo_dict

    def _deploy_osimage(self, osimage, excludes=None, task_vars=None):

        module_rs = dict()
        osname = osimage.get('basic_attributes').get('osdistro')

        # Only support RHEL/CentOS now
        if not (osname.startswith('rhel') or osname.startswith('centos')):
            raise AnsibleError('%s is not supported yet.' % osname)

        # TODO: syncing files

        if 'package_selection' in osimage and 'package' not in excludes:

            # 1, parse defintion and get the possible repos
            repos = osimage['package_selection'].get('pkgdir')
            pkgs = dict()
            otherpkgs = dict()
            if 'otherpkgdir' in osimage['package_selection']:
                otherrepo_root = osimage['package_selection'].get('otherpkgdir')
                if otherrepo_root:
                    otherrepo_root = otherrepo_root[0]
                    otherrepos_dict = dict()
                    for rp in osimage['package_selection'].get('otherpkglist', []):
                        p, r = self._parse_pkglist(rp, other=True)
                        otherpkgs.update(p)
                        otherrepos_dict.update(r)

                    for key in otherrepos_dict.keys():
                        display.vv('Repository for other packages: %s' % key)
                        if key:
                            repos.append('%s/%s' % (otherrepo_root, key))
                        else:
                            repos.append(otherrepo_root)

            # 2, setup repositories
            repo_url = self._task.args.get('repo', '127.0.0.1')
            for i, repo in enumerate(repos):
                reponame = "%s-repo-%d" % (osname, i)
                module_args = dict(
                    name=reponame,
                    description='Automatically generated repo: %s' % reponame,
                    baseurl="http://%s%s" % (repo_url, repo),
                    enabled=True,
                    gpgcheck=False
                )
                rs = self._execute_module(module_name='yum_repository',
                                          module_args=module_args, task_vars=task_vars, become=True,
                                          )
                module_rs = merge_hash(module_rs, rs)

            for rp in osimage['package_selection'].get('pkglist', []):
                pkgs.update(self._parse_pkglist(rp)[0])

            # 3, install packages
            for pp in [pkgs, otherpkgs]:
                if not pp:
                    continue
                module_args = dict(
                    name=pp.keys(),
                )
                rs = self._execute_module(module_name='yum',
                                          module_args=module_args, task_vars=task_vars, become=True,
                                          )
                module_rs = merge_hash(module_rs, rs)

        if 'scripts' in osimage and 'script' not in excludes:
            script_root = self._task.args.get('script_root', '/install/postscripts')
            postscripts = osimage['scripts'].get('postscripts', [])
            scripts = list(postscripts)
            for scpt in osimage['scripts'].get('postbootscripts', []):
                if scpt not in postscripts:
                    scripts.append(scpt)

            for scpt in scripts:
                if not os.path.isabs(scpt):
                    scpt = os.path.join(script_root, scpt)
                display.vv('Executing: %s' % scpt)
                new_task = self._task.copy()
                new_task.args = dict(
                    _raw_params=scpt,
                )
                script_action = self._shared_loader_obj.action_loader.get('script',
                                                                          task=new_task,
                                                                          connection=self._connection,
                                                                          play_context=self._play_context,
                                                                          loader=self._loader,
                                                                          templar=self._templar,
                                                                          shared_loader_obj=self._shared_loader_obj)
                rs = script_action.run(task_vars=task_vars)
                module_rs = merge_hash(module_rs, rs)

        return module_rs

    def run(self, tmp=None, task_vars=None):
        del tmp  # tmp no longer has any effect

        if task_vars is None:
            task_vars = dict()
        result = super(ActionModule, self).run(task_vars=task_vars)

        if result.get('skipped'):
            return result

        # Validate arguments
        for arg in self._task.args:
            if arg not in self.VALID_ARGUMENTS:
                raise AnsibleError('Invalid option %s, it is not supported.' % arg)

        name = self._task.args.get('name')
        osimage_src = self._task.args.get('osimage_src', None)
        osimage_dir = self._task.args.get('osimage_dir', None)
        osimage_exc = self._task.args.get('excludes', '')

        osimage_dict = {}
        if osimage_src and osimage_dir:
            raise AnsibleError('Option osimage_src and osimage_dir cannot be used in the mean time.')

        elif osimage_src:
            if not os.path.exists(osimage_src):
                raise AnsibleError('%s does not exist.' % osimage_src)
            with open(osimage_src) as f:
                try:
                    osimage_dict = yaml.load(f, Loader=Loader)
                    assert osimage_dict
                    if 'osimage' in osimage_dict:
                        osimage_dict = osimage_dict['osimage']
                        assert osimage_dict
                except Exception:
                    raise AnsibleError(
                        "Error: failed to load file \"%s\", "
                        "please validate the file with 'yamllint %s'(for yaml format)"
                        % (osimage_src, osimage_src)
                    )

            if name:
                osimage = osimage_dict.get(name)
            else:
                # get the first one
                osimage = osimage_dict.values()[0]

            result = self._deploy_osimage(osimage, excludes=osimage_exc.split(','), task_vars=task_vars)

        return result
