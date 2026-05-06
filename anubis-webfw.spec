#
# Conditional build:
%bcond_with	tests		# run upstream tests during build

Summary:	Anubis web AI firewall - proof-of-work bot blocker
Summary(pl.UTF-8):	Anubis - zapora przeciwko botom AI z wyzwaniem proof-of-work
Name:		anubis-webfw
Version:	1.25.0
Release:	2
License:	MIT
Group:		Networking/Daemons/HTTP
#Source0Download: https://github.com/TecharoHQ/anubis/releases
Source0:	https://github.com/TecharoHQ/anubis/releases/download/v%{version}/anubis-src-vendor-npm-%{version}.tar.gz
# Source0-md5:	e0f17ebee4f7ae72c9581a87f67ddf72
Source1:	%{name}.init
Source2:	%{name}.sysconfig
Source3:	%{name}.service
Source4:	%{name}.logrotate
URL:		https://anubis.techaro.lol/
BuildRequires:	golang >= 1.24.2
BuildRequires:	rpm-build >= 4.6
BuildRequires:	rpmbuild(macros) >= 2.009
BuildRequires:	tar >= 1:1.22
BuildRequires:	xz
Requires(post,preun):	/sbin/chkconfig
Requires(post,preun,postun):	systemd-units >= 38
Requires(postun):	/usr/sbin/groupdel
Requires(postun):	/usr/sbin/userdel
Requires(pre):	/bin/id
Requires(pre):	/usr/bin/getgid
Requires(pre):	/usr/sbin/groupadd
Requires(pre):	/usr/sbin/useradd
Requires:	rc-scripts
Requires:	systemd-units >= 0.38
Provides:	group(anubis)
Provides:	user(anubis)
ExclusiveArch:	%go_arches
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%undefine	_debugsource_packages

%description
Anubis is a Web AI Firewall Utility that weighs the soul of your
connection using one or more challenges to protect upstream resources
from scraper bots. By default Anubis presents a SHA-256 proof-of-work
challenge to clients, which discourages high-volume automated traffic
without inconveniencing real users.

This package installs the anubis daemon, the robots2policy helper for
converting robots.txt into Anubis bot policies, and the iplist2rule
helper for turning IP blocklists into Anubis rules.

%description -l pl.UTF-8
Anubis to webowa zapora chroniąca przed botami AI: stawia każdemu
łączącemu się klientowi jedno lub więcej wyzwań kryptograficznych
(domyślnie proof-of-work SHA-256), aby blokować masowy ruch automatyczny
przy minimalnej uciążliwości dla zwykłych użytkowników.

Pakiet zawiera demona anubis oraz narzędzia robots2policy (konwersja
robots.txt na polityki bota Anubis) i iplist2rule (konwersja list IP
na reguły Anubis).

%prep
%setup -q -n anubis-src-vendor-npm-%{version}

%{__mkdir_p} .go-cache target

%build
LDFLAGS="-X 'github.com/TecharoHQ/anubis.Version=v%{version}'"

%__go build -v -mod=vendor -ldflags "$LDFLAGS" -o target/anubis ./cmd/anubis
%__go build -v -mod=vendor -ldflags "$LDFLAGS" -o target/robots2policy ./cmd/robots2policy
%__go build -v -mod=vendor -ldflags "$LDFLAGS" -o target/iplist2rule ./utils/cmd/iplist2rule

%if %{with tests}
%__go test -mod=vendor ./...
%endif

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_bindir},%{_sysconfdir}/{anubis-webfw,logrotate.d},/etc/{rc.d/init.d,sysconfig},%{systemdunitdir},%{_datadir}/anubis-webfw,/var/log}

install -p target/anubis		$RPM_BUILD_ROOT%{_bindir}/anubis
install -p target/robots2policy	$RPM_BUILD_ROOT%{_bindir}/anubis-robots2policy
install -p target/iplist2rule		$RPM_BUILD_ROOT%{_bindir}/anubis-iplist2rule

install -p %{SOURCE1} $RPM_BUILD_ROOT/etc/rc.d/init.d/anubis-webfw
cp -p %{SOURCE2} $RPM_BUILD_ROOT/etc/sysconfig/anubis-webfw
cp -p %{SOURCE3} $RPM_BUILD_ROOT%{systemdunitdir}/anubis-webfw.service
cp -p %{SOURCE4} $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d/anubis-webfw
: > $RPM_BUILD_ROOT/var/log/anubis-webfw.log

# Ship sample botPolicies and the bundled data tree as documentation;
# admins can copy and reference snippets from /usr/share/anubis-webfw/data.
cp -pr data $RPM_BUILD_ROOT%{_datadir}/anubis-webfw/data
cp -p data/botPolicies.yaml $RPM_BUILD_ROOT%{_sysconfdir}/anubis-webfw/botPolicies.yaml

%clean
rm -rf $RPM_BUILD_ROOT

%pre
%groupadd -g 360 anubis
%useradd -u 360 -d /var/lib/anubis -s /bin/false -g anubis -c "Anubis web firewall" anubis

%post
/sbin/chkconfig --add anubis-webfw
%service anubis-webfw restart
%systemd_post anubis-webfw.service

%preun
if [ "$1" = "0" ]; then
	%service -q anubis-webfw stop
	/sbin/chkconfig --del anubis-webfw
fi
%systemd_preun anubis-webfw.service

%postun
if [ "$1" = "0" ]; then
	%userremove anubis
	%groupremove anubis
fi
%systemd_reload

%files
%defattr(644,root,root,755)
%doc LICENSE README.md SECURITY.md CONTRIBUTING.md
%attr(754,root,root) /etc/rc.d/init.d/anubis-webfw
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) /etc/sysconfig/anubis-webfw
%dir %{_sysconfdir}/anubis-webfw
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/anubis-webfw/botPolicies.yaml
%config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/logrotate.d/anubis-webfw
%attr(755,root,root) %{_bindir}/anubis
%attr(755,root,root) %{_bindir}/anubis-robots2policy
%attr(755,root,root) %{_bindir}/anubis-iplist2rule
%{systemdunitdir}/anubis-webfw.service
%{_datadir}/anubis-webfw
%attr(640,anubis,logs) %ghost /var/log/anubis-webfw.log
