# Don't try fancy stuff like debuginfo, which is useless on binary-only
# packages. Don't strip binary too
# Be sure buildpolicy set to do nothing
%define        __spec_install_post %{nil}
%define          debug_package %{nil}
%define        __os_install_post %{_dbpath}/brp-compress

Summary: Package to automagically configure fractal boxes to display gluster admin
Name: fractal_gluster_admin_config
Version: 0.1
Release: 1
License: Proprietary
Group: Development/Tools
SOURCE0 : %{name}-%{version}.tar.gz
URL: http://datalifecycle.com/
Requires:nginx,fractal_uwsgi
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root

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


%clean
rm -rf %{buildroot}

%post
echo "/usr/sbin/uwsgi --single-interpreter --emperor /etc/uwsgi/vassals/ --uid root --gid root" >> /etc/rc.local

%postun
if [[ "$1" == 0 ]]
then
	sed -i '/\/usr\/sbin\/uwsgi\ --single-interpreter\ --emperor\ \/etc\/uwsgi\/vassals\/\ --uid\ root\ --gid\ root/d' /etc/rc.local
fi

%files
%defattr(-,root,root,-)
%config(noreplace) /etc/nginx/sites-enabled/gluster_admin_nginx.conf
%config(noreplace) /etc/uwsgi/vassals/gluster_admin_uwsgi.ini

%changelog
* Thu Apr 03 2014  Harish Badrinath <harishbadrinath@gmail.com> 0.1-1
- First Build


