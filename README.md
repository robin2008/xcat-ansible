# xcat-ansible
Provide an ansible module to deploy xCAT OS image on servers which OS is installed.

### Prerequisites

Ansible is installed

```
yum install ansible
```

### Installing

Install the module and action plugin to corresponding directory

```
MODULE_LIBRARY=/usr/share/ansible/plugins
mkdir -p ${MODULE_LIBRARY} && cp -rf lib/plugins/* ${MODULE_LIBRARY}
```

And run `ansible-doc` to see if the module information could be shown.

```
ansible-doc xcat_osimage
```

## Running the tests

1, Define ansible inventory
```
cat /etc/ansible/hosts
[xcat]
10.3.5.29
10.3.5.30
```

2, Get the xcat osimage inventory
```
osimage:
  xcat.redhat.full.install:
    basic_attributes:
      arch: ppc64le
      distribution: rhels7.5
      osdistro: rhels7.5-ppc64le
      osname: Linux
    imagetype: linux
    package_selection:
      otherpkgdir:
      - /install/REPO/software
      otherpkglist:
      - /install/xcat_clusters/osimage/rhels/common/otherpkglist/epel.otherpkglist
      - /install/xcat_clusters/osimage/rhels/common/otherpkglist/gsa.otherpkglist
      pkgdir:
      - /install/REPO/os/rhels/7.5/rhels7.5-ga/ppc64le
      - /install/REPO/os/rhels/7.5/kernel-3.10.0-862.14.4.el7/ppc64le
      - /install/REPO/software/nvidia/cuda-core/9.2.148-1-396.47/repo/ppc64le
      - /install/REPO/software/nvidia/cuda-dep/repo/ppc64le
      pkglist:
      - /install/xcat_clusters/osimage/rhels/common/pkglist/all.df.pkglist
    provision_mode: install
    role: compute
    scripts:
      postbootscripts:
      - custom.ps/nvidia/postinstall/cuda_power9_setup
      postscripts:
      - custom.ps/mellanox/mlnxofed_ib_install
        -p /install/REPO/software/mellanox/ofed/iso/redhat/7.5/ppc64le/MLNX_OFED_LINUX-4.3-4.0.7.1-rhel7.5-ppc64le.iso
        -m --add-kernel-support --force -end-
      - custom.ps/checknode
    template: /install/xcat_clusters/osimage/rhels/xcat/install/rhels7.tmpl
schema_version: '1.0'

#Version 2.14.2 (git commit dc2ea9014d1d4e7932104159417f6335cea5fac7, built Mon Jul  2 06:15:47 EDT 2018)

```

3, run

```
ansible 10.3.5.30 -m xcat_osimage -a "osimage_src=/install/xcat_clusters/osimage/rhels/xcat/xcat.redhat.full.install.osimage.yaml repo=10.3.5.20 script_root=/install/xcat_clusters"
```

## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/robin2008/xyz) for details on our code of conduct, and the process for submitting pull requests to us.

## License

This project is licensed under the EPL License - see the [LICENSE.md](LICENSE.md) file for details

