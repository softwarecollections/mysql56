%{!?scl:%global scl mariadb55}
%scl_package %scl

Summary: Package that installs %scl
Name: %scl_name
Version: 1
Release: 2%{?dist}
BuildArch: noarch
License: GPLv2+
Group: Applications/File
Requires: scl-utils
Requires: %{scl_prefix}mariadb-server
%if 0%{?rhel} >= 6
Requires(post): policycoreutils-python
%endif
BuildRequires: scl-utils-build
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
This is the main package for %scl Software Collection.

%package runtime
Summary: Package that handles %scl Software Collection.
Group: Applications/File
Requires: scl-utils

%description runtime
Package shipping essential scripts to work with %scl Software Collection.

%package build
Summary: Package shipping basic build configuration
Group: Applications/File

%description build
Package shipping essential configuration macros to build %scl Software Collection.

%prep
%setup -c -T

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_scl_scripts}/root

# During the build of this package, we don't know which architecture it is 
# going to be used on, so if we build on 64-bit system and use it on 32-bit, 
# the %{_libdir} would stay expanded to '.../lib64'. This way we determine 
# architecture everytime the 'scl enable ...' is run and set the 
# LD_LIBRARY_PATH accordingly
cat >> %{buildroot}%{_scl_scripts}/enable << EOF
export PATH=%{_bindir}:\$PATH
export LIBRARY_PATH=%{_scl_root}`rpm -E %%_libdir`:\$LIBRARY_PATH
export LD_LIBRARY_PATH=%{_scl_root}`rpm -E %%_libdir`:\$LD_LIBRARY_PATH
EOF

cat >> %{buildroot}%{_scl_scripts}/service-environment << EOF
# Services are started in a fresh environment without any influence of user's
# environment (like environment variable values). As a consequence,
# information of all enabled collections will be lost during service start up.
# If user needs to run a service under any software collection enabled, this
# collection has to be written into MARIADB55_MYSQLD_SCLS_ENABLED variable in
# /opt/rh/sclname/service-environment.
MARIADB55_MYSQLD_SCLS_ENABLED="%{scl}"
EOF

%scl_install

%post runtime
# Simple copy of context from system root to DSC root.
# In case new version needs some additional rules or context definition,
# it needs to be solved.
# Unfortunately, semanage does not have -e option in RHEL-5, so we have to
# have its own policy for collection
%if 0%{?rhel} >= 6
    semanage fcontext -a -e / %{_scl_root} >/dev/null 2>&1 || :
    restorecon -R %{_scl_root} >/dev/null 2>&1 || :
%endif

%files

%files runtime
%scl_files
%config(noreplace) %{_scl_scripts}/service-environment

%files build
%{_root_sysconfdir}/rpm/macros.%{scl}-config

%changelog
* Mon Apr  8 2013 Honza Horak <hhorak@redhat.com> 1-2
- Don't require policycoreutils-python in RHEL-5 or older
- Require mariadb-server from the collection as main package

* Thu Mar 21 2013 Honza Horak <hhorak@redhat.com> 1-1
- initial packaging

