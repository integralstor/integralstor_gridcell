# Don't try fancy stuff like debuginfo, which is useless on binary-only
# packages. Don't strip binary too
# Be sure buildpolicy set to do nothing
%define        __spec_install_post %{nil}
%define          debug_package %{nil}
%define        __os_install_post %{_dbpath}/brp-compress

Summary:       Creates a raidz zpool called as frzpool combining all disks except ssd. 
Name:          fractalio_zpool_creation
Version:       0.1
Release:       1
License:       Proprietary
Group:         Development/Tools
SOURCE0 :      %{name}-%{version}.tar.gz
URL:           http://www.fractalio.com/
REQUIRES:      zfs
BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root

%description
%{summary}

%prep
%setup -q

%build
# Empty section.

%install
rm -rf %{buildroot}
mkdir -p  %{buildroot}

# in builddir
cp -a * %{buildroot}

%post
/bin/sh /sbin/fractalio_zfs/01_zfs_format.sh

%postun
rm -f /sbin/fractalio_zfs/01_zfs_format.sh

%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
/sbin/*

%changelog
* Tue Jan 13 2015  Omkar Sharma MN <omkar@fractalio.com> 0.1-1
- Changes to 01_zfs_format.sh script
* Wed Dec 17 2014  Omkar Sharma MN <omkar@fractalio.com> 0.1-1
- First Build
