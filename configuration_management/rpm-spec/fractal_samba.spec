# Don't try fancy stuff like debuginfo, which is useless on binary-only
# packages. Don't strip binary too
# Be sure buildpolicy set to do nothing
%define        __spec_install_post %{nil}
%define          debug_package %{nil}
%define        __os_install_post %{_dbpath}/brp-compress

Summary: fractal samba 
Name: fractal_samba 
Version: 0.1
Release: 1
License: Proprietary 
Group: Development/Tools
SOURCE0 : %{name}-%{version}.tar.gz
URL: http://www.datalifecycle.com/
Requires:glusterfs-libs
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

%description
%{summary}

%prep
%setup -q

%post
chmod a+x /etc/init.d/samba
chkconfig samba on

%build
# Empty section.

%install
rm -rf %{buildroot}
mkdir -p  %{buildroot}

# in builddir
cp -a * %{buildroot}


%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
/etc/rc.d/init.d/samba
/usr/local/samba/*

%changelog
* Mon Dec 16 2013  Harish Badrinath <harishbadrinath@gmail.com> 0.1
- First Build

