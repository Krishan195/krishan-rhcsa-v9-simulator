"""Fixed RHCSA v9 practice paper supplied by the repository owner.

Unlike the upstream random catalogue, this profile always returns the same
15 Node 1 and 6 Node 2 tasks, in paper order. Validation is deliberately
read-only: it inspects the resulting system but never changes it.
"""

import os
import pwd
import grp
import subprocess

from tasks.base import BaseTask
from core.validator import ValidationCheck, ValidationResult


def _run(command):
    return subprocess.run(
        command, shell=True, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, timeout=12
    )


class ExactPaperTask(BaseTask):
    exam_versions = [9]

    def __init__(self, number, node, category, points, description, checks,
                 requires_reboot=False):
        super().__init__(f"paper_node{node}_{number:02d}", category, "exam", points)
        self.number = number
        self.node = node
        self.description = f"NODE {node} - Question {number}\n\n{description}"
        self._checks = checks
        self.requires_reboot = requires_reboot
        self.requires_persistence = category in {
            "networking", "repos", "selinux", "firewall", "users_groups",
            "permissions", "scheduling", "network_storage", "time_services",
            "containers", "lvm", "swap", "filesystems"
        }
        self.tags = ["exact-paper", f"node{node}"]

    def generate(self, **params):
        return self

    def validate(self):
        results = []
        earned = 0
        each = self.points / max(1, len(self._checks))
        for label, command in self._checks:
            try:
                proc = _run(command)
                passed = proc.returncode == 0
                detail = (proc.stdout or "").strip()[-500:]
            except Exception as exc:
                passed, detail = False, str(exc)
            pts = each if passed else 0
            earned += pts
            results.append(ValidationCheck(
                label, passed, pts,
                f"{label}: {'passed' if passed else 'not satisfied'}",
                max_points=each, details=detail or None,
            ))
        score = round(earned)
        return ValidationResult(
            self.id, all(c.passed for c in results), score, self.points, results
        )


def _t(number, node, category, points, description, *checks, **kwargs):
    return ExactPaperTask(number, node, category, points, description,
                          list(checks), **kwargs).generate()


def build_exact_exam():
    """Return the supplied paper verbatim in its original node/task order."""
    return [
        _t(1, 1, "networking", 14,
           "Configure the network using IP 172.24.7.10/24, gateway 172.24.7.254, DNS 172.24.7.254, and set the hostname to node1.domain7.example.com.",
           ("hostname", "test \"$(hostname)\" = node1.domain7.example.com"),
           ("IPv4 address", "ip -4 addr show | grep -q '172.24.7.10/24'"),
           ("default gateway", "ip route | grep -q 'default via 172.24.7.254'"),
           ("DNS server", "grep -q '172.24.7.254' /etc/resolv.conf")),

        _t(2, 1, "repos", 12,
           "Configure DNF repositories for BaseOS at http://content.example.com/rhel9/x86_64/dvd/BaseOS and AppStream at http://content.example.com/rhel9/x86_64/dvd/AppStream. Disable GPG checking for both.",
           ("BaseOS repository", "grep -Rqs 'content.example.com/rhel9/x86_64/dvd/BaseOS' /etc/yum.repos.d"),
           ("AppStream repository", "grep -Rqs 'content.example.com/rhel9/x86_64/dvd/AppStream' /etc/yum.repos.d"),
           ("repositories enabled", "dnf -q repolist >/dev/null")),

        _t(3, 1, "selinux", 16,
           "Troubleshoot the web server under /var/www/html so it serves on both TCP ports 80 and 82. Configure SELinux and the firewall correctly.",
           ("httpd active", "systemctl is-active --quiet httpd"),
           ("SELinux port 82", "semanage port -l | awk '$1==\"http_port_t\" {print}' | grep -Eq '(^|,| )82(,| |$)'"),
           ("firewall HTTP", "firewall-cmd --query-service=http"),
           ("firewall port 82", "firewall-cmd --query-port=82/tcp")),

        _t(4, 1, "users_groups", 16,
           "Create group adminuser. Create harry and natasha with adminuser as a secondary group. Create sarah with no interactive shell and not as a member of adminuser. Set all three passwords to postroll.",
           ("adminuser group", "getent group adminuser >/dev/null"),
           ("harry membership", "id -nG harry | tr ' ' '\\n' | grep -qx adminuser"),
           ("natasha membership", "id -nG natasha | tr ' ' '\\n' | grep -qx adminuser"),
           ("sarah nologin", "getent passwd sarah | grep -Eq ':(/sbin|/usr/sbin)/nologin$'"),
           ("sarah excluded", "! id -nG sarah | tr ' ' '\\n' | grep -qx adminuser")),

        _t(5, 1, "scheduling", 10,
           "Configure a cron job for natasha that runs /bin/echo Haiya every day at 14:23 local time.",
           ("natasha cron", "crontab -u natasha -l | grep -Eq '^23[[:space:]]+14[[:space:]]+\\*[[:space:]]+\\*[[:space:]]+\\*[[:space:]]+/bin/echo[[:space:]]+Haiya([[:space:]]*)$'")),

        _t(6, 1, "permissions", 12,
           "Create collaborative directory /home/admin owned by group adminuser. Group members must have full access, others no access, and new files must inherit group adminuser.",
           ("directory exists", "test -d /home/admin"),
           ("group ownership", "test \"$(stat -c %G /home/admin)\" = adminuser"),
           ("mode 2770", "test \"$(stat -c %a /home/admin)\" = 2770")),

        _t(7, 1, "users_groups", 8,
           "Create user alex with UID 3456 and password postroll.",
           ("alex UID", "test \"$(id -u alex 2>/dev/null)\" = 3456")),

        _t(8, 1, "essential_tools", 10,
           "Locate all regular files owned by user aletha and copy them into /root/find while preserving attributes.",
           ("destination", "test -d /root/find"),
           ("files copied", "test -n \"$(find /root/find -type f -print -quit 2>/dev/null)\"")),

        _t(9, 1, "essential_tools", 8,
           "Find every complete word containing the string 'asse' in /usr/share/dict/words and write the results to /root/lines. The output must not contain spaces.",
           ("lines file", "test -s /root/lines"),
           ("matching words only", "! grep -Ev '^[^[:space:]]*asse[^[:space:]]*$' /root/lines | grep -q .")),

        _t(10, 1, "network_storage", 16,
           "Configure autofs so 172.24.20.250:/home/remoteuser20 is mounted read-write at /remote/remoteuser20 on demand.",
           ("autofs enabled", "systemctl is-enabled --quiet autofs"),
           ("map configured", "grep -Rqs '172.24.20.250:/home/remoteuser20' /etc/auto.*"),
           ("mount path", "grep -Rqs '/remote' /etc/auto.master /etc/auto.master.d")),

        _t(11, 1, "essential_tools", 8,
           "Create a bzip2-compressed archive /root/backup.tar.bz2 containing /usr/local.",
           ("archive valid", "tar -tjf /root/backup.tar.bz2 >/dev/null"),
           ("contains usr/local", "tar -tjf /root/backup.tar.bz2 | grep -q '^usr/local'")),

        _t(12, 1, "scripting", 12,
           "Create executable script /usr/local/bin/myscript. It must locate regular files under /usr/share that are 10 MB or smaller and have SGID set, writing the list to /root/script.",
           ("script executable", "test -x /usr/local/bin/myscript"),
           ("uses find", "grep -q 'find.*/usr/share' /usr/local/bin/myscript"),
           ("writes output", "grep -q '/root/script' /usr/local/bin/myscript")),

        _t(13, 1, "time_services", 10,
           "Configure node1 to synchronize time from redhat.domain7.example.com.",
           ("chrony source", "grep -REq '^[[:space:]]*(server|pool)[[:space:]]+redhat\\.domain7\\.example\\.com([[:space:]]|$)' /etc/chrony.conf /etc/chrony.d 2>/dev/null"),
           ("chronyd active", "systemctl is-active --quiet chronyd")),

        _t(14, 1, "containers", 12,
           "As user aletha, download the unmodified Containerfile from http://domain.exam.com/rhel9/Containerfile and build an image named monitor.",
           ("monitor image", "podman image exists monitor || runuser -u aletha -- podman image exists monitor")),

        _t(15, 1, "containers", 18,
           "As user aletha, create container asciipdf from image monitor. Bind-mount /opt/input to /opt/incoming and /opt/output to /opt/processed with SELinux labeling. Configure container-asciipdf.service to start and stop with boot.",
           ("host directories", "test -d /opt/input -a -d /opt/output"),
           ("container exists", "podman container exists asciipdf || runuser -u aletha -- podman container exists asciipdf"),
           ("user service", "test -f /home/aletha/.config/systemd/user/container-asciipdf.service"),
           ("linger enabled", "loginctl show-user aletha -p Linger --value | grep -qx yes")),

        _t(1, 2, "boot_recovery", 12,
           "Reset the root password on node2 using the RHEL 9 rescue-kernel rd.break procedure.",
           ("root password set", "passwd -S root | awk '$2 != \"NP\" {ok=1} END {exit !ok}'"),
           requires_reboot=True),

        _t(2, 2, "repos", 12,
           "Configure DNF repositories for BaseOS at http://content.example.com/rhel9/x86_64/dvd/BaseOS and AppStream at http://content.example.com/rhel9/x86_64/dvd/AppStream. Disable GPG checking for both.",
           ("BaseOS repository", "grep -Rqs 'content.example.com/rhel9/x86_64/dvd/BaseOS' /etc/yum.repos.d"),
           ("AppStream repository", "grep -Rqs 'content.example.com/rhel9/x86_64/dvd/AppStream' /etc/yum.repos.d")),

        _t(3, 2, "lvm", 16,
           "Resize logical volume data to 750 MiB without losing its existing data. Resize its ext4 filesystem as well.",
           ("LV size", "lvs --noheadings --units m --nosuffix -o lv_size data 2>/dev/null | awk '{exit !($1 >= 749 && $1 <= 751)}'"),
           ("filesystem", "blkid -o value -s TYPE $(lvs --noheadings -o lv_path data 2>/dev/null | xargs) | grep -qx ext4")),

        _t(4, 2, "swap", 14,
           "Create an additional 512 MiB swap partition and enable it permanently without changing existing swap space.",
           ("512 MiB swap active", "swapon --show --bytes --noheadings --output SIZE | awk '$1 >= 530000000 && $1 <= 544000000 {ok=1} END {exit !ok}'"),
           ("persistent swap", "grep -Ev '^[[:space:]]*(#|$)' /etc/fstab | grep -q '[[:space:]]swap[[:space:]]'")),

        _t(5, 2, "lvm", 18,
           "Create volume group Exam and logical volume RHCSA sized 750 MiB. Format it as ext3 and mount it persistently at /root/exam.",
           ("volume group", "vgs Exam >/dev/null"),
           ("logical volume", "lvs Exam/RHCSA >/dev/null"),
           ("ext3 filesystem", "blkid -o value -s TYPE /dev/Exam/RHCSA | grep -Eq '^ext3$'"),
           ("mounted", "findmnt -rn /root/exam >/dev/null"),
           ("persistent mount", "grep -Ev '^[[:space:]]*(#|$)' /etc/fstab | grep -qE '/root/exam[[:space:]]+ext3'")),

        _t(6, 2, "services", 10,
           "Apply the tuned profile recommended for node2 and ensure tuned is enabled.",
           ("tuned enabled", "systemctl is-enabled --quiet tuned"),
           ("recommended profile active", "test \"$(tuned-adm active | sed 's/.*: //')\" = \"$(tuned-adm recommend)\"")),
    ]
