# Don't try fancy stuff like debuginfo, which is useless on binary-only
# packages. Don't strip binary too
# Be sure buildpolicy set to do nothing
%define        __spec_install_post %{nil}
%define          debug_package %{nil}
%define        __os_install_post %{_dbpath}/brp-compress

Summary: Fractal uWSGI RPM
Name: fractal_uwsgi
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

%post
chown uwsgi /var/run/uwsgi
chown uwsgi /var/log/uwsgi
chkconfig --add uwsgi
chkconfig uwsgi on
service uwsgi start

%preun
if [[ "$1" == 0 ]]
then
	chkconfig uwsgi off
	service uwsgi stop
	rm -rf /var/log/uwsgi/*
	rm -rf /var/run/uwsgi/*
fi

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
/etc/init.d/uwsgi
/usr/sbin/uwsgi
%dir /var/run/uwsgi
%dir /var/log/uwsgi
%dir /etc/uwsgi

%changelog
* Wed Apr 02 2014 Harish Badrinath <harishbadrinath@gmail.com> 0.1
First Build
