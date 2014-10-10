# Don't try fancy stuff like debuginfo, which is useless on binary-only
#packages. Don't strip binary tpp
#Be sure buildpolicy set to do nothing
%define     __spec_install_post %{nil}
%define       debug_package %{nil}
#define    __os_install_post %{_dbpath}/brp-compress

Summary: A iscsi target rpm package
Name: fractalistgt
Version: 1.0
Release: 1
License: Proprietary
Group: Development/Tools
SOURCE0 : %{name}-%{version}.tar.gz
URL: http://www.fractalio.com

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

%description
%{summary}

%prep
%setup -q

%build
#Empty section.

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}

# in builddir
cp -a * %{buildroot}

%clean
rm -rf %{buildroot}
%post
chmod a+x /etc/init.d/istgt


%files
%defattr(-,root,root,-)
%config(noreplace) /usr/local/%{_sysconfdir}/istgt/istgt.conf
%config(noreplace) /usr/local/%{_sysconfdir}/istgt/istgtcontrol.conf
%config(noreplace) /usr/local/%{_sysconfdir}/istgt/auth.conf
/etc/init.d/istgt
/usr/local/sbin*

%changelog
* Thu Mar 06 2014 Dhananjaya Gurusiddappa <info@fractalio.com> 1.0-1
- First Build

