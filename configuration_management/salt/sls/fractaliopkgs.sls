fractaliopkgs:
  pkgrepo.managed:
    - humanname: Fractal Packages
    - baseurl: http://10.1.1.200/fractaliolocal

smartmontools:
  pkg.installed:
    - skip_verify: True
    - refresh: True

glusterfs:
  pkg.installed:
    - skip_verify: True
    - refresh: True
 
glusterfs-fuse:
  pkg.installed:
    - skip_verify: True
    - refresh: True

glusterfs-server:
  pkg.installed:
    - skip_verify: True
    - refresh: True

ctdb:
  pkg.installed:
    - skip_verify: True
    - refresh: True

samba:
  pkg.installed:
    - skip_verify: True
    - refresh: True

samba-vfs-glusterfs:
  pkg.installed:
    - skip_verify: True
    - refresh: True

ipmitool:
  pkg.installed:
    - skip_verify: True
    - refresh: True

OpenIPMI:
  pkg.installed:
    - skip_verify: True
    - refresh: True

zfs:
  pkg.installed:
    - skip_verify: True
    - refresh: True

krb5-workstation:
  pkg.installed:
    - skip_verify: True
    - refresh: True

bind:
  pkg.installed:
    - skip_verify: True
    - refresh: True

ypbind:
  pkg.installed:
    - skip_verify: True
    - refresh: True

ypserv:
  pkg.installed:
    - skip_verify: True
    - refresh: True

ntp:
  pkg.installed:
    - skip_verify: True
    - refresh: True

uwsgi:
  pkg.installed:
    - skip_verify: True
    - refresh: True

nginx:
  pkg.installed:
    - skip_verify: True
    - refresh: True

perf:
  pkg.installed:
    - skip_verify: True
    - refresh: True

kexec-tools:
  pkg.installed:
    - skip_verify: True
    - refresh: True

fractalio_django:
  pkg.installed:
    - skip_verify: True
    - refresh: True

fractalio_integral_view:
  pkg.installed:
    - skip_verify: True
    - refresh: True

fractalio_zpool_creation:
  pkg.installed:
    - skip_verify: True
    - refresh: True

python-devel:
  pkg.installed:
    - skip_verify: True
    - refresh: True
