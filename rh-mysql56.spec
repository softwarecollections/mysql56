# Define SCL name
%{!?scl_name_prefix: %global scl_name_prefix rh-}
%{!?scl_name_base: %global scl_name_base mysql}
%{!?version_major: %global version_major 5}
%{!?version_minor: %global version_minor 6}
%{!?scl_name_version: %global scl_name_version %{version_major}%{version_minor}}
%{!?scl: %global scl %{scl_name_prefix}%{scl_name_base}%{scl_name_version}}

# Turn on new layout -- prefix for packages and location
# for config and variable files
# This must be before calling %%scl_package
%{!?nfsmountable: %global nfsmountable 1}

# Define SCL macros
%{?scl_package:%scl_package %scl}

# do not produce empty debuginfo package
%global debug_package %{nil}

Summary: Package that installs %{scl}
Name: %{scl}
Version: 2.0
Release: 13%{?dist}
License: GPLv2+
Group: Applications/File
Source0: README
Source1: LICENSE
Requires: scl-utils
Requires: %{?scl_prefix}mysql-server
BuildRequires: scl-utils-build help2man

%description
This is the main package for %{scl} Software Collection, which installs
necessary packages to use MySQL %{version_major}.%{version_minor} server.
Software Collections allow to install more versions of the same
package by using alternative directory structure.
Install this package if you want to use MySQL %{version_major}.%{version_minor}
server on your system.

%package runtime
Summary: Package that handles %{scl} Software Collection.
Group: Applications/File
Requires: scl-utils
Requires(post): policycoreutils-python libselinux-utils

%description runtime
Package shipping essential scripts to work with %{scl} Software Collection.

%package build
Summary: Package shipping basic build configuration
Group: Applications/File
Requires: scl-utils-build

%description build
Package shipping essential configuration macros to build %{scl} Software
Collection or packages depending on %{scl} Software Collection.

%package scldevel
Summary: Package shipping development files for %{scl}

%description scldevel
Package shipping development files, especially usefull for development of
packages depending on %{scl} Software Collection.

%prep
%setup -c -T

# This section generates README file from a template and creates man page
# from that file, expanding RPM macros in the template file.
cat <<'EOF' | tee README
%{expand:%(cat %{SOURCE0})}
EOF

# copy the license file so %%files section sees it
cp %{SOURCE1} .

%build
# generate a helper script that will be used by help2man
cat <<'EOF' | tee h2m_helper
#!/bin/bash
[ "$1" == "--version" ] && echo "%{?scl_name} %{version} Software Collection" || cat README
EOF
chmod a+x h2m_helper
# generate the man page
help2man -N --section 7 ./h2m_helper -o %{?scl_name}.7

%install
%{?scl_install}

# create and own dirs not covered by %%scl_install and %%scl_files
%if 0%{?rhel} >= 7 || 0%{?fedora} >= 15
mkdir -p %{buildroot}%{_mandir}/man{1,7,8}
%else
mkdir -p %{buildroot}%{_datadir}/aclocal
%endif

# create enable scriptlet that sets correct environment for collection
cat << EOF | tee -a %{buildroot}%{?_scl_scripts}/enable
# For binaries
export PATH="%{_bindir}\${PATH:+:\${PATH}}"
# For header files
export CPATH="%{_includedir}\${CPATH:+:\${CPATH}}"
# For libraries during build
export LIBRARY_PATH="%{_libdir}\${LIBRARY_PATH:+:\${LIBRARY_PATH}}"
# For libraries during linking
export LD_LIBRARY_PATH="%{_libdir}\${LD_LIBRARY_PATH:+:\${LD_LIBRARY_PATH}}"
# For man pages; empty field makes man to consider also standard path
export MANPATH="%{_mandir}:\${MANPATH}"
# For Java Packages Tools to locate java.conf
export JAVACONFDIRS="%{_sysconfdir}/java:\${JAVACONFDIRS:-/etc/java}"
# For XMvn to locate its configuration file(s)
export XDG_CONFIG_DIRS="%{_sysconfdir}/xdg:\${XDG_CONFIG_DIRS:-/etc/xdg}"
# For systemtap
export XDG_DATA_DIRS="%{_datadir}\${XDG_DATA_DIRS:+:\${XDG_DATA_DIRS}}"
# For pkg-config
export PKG_CONFIG_PATH="%{_libdir}/pkgconfig\${PKG_CONFIG_PATH:+:\${PKG_CONFIG_PATH}}"
EOF

# generate rpm macros file for depended collections
cat << EOF | tee -a %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel
%%scl_%{scl_name_base} %{scl}
%%scl_prefix_%{scl_name_base} %{?scl_prefix}
EOF

# install generated man page
mkdir -p %{buildroot}%{_mandir}/man7/
install -m 644 %{?scl_name}.7 %{buildroot}%{_mandir}/man7/%{?scl_name}.7

%post runtime
# Simple copy of context from system root to SCL root.
# In case new version needs some additional rules or context definition,
# it needs to be solved in base system.
# semanage does not have -e option in RHEL-5, so we would
# have to have its own policy for collection.
semanage fcontext -a -e / %{?_scl_root} >/dev/null 2>&1 || :
semanage fcontext -a -e %{_root_sysconfdir} %{_sysconfdir} >/dev/null 2>&1 || :
semanage fcontext -a -e %{_root_localstatedir} %{_localstatedir} >/dev/null 2>&1 || :
selinuxenabled && load_policy || :
restorecon -R %{?_scl_root} >/dev/null 2>&1 || :
restorecon -R %{_sysconfdir} >/dev/null 2>&1 || :
restorecon -R %{_localstatedir} >/dev/null 2>&1 || :

%files

%if 0%{?rhel} >= 7 || 0%{?fedora} >= 15
%files runtime -f filesystem
%else
%files runtime
%{_datadir}/aclocal
%endif
%doc README LICENSE
%{?scl_files}
%{_mandir}/man7/%{?scl_name}.*

%files build
%doc LICENSE
%{_root_sysconfdir}/rpm/macros.%{scl}-config

%files scldevel
%doc LICENSE
%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel

%changelog
* Tue Mar 17 2015 Honza Horak <hhorak@redhat.com> - 2.0-13
- Add comment about running the test suite
  Related: #1194759

* Mon Mar 09 2015 Honza Horak <hhorak@redhat.com> - 2.0-12
- Rebuild due to 'scls' removal
  Resolves: #1200052

* Wed Feb 18 2015 Honza Horak <hhorak@redhat.com> - 2.0-11
- Remove NFS register feature for questionable usage for DBs

* Mon Jan 26 2015 Honza Horak <hhorak@redhat.com> - 2.0-10
- Use cat for README expansion, rather than include macro

* Mon Jan 26 2015 Honza Horak <hhorak@redhat.com> - 2.0-9
- Do not set selinux context  scl root during scl register

* Sat Jan 17 2015 Honza Horak <hhorak@redhat.com> - 2.0-8
- Rework register implementation

* Fri Jan 16 2015 Honza Horak <hhorak@redhat.com> - 2.0-7
- Move service-environment into mariadb package

* Tue Jan 13 2015 Honza Horak <hhorak@redhat.com> - 2.0-6
- Re-work selinux rules setting and register layout

* Tue Jan 13 2015 Honza Horak <hhorak@redhat.com> - 2.0-5
- Use prefix in service-environment variable

* Mon Jan 12 2015 Honza Horak <hhorak@redhat.com> - 2.0-4
- Use scl macros more generally

* Fri Jan 09 2015 Honza Horak <hhorak@redhat.com> - 2.0-3
- Change prefix handling

* Fri Dec 05 2014 Honza Horak <hhorak@redhat.com> - 2.0-2
- Rework macros specification
  Specify macros that can be used in other packages in the collection

* Fri Nov 28 2014 Honza Horak <hhorak@redhat.com> - 2.0-1
- Adjust for MariaDB 10.0

* Tue Nov 25 2014 Honza Horak <hhorak@redhat.com> - 1.1-19
- Remove unncessary comment and buildroot cleanup

* Wed Oct 01 2014 Honza Horak <hhorak@redhat.com> - 1.1-18
- Make spec readable without scl-utils-build installed

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

