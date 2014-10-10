# Don't try fancy stuff like debuginfo, which is useless on binary-only
# packages. Don't strip binary too
# Be sure buildpolicy set to do nothing
%define        __spec_install_post %{nil}
%define          debug_package %{nil}
%define        __os_install_post %{_dbpath}/brp-compress

Summary: Fractal-Base package 
Name: fractal_base
Version: 0.1
Release: 1
License: Proprietary
Group: Development/Tools
SOURCE0 : %{name}-%{version}.tar.gz
URL: http://datalifecycle.com/

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

%preun
rm -rf /config/*

%files
%defattr(-,root,root,-)
%dir /config/
/opt/fractal/*

%changelog
* Tue Nov 19 2013  Harish Badrinath <harishbadrinath@gmail.com> 0.1-1
- First Build


