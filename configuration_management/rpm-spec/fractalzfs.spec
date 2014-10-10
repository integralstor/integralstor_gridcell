# Don't try fancy stuff like debuginfo, which is useless on binary-only
# packages. Don't strip binary too
# Be sure buildpolicy set to do nothing
%define        __spec_install_post %{nil}
%define          debug_package %{nil}
%define        __os_install_post %{_dbpath}/brp-compress

Summary: Fractal ZFS RPM
Name: fractalzfs
Version: 0.6.2
Release: 1
License: Proprietary
Group: Development/Tools
SOURCE0 : %{name}-%{version}.tar.gz 
URL : http://fractal-io.com/

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

%description
%{summary}

%prep
%setup -q

%build
# Empty section

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}

# in builddir
cp -a * %{buildroot}

%pre
VAL1=`uname -r`
if [ "$VAL1" != "2.6.32-358.el6.x86_64" ]
then
        echo "Fatal: fractalzfs-* module dependency, requires kernel-2.6.32-358.el6.x86_64.rpm"
        exit -1
fi

%post
depmod -a
VAL2=`lsmod | grep zfs | wc -l`
if [[ $VAL2 != 6 ]]
then
	modprobe zfs
fi
chkconfig zfs on

%postun
depmod -a

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
/sbin/*
/lib64/*
/lib/*
/etc/init.d/zfs
/etc/zfs/*
/usr/*

%changelog
* Fri Mar 14 2014 Omkar Sharma MN Dhananjaya <mnomkar2008@gmail.com> 0.6.0
First Build

