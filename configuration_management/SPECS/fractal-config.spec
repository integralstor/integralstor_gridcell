# Don't try fancy stuff like debuginfo, which is useless on binary-only
# packages. Don't strip binary too
# Be sure buildpolicy set to do nothing
%define        __spec_install_post %{nil}
%define          debug_package %{nil}
%define        __os_install_post %{_dbpath}/brp-compress

Summary: Fractal-Config package 
Name: fractal_config
Version: 0.1
Release: 1
License: Proprietary
Group: Development/Tools
SOURCE0 : %{name}-%{version}.tar.gz
URL: http://datalifecycle.com/

BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root
Requires(postun): sed
Requires(pre): cronie 

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
echo "/sbin/fractalSetup.sh" >> /etc/rc.local
echo "modprobe ipmi_devintf" >> /etc/rc.modules
chmod a+x /etc/rc.modules
chmod a+x /sbin/fractalSetup.sh
chmod a+x /etc/fractalSetupScripts/*
(crontab -l 2>/dev/null; echo "*/1 * * * * /opt/fractal/bin/runscript > /tmp/out >> /tmp/err") | crontab - 


%postun
sed -i '/\/sbin\/fractalSetup.sh/d' /etc/rc.local
sed -i '/modprobe\ ipmi_devintf/d' /etc/rc.modules 

%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
/sbin/fractalSetup.sh
/etc/fractalSetupScripts/*

%changelog
* Wed Nov 27 2013  Harish Badrinath <harishbadrinath@gmail.com> 0.1-1
- First Build


