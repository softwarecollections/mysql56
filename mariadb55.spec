%{!?scl_name_base: %global scl_name_base mariadb}
%{!?scl_name_version: %global scl_name_version 55}
%{!?scl:%global scl %{scl_name_base}%{scl_name_version}}
%scl_package %scl

# do not produce empty debuginfo package
%global debug_package %{nil}

Summary: Package that installs %scl
Name: %scl_name
Version: 1.1
Release: 17%{?dist}
License: GPLv2+
Group: Applications/File
Source0: README
Source1: LICENSE
Requires: scl-utils
Requires: %{scl_prefix}mariadb-server
BuildRequires: scl-utils-build help2man
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%description
This is the main package for %scl Software Collection, which installs
necessary packages to use MariaDB 5.5 server, a community developed branch
of MySQL. Software Collections allow to install more versions of the same
package by using alternative directory structure.
Install this package if you want to use MariaDB 5.5 server on your system.

%package runtime
Summary: Package that handles %scl Software Collection.
Group: Applications/File
Requires: scl-utils
Requires(post): policycoreutils-python libselinux-utils

%description runtime
Package shipping essential scripts to work with %scl Software Collection.

%package build
Summary: Package shipping basic build configuration
Group: Applications/File
Requires: scl-utils-build

%description build
Package shipping essential configuration macros to build %scl Software
Collection or packages depending on %scl Software Collection.

%package scldevel
Summary: Package shipping development files for %scl

%description scldevel
Package shipping development files, especially usefull for development of
packages depending on %scl Software Collection.

%prep
%setup -c -T

# This section generates README file from a template and creates man page
# from that file, expanding RPM macros in the template file.
cat >README <<'EOF'
%{expand:%(cat %{SOURCE0})}
EOF

# copy the license file so %%files section sees it
cp %{SOURCE1} .

%build
# generate a helper script that will be used by help2man
cat >h2m_helper <<'EOF'
#!/bin/bash
[ "$1" == "--version" ] && echo "%{scl_name} %{version} Software Collection" || cat README
EOF
chmod a+x h2m_helper
# generate the man page
help2man -N --section 7 ./h2m_helper -o %{scl_name}.7

%install
rm -rf %{buildroot}

%scl_install

# create and own dirs not covered by %%scl_install and %%scl_files
%if 0%{?rhel} <= 6
mkdir -p %{buildroot}%{_datadir}/aclocal
%else
mkdir -p %{buildroot}%{_mandir}/man{1,7,8}
%endif

# During the build of this package, we don't know which architecture it is 
# going to be used on, so if we build on 64-bit system and use it on 32-bit, 
# the %{_libdir} would stay expanded to '.../lib64'. This way we determine 
# architecture everytime the 'scl enable ...' is run and set the 
# LD_LIBRARY_PATH accordingly
cat >> %{buildroot}%{_scl_scripts}/enable << EOF
export PATH=%{_bindir}\${PATH:+:\${PATH}}
export LIBRARY_PATH=%{_libdir}\${LIBRARY_PATH:+:\${LIBRARY_PATH}}
export LD_LIBRARY_PATH=%{_libdir}\${LD_LIBRARY_PATH:+:\${LD_LIBRARY_PATH}}
export MANPATH=%{_mandir}:\${MANPATH}
export CPATH=%{_includedir}\${CPATH:+:\${CPATH}}
EOF

# generate rpm macros file for depended collections
cat >> %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel << EOF
%%scl_%{scl_name_base} %{scl}
%%scl_prefix_%{scl_name_base} %{scl_prefix}
EOF

# generate a configuration file for daemon
cat >> %{buildroot}%{_scl_scripts}/service-environment << EOF
# Services are started in a fresh environment without any influence of user's
# environment (like environment variable values). As a consequence,
# information of all enabled collections will be lost during service start up.
# If user needs to run a service under any software collection enabled, this
# collection has to be written into MARIADB55_SCLS_ENABLED variable in
# /opt/rh/sclname/service-environment.
MARIADB55_SCLS_ENABLED="%{scl}"
EOF

# install generated man page
mkdir -p %{buildroot}%{_mandir}/man7/
install -m 644 %{scl_name}.7 %{buildroot}%{_mandir}/man7/%{scl_name}.7

%post runtime
# Simple copy of context from system root to DSC root.
# In case new version needs some additional rules or context definition,
# it needs to be solved.
# Unfortunately, semanage does not have -e option in RHEL-5, so we would
# have to have its own policy for collection (inspire in mysql55 package)
semanage fcontext -a -e / %{_scl_root} >/dev/null 2>&1 || :
semanage fcontext -a -e /etc/rc.d/init.d/mysqld /etc/rc.d/init.d/%{scl_prefix}mysqld >/dev/null 2>&1 || :
semanage fcontext -a -e /var/log/mysqld.log /var/log/%{?scl_prefix}mysqld.log >/dev/null 2>&1 || :
semanage fcontext -a -e /var/log/mariadb /var/log/%{?scl_prefix}mariadb >/dev/null 2>&1 || :
restorecon -R %{_scl_root} >/dev/null 2>&1 || :
restorecon /etc/rc.d/init.d/%{scl_prefix}mysqld >/dev/null 2>&1 || :
restorecon /var/log/%{?scl_prefix}mysqld.log >/dev/null 2>&1 || :
restorecon /var/log/%{?scl_prefix}mariadb >/dev/null 2>&1 || :
selinuxenabled && load_policy || :

%files

%files runtime
%doc README LICENSE
%scl_files
%if 0%{?rhel} <= 6
%{_datadir}/aclocal
%else
%{_mandir}/man*
%endif
%config(noreplace) %{_scl_scripts}/service-environment
%{_mandir}/man7/%{scl_name}.*

%files build
%doc LICENSE
%{_root_sysconfdir}/rpm/macros.%{scl}-config

%files scldevel
%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel

%changelog
* Fri Mar 28 2014 Honza Horak <hhorak@redhat.com> - 1.1-17
- Include LICENSE also in -build package
  Related: #1072482

* Thu Mar 27 2014 Honza Horak <hhorak@redhat.com> - 1.1-16
- Own all dirs properly
  Resolves: #1079913

* Wed Mar 26 2014 Jan Stanek <jstanek@redhat.com> - 1.1-15
- Wrong macro in README
  Related: #1072482

* Wed Mar 26 2014 Jan Stanek <jstanek@redhat.com> - 1.1-14
- Fixed incorrect serveice name and unexpanded macro in README
  Resolves: #1079973 #1072482

* Thu Feb 13 2014 Honza Horak <hhorak@redhat.com> - 1.1-13
- Define context for RHEL-7 log file location
  Related: #1007861

* Wed Feb 12 2014 Honza Horak <hhorak@redhat.com> - 1.1-12
- Fix some grammar mistakes in README
  Related: #1061444

* Tue Feb 11 2014 Honza Horak <hhorak@redhat.com> - 1.1-11
- Add LICENSE, README and mariadb55.7 man page
  Resolves: #1061444
- Add -scldevel subpackage
  Resolves: #1063352
- Add scl-utils-build requirement to -build package
  Resolves: #1058612

* Wed Jan 15 2014 Honza Horak <hhorak@redhat.com> - 1-11
- Require policycoreutils-python for semanage
  Resolves: #1053393

* Fri Nov 22 2013 Honza Horak <hhorak@redhat.com> 1-10
- Reload SELinux policy after setting it

* Tue Oct 15 2013 Honza Horak <hhorak@redhat.com> 1-9
- Simplify environment variable name for enabled collections

* Thu Oct 10 2013 Honza Horak <hhorak@redhat.com> 1-8
- Release bump for RHSCL-1.1

* Mon Jun 10 2013 Honza Horak <hhorak@redhat.com> 1-7
- Add CPATH variable to enable script
  Resolves: #971808
- Define and restore SELinux context of log file
  Resolves: #971380

* Wed May 22 2013 Honza Horak <hhorak@redhat.com> 1-6
- Run semanage on whole root, BZ#956981 is fixed now
- Require semanage utility to be installed for -runtime package
- Fix MANPATH definition, colon in the end is correct (it means default)
  Resolves: BZ#966384

* Fri May  3 2013 Honza Horak <hhorak@redhat.com> 1-5
- Run semanage for all directories separately, since it has
  problems with definition for whole root

* Thu May  2 2013 Honza Horak <hhorak@redhat.com> 1-4
- Handle context of the init script
- Add better descriptions for packages

* Fri Apr 26 2013 Honza Horak <hhorak@redhat.com> 1-3
- fix escaping in PATH variable definition

* Mon Apr  8 2013 Honza Horak <hhorak@redhat.com> 1-2
- Don't require policycoreutils-python in RHEL-5 or older
- Require mariadb-server from the collection as main package
- Build separately on all arches
- Fix Environment variables definition

* Thu Mar 21 2013 Honza Horak <hhorak@redhat.com> 1-1
- initial packaging

