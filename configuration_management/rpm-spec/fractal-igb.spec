# Don't try fancy stuff like debuginfo, which is useless on binary-only
# packages. Don't strip binary too
# Be sure buildpolicy set to do nothing
%define        __spec_install_post %{nil}
%define          debug_package %{nil}
%define        __os_install_post %{_dbpath}/brp-compress

Summary: Fractal IGB RPM
Name: fractal_igb
Version: 0.1
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
        echo "Fatal: fractal_igb-* module dependency, requires kernel-2.6.32-358.el6.x86_64.rpm"
        exit -1
fi

%post
grep -q "igb.ko" "/lib/modules/`uname -r`/modules.networking" || echo "igb.ko" >> "/lib/modules/`uname -r`/modules.networking"
depmod -a

%postun
sed -i '/igb\.ko/d' /lib/modules/`uname -r`/modules.networking
depmod -a

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
/lib/modules/2.6.32-358.el6.x86_64/extra/igb.ko

%changelog
* Tue Apr 08 2014 Harish Badrinath <harishbadrinath@gmail.com> 0.1
First Build

