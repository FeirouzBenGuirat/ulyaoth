#
%define monkey_home %{_localstatedir}/cache/monkey
%define monkey_user monkey
%define monkey_group monkey
%define monkey_loggroup adm

# distribution specific definitions
%define use_systemd (0%{?fedora} && 0%{?fedora} >= 18) || (0%{?rhel} && 0%{?rhel} >= 7)

Summary: Monkey is a lightweight and powerful web server and development stack for GNU/Linux.
Name: ulyaoth-monkey
Version: 1.5.6
Release: 2%{?dist}
BuildArch: x86_64
Vendor: Monkey HTTP Daemon development group.
URL: http://monkey-project.com/
Packager: Sjir Bagmeijer <sbagmeijer@ulyaoth.co.kr>

Source0: http://monkey-project.com/releases/1.5/monkey-%{version}.tar.gz
Source1: https://raw.githubusercontent.com/sbagmeijer/ulyaoth/master/Repository/ulyaoth-monkey/SOURCES/monkey.service
Source2: https://raw.githubusercontent.com/sbagmeijer/ulyaoth/master/Repository/ulyaoth-monkey/SOURCES/monkey.init
Source3: https://raw.githubusercontent.com/sbagmeijer/ulyaoth/master/Repository/ulyaoth-monkey/SOURCES/monkey.logrotate


License: GPLv2+

Requires: ulyaoth-mbedtls

BuildRoot: %{_tmppath}/monkey-%{version}-%{release}-root
BuildRequires: ulyaoth-mbedtls

Provides: webserver
Provides: monkey
Provides: monkey-web-server
Provides: ulyaoth-monkey
Provides: ulyaoth-monkey-web-server

%description
Monkey is a lightweight and powerful web server and development stack for GNU/Linux.

It has been designed to be very scalable with low memory and CPU consumption, the perfect solution for embedded devices. Made for ARM, x86 and x64.

%prep
%setup -q -n monkey-%{version}

%build
./configure \
  --enable-plugins=mbedtls \
  --prefix=/srv/monkey \
  --bindir=/usr/bin \
  --libdir=/usr/lib \
  --incdir=/usr/include/monkey \
  --datadir=/srv/monkey \
  --mandir=/usr/share/man \
  --logdir=/var/log/monkey \
  --plugdir=/etc/monkey/plugins \
  --sysconfdir=/etc/monkey/conf \
  --pidfile=/var/run/monkey.pid \
  --default-port=80 \
  --default-user=monkey \
  $*
make %{?_smp_mflags}

%install
%{__rm} -rf $RPM_BUILD_ROOT
%{__make} DESTDIR=$RPM_BUILD_ROOT install

%{__rm} -rf $RPM_BUILD_ROOT/usr/lib/libmonkey.so

%if %{use_systemd}
# install systemd-specific files
%{__mkdir} -p $RPM_BUILD_ROOT%{_unitdir}
%{__install} -m644 %SOURCE1 \
        $RPM_BUILD_ROOT%{_unitdir}/monkey.service
%else
# install SYSV init stuff
%{__mkdir} -p $RPM_BUILD_ROOT%{_initrddir}
%{__install} -m755 %{SOURCE2} \
   $RPM_BUILD_ROOT%{_initrddir}/monkey
%endif

# install log rotation stuff
%{__mkdir} -p $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d
%{__install} -m 644 -p %{SOURCE3} \
   $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d/monkey

%clean
%{__rm} -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)

/usr/bin/monkey
/usr/bin/banana
/usr/bin/mk_passwd
/usr/lib/pkgconfig/monkey.pc

%dir %{_sysconfdir}/monkey
%dir /usr/include/monkey
%dir /srv/monkey
%dir /var/log/monkey

/srv/monkey/*
/usr/include/monkey/*
/etc/monkey/*
/usr/share/man/man1/*
/usr/share/man/man3/*

%config(noreplace) /etc/monkey/conf/monkey.conf
%config(noreplace) /etc/monkey/conf/plugins/auth/monkey.users
%config(noreplace) /etc/monkey/conf/plugins/cgi/cgi.conf
%config(noreplace) /etc/monkey/conf/plugins/cheetah/cheetah.conf
%config(noreplace) /etc/monkey/conf/plugins/dirlisting/dirhtml.conf
%config(noreplace) /etc/monkey/conf/plugins/fastcgi/fastcgi.conf
%config(noreplace) /etc/monkey/conf/plugins/logger/logger.conf
%config(noreplace) /etc/monkey/conf/plugins/mandril/mandril.conf
%config(noreplace) /etc/logrotate.d/monkey

%if %{use_systemd}
%{_unitdir}/monkey.service
%else
%{_initrddir}/monkey
%endif

%pre
# Add the "monkey" user
getent group %{monkey_group} >/dev/null || groupadd -r %{monkey_group}
getent passwd %{monkey_user} >/dev/null || \
    useradd -r -g %{monkey_group} -s /sbin/nologin \
    -d %{monkey_home} -c "monkey user"  %{monkey_user}
exit 0

%post
# Register the monkey service
if [ $1 -eq 1 ]; then
%if %{use_systemd}
    /usr/bin/systemctl preset monkey.service >/dev/null 2>&1 ||:
%else
    /sbin/chkconfig --add monkey
%endif
    # print site info
    cat <<BANNER
----------------------------------------------------------------------

Thanks for using ulyaoth-monkey!

Please find the official documentation for monkey here:
* http://monkey-project.com/

For any additional help please visit my forum at:
* http://www.ulyaoth.net

----------------------------------------------------------------------
BANNER

    # Touch and set permissions on default log files on installation

    if [ -d %{_localstatedir}/log/monkey ]; then
        if [ ! -e %{_localstatedir}/log/monkey/access.log ]; then
            touch %{_localstatedir}/log/monkey/access.log
            %{__chmod} 640 %{_localstatedir}/log/monkey/access.log
            %{__chown} monkey:%{monkey_loggroup} %{_localstatedir}/log/monkey/access.log
        fi

        if [ ! -e %{_localstatedir}/log/monkey/error.log ]; then
            touch %{_localstatedir}/log/monkey/error.log
            %{__chmod} 640 %{_localstatedir}/log/monkey/error.log
            %{__chown} monkey:%{monkey_loggroup} %{_localstatedir}/log/monkey/error.log
        fi
    fi
fi

%preun
if [ $1 -eq 0 ]; then
%if %use_systemd
    /usr/bin/systemctl --no-reload disable monkey.service >/dev/null 2>&1 ||:
    /usr/bin/systemctl stop monkey.service >/dev/null 2>&1 ||:
%else
    /sbin/service monkey stop > /dev/null 2>&1
    /sbin/chkconfig --del monkey
%endif
fi

%postun
%if %use_systemd
/usr/bin/systemctl daemon-reload >/dev/null 2>&1 ||:
%endif

%changelog
* Sun May 3 2015 Sjir Bagmeijer <sbagmeijer@ulyaoth.co.kr> 1.5.6-2
- Adding Secure Socket Layers (SSL) support.

* Fri May 1 2015 Sjir Bagmeijer <sbagmeijer@ulyaoth.co.kr> 1.5.6-1
- Initial release.