"""Krishan deterministic RHCSA v9 paper simulator.

This module locks Exam Mode to the exact 21-question paper used for the
practice session: 15 tasks for node1 and 6 tasks for node2.  The validators are
read-mostly shell predicates; where a practical proof is useful, they only run
safe verification commands.
"""

import subprocess
from dataclasses import dataclass

from tasks.base import BaseTask
from core.validator import ValidationCheck, ValidationResult
from core import lab_machine


@dataclass(frozen=True)
class ShellCheck:
    name: str
    points: int
    script: str
    success: str
    failure: str
    remote: bool = False


def _run(script, remote=False, timeout=30):
    if remote:
        return lab_machine.run(script, timeout=timeout)
    try:
        result = subprocess.run(
            ["bash", "-o", "pipefail", "-c", script],
            text=True, capture_output=True, timeout=timeout)
        return result.returncode, (result.stdout or "") + (result.stderr or "")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, str(exc)


class PaperTask(BaseTask):
    """Fixed task whose shell checks return exit 0 on success."""

    def __init__(self, task_id, node, category, points, description, checks,
                 requires_persistence=True):
        super().__init__(task_id, category, "exam", points)
        self.node = node
        self.description = description
        self.checks_spec = tuple(checks)
        self.requires_persistence = requires_persistence
        self.requires_lab_machine = node == 2
        self.tags = ["krishan-exact-paper", f"node-{node}"]
        self.hints = []

    def generate(self, **params):
        return self

    def validate(self):
        results = []
        score = 0
        for spec in self.checks_spec:
            rc, output = _run(spec.script, spec.remote)
            passed = rc == 0
            if passed:
                score += spec.points
            message = spec.success if passed else spec.failure
            if not passed and output:
                message += f" ({output.strip()[:220]})"
            results.append(ValidationCheck(
                spec.name, passed, spec.points if passed else 0, message,
                max_points=spec.points))
        return ValidationResult(
            self.id, score >= self.points * 0.70, score, self.points, results)

    def validate_persistence(self):
        return self.validate()


class RootRecoveryTask(PaperTask):
    """Use the simulator's guarded two-node password-recovery scenario."""

    has_setup = True

    def setup_environment(self):
        from core import boot_rescue
        return boot_rescue.start()

    def validate(self):
        from core import boot_rescue
        checks, _method, error = boot_rescue.validate()
        if checks is None:
            result = ValidationCheck(
                "root_recovery", False, 0, error or "Recovery not validated",
                max_points=self.points)
            return ValidationResult(self.id, False, 0, self.points, [result])
        weights = {"password_changed": 10, "rebooted": 5,
                   "shadow_context": 5}
        rendered = []
        score = 0
        for name, passed, message in checks:
            if passed is None:
                continue
            points = weights.get(name, 0)
            if passed:
                score += points
            rendered.append(ValidationCheck(
                name, bool(passed), points if passed else 0, message,
                max_points=points))
        return ValidationResult(self.id, score >= self.points * 0.70,
                                score, self.points, rendered)


def C(name, points, script, success, failure, remote=False):
    return ShellCheck(name, points, script, success, failure, remote)


NODE1_REPO_BASEOS = "http://content.example.com/rhel9/x86_64/dvd/BaseOS"
NODE1_REPO_APPSTREAM = "http://content.example.com/rhel9/x86_64/dvd/AppStream"


def build_exam_tasks():
    """Return the supplied paper in exact exam order: node1 then node2."""
    tasks = [
        PaperTask("n1_01_network_hostname", 1, "networking", 15,
            "On node1, configure hostname node1.domain7.example.com. Configure the existing NetworkManager connection for IPv4 address 172.24.7.10/24, gateway 172.24.7.254, DNS 172.24.7.254, manual IPv4, and autoconnect enabled.", [
                C("hostname", 4, "test \"$(hostnamectl --static)\" = node1.domain7.example.com",
                  "Hostname is correct", "Hostname is not node1.domain7.example.com"),
                C("ipv4_address", 4, "ip -4 addr show | grep -q '172.24.7.10/24'",
                  "IPv4 address is present", "172.24.7.10/24 was not found"),
                C("gateway", 3, "ip route | grep -q 'default via 172.24.7.254'",
                  "Default gateway is correct", "Default gateway is not 172.24.7.254"),
                C("dns", 2, "grep -q '172.24.7.254' /etc/resolv.conf || grep -Rqs 'dns.*172.24.7.254' /etc/NetworkManager/system-connections",
                  "DNS is configured", "DNS 172.24.7.254 was not found"),
                C("autoconnect", 2, "nmcli -g connection.autoconnect con show | grep -qx yes",
                  "A persistent autoconnecting profile exists", "No autoconnecting NetworkManager profile was detected"),
            ]),

        PaperTask("n1_02_repositories", 1, "repos", 12,
            f"Configure DNF repositories for BaseOS at {NODE1_REPO_BASEOS} and AppStream at {NODE1_REPO_APPSTREAM}. Enable both and disable GPG checking.", [
                C("baseos", 4, f"grep -Rqs 'baseurl={NODE1_REPO_BASEOS}' /etc/yum.repos.d && grep -Rqs '^\\[BaseOS\\]' /etc/yum.repos.d",
                  "BaseOS repository is configured", "BaseOS repository is missing or incorrect"),
                C("appstream", 4, f"grep -Rqs 'baseurl={NODE1_REPO_APPSTREAM}' /etc/yum.repos.d && grep -Rqs '^\\[AppStream\\]' /etc/yum.repos.d",
                  "AppStream repository is configured", "AppStream repository is missing or incorrect"),
                C("enabled_gpgcheck", 4, "awk 'BEGIN{RS=\"\"} /\\[(BaseOS|AppStream)\\]/ {if ($0 !~ /enabled[[:space:]]*=[[:space:]]*1/ || $0 !~ /gpgcheck[[:space:]]*=[[:space:]]*0/) bad=1} END{exit bad}' /etc/yum.repos.d/*.repo",
                  "Repositories are enabled with gpgcheck disabled", "Repository enabled/gpgcheck settings are incorrect"),
            ]),

        PaperTask("n1_03_httpd_selinux_firewall", 1, "selinux", 18,
            "Configure the web server to serve content from /var/www/html on TCP ports 80 and 82. Ensure httpd is active, SELinux permits port 82 as http_port_t, and the firewall allows HTTP and 82/tcp.", [
                C("httpd_active", 4, "systemctl is-active --quiet httpd",
                  "httpd is active", "httpd is not active"),
                C("httpd_listens_82", 4, "ss -ltnp 2>/dev/null | grep -q ':82[[:space:]]' || grep -RqsE '^[[:space:]]*Listen[[:space:]]+82' /etc/httpd/conf /etc/httpd/conf.d",
                  "httpd is configured/listening on port 82", "httpd port 82 was not found"),
                C("selinux_port", 4, "semanage port -l | awk '$1==\"http_port_t\" && $2==\"tcp\" {$1=$2=\"\"; print}' | grep -qw 82",
                  "SELinux permits httpd on 82/tcp", "82/tcp is not labelled http_port_t"),
                C("firewall_http", 3, "firewall-cmd --quiet --query-service=http && firewall-cmd --quiet --permanent --query-service=http",
                  "HTTP firewall service is allowed", "HTTP firewall service is not allowed runtime/permanent"),
                C("firewall_82", 3, "firewall-cmd --quiet --query-port=82/tcp && firewall-cmd --quiet --permanent --query-port=82/tcp",
                  "82/tcp firewall port is allowed", "82/tcp firewall port is not allowed runtime/permanent"),
            ]),

        PaperTask("n1_04_users_groups", 1, "users_groups", 16,
            "Create group adminuser. Create users harry and natasha with adminuser as a supplementary group. Create user sarah with no interactive shell and without adminuser membership. Set passwords to postroll.", [
                C("group", 3, "getent group adminuser >/dev/null",
                  "adminuser group exists", "adminuser group was not found"),
                C("harry", 3, "id -nG harry 2>/dev/null | tr ' ' '\\n' | grep -qx adminuser",
                  "harry is in adminuser", "harry is missing adminuser supplementary membership"),
                C("natasha", 3, "id -nG natasha 2>/dev/null | tr ' ' '\\n' | grep -qx adminuser",
                  "natasha is in adminuser", "natasha is missing adminuser supplementary membership"),
                C("sarah_shell", 3, "getent passwd sarah | cut -d: -f7 | grep -Eq '(/sbin/nologin|/usr/sbin/nologin|/bin/false)$'",
                  "sarah has no interactive shell", "sarah shell is not non-interactive"),
                C("sarah_not_admin", 2, "! id -nG sarah 2>/dev/null | tr ' ' '\\n' | grep -qx adminuser",
                  "sarah is not in adminuser", "sarah must not be in adminuser"),
                C("passwords", 2, "for u in harry natasha sarah; do passwd -S $u | awk '$2==\"P\" {ok=1} END{exit !ok}' || exit 1; done",
                  "All users have usable passwords", "One or more passwords are not set"),
            ]),

        PaperTask("n1_05_cron_natasha", 1, "scheduling", 10,
            "Configure a cron job for natasha that runs /bin/echo Haiya every day at 14:23.", [
                C("cron", 10, "crontab -u natasha -l 2>/dev/null | grep -Eq '^23[[:space:]]+14[[:space:]]+\\*[[:space:]]+\\*[[:space:]]+\\*[[:space:]]+/bin/echo[[:space:]]+Haiya([[:space:]]*)$'",
                  "natasha cron job is correct", "Required natasha cron entry was not found"),
            ]),

        PaperTask("n1_06_collaborative_directory", 1, "permissions", 12,
            "Create /home/admin as a collaborative directory owned by group adminuser. Group members must have full access, others no access, and new files must inherit group adminuser.", [
                C("exists", 3, "test -d /home/admin",
                  "/home/admin exists", "/home/admin does not exist"),
                C("group", 3, "test \"$(stat -c %G /home/admin)\" = adminuser",
                  "Group owner is adminuser", "Group owner is not adminuser"),
                C("mode", 6, "test \"$(stat -c %a /home/admin)\" = 2770",
                  "Mode is 2770", "Expected mode 2770"),
            ]),

        PaperTask("n1_07_alex_uid", 1, "users_groups", 8,
            "Create user alex with UID 3456 and password postroll.", [
                C("uid", 5, "test \"$(id -u alex 2>/dev/null)\" = 3456",
                  "alex UID is 3456", "alex UID is not 3456"),
                C("password", 3, "passwd -S alex | awk '$2==\"P\" {ok=1} END{exit !ok}'",
                  "alex has a usable password", "alex password is not set"),
            ]),

        PaperTask("n1_08_find_aletha_files", 1, "essential_tools", 10,
            "Find all regular files owned by user aletha and copy them to /root/find while preserving attributes.", [
                C("destination", 3, "test -d /root/find",
                  "/root/find exists", "/root/find does not exist"),
                C("has_copies", 4, "test -n \"$(find /root/find -type f -user aletha -print -quit 2>/dev/null)\" || test -n \"$(find /root/find -type f -print -quit 2>/dev/null)\"",
                  "Copied files are present", "No copied regular files were found in /root/find"),
                C("preserve_owner", 3, "test -n \"$(find /root/find -type f -user aletha -print -quit 2>/dev/null)\"",
                  "At least one copied file preserved aletha ownership", "Copied files do not preserve aletha ownership"),
            ]),

        PaperTask("n1_09_grep_asse", 1, "essential_tools", 8,
            "Find every word containing the string 'asse' in /usr/share/dict/words and save the result in /root/lines.", [
                C("file_exists", 3, "test -s /root/lines",
                  "/root/lines exists and is not empty", "/root/lines is missing or empty"),
                C("matches_only", 3, "! grep -Ev '^[^[:space:]]*asse[^[:space:]]*$' /root/lines | grep -q .",
                  "All output lines contain asse as complete words", "Output contains non-matching lines"),
                C("same_as_grep", 2, "cmp -s <(grep 'asse' /usr/share/dict/words 2>/dev/null) /root/lines",
                  "Output matches grep result", "Output does not match grep 'asse' /usr/share/dict/words"),
            ]),

        PaperTask("n1_10_autofs_remoteuser20", 1, "network_storage", 16,
            "Configure autofs so 172.24.20.250:/home/remoteuser20 is mounted read-write on demand at /remote/remoteuser20.", [
                C("packages_service", 3, "rpm -q autofs nfs-utils >/dev/null && systemctl is-enabled --quiet autofs && systemctl is-active --quiet autofs",
                  "autofs and nfs-utils are installed and autofs is enabled/active", "autofs/nfs-utils or autofs service is not ready"),
                C("master_map", 4, "grep -RqsE '^[[:space:]]*/remote[[:space:]]+' /etc/auto.master /etc/auto.master.d/*.autofs 2>/dev/null",
                  "Master map manages /remote", "No /remote autofs master map found"),
                C("direct_key", 4, "grep -RqsE '^remoteuser20[[:space:]]+' /etc/auto.remoteuser /etc/auto.* 2>/dev/null",
                  "remoteuser20 key is configured", "remoteuser20 key was not found"),
                C("nfs_target", 5, "grep -RqsE '(172\\.24\\.20\\.250|serverb|classroom\\.example\\.com):/home/remoteuser20' /etc/auto.remoteuser /etc/auto.* 2>/dev/null",
                  "NFS target is configured", "NFS target /home/remoteuser20 was not found"),
            ]),

        PaperTask("n1_11_backup_archive", 1, "essential_tools", 8,
            "Create a bzip2-compressed tar archive /root/backup.tar.bz2 containing /usr/local.", [
                C("valid_bzip2_tar", 4, "tar -tjf /root/backup.tar.bz2 >/dev/null",
                  "Archive is a valid bzip2 tar", "Archive is missing or invalid"),
                C("contains_usr_local", 4, "tar -tjf /root/backup.tar.bz2 | grep -Eq '^(usr/local|/usr/local)'",
                  "Archive contains /usr/local", "Archive does not contain /usr/local"),
            ]),

        PaperTask("n1_12_myscript", 1, "scripting", 12,
            "Create executable script /usr/local/bin/myscript. The script must find regular files under /usr/share that are smaller than 10 MB and have SGID set, writing the list to /root/script.", [
                C("exists_executable", 3, "test -x /usr/local/bin/myscript",
                  "myscript exists and is executable", "myscript missing or not executable"),
                C("uses_usr_share", 3, "grep -Eq 'find[[:space:]]+/usr/share|find[[:space:]].*/usr/share' /usr/local/bin/myscript",
                  "Script searches /usr/share", "Script does not search /usr/share"),
                C("sgid_condition", 3, "grep -Eq -- '-perm[[:space:]]+(-g=s|-2000|-02000)' /usr/local/bin/myscript",
                  "Script checks SGID permission", "Script does not check SGID permission"),
                C("writes_root_script", 3, "grep -q '/root/script' /usr/local/bin/myscript",
                  "Script writes to /root/script", "Script does not write to /root/script"),
            ]),

        PaperTask("n1_13_chrony", 1, "time_services", 10,
            "Configure time synchronization using redhat.domain7.example.com and ensure chronyd is enabled and running.", [
                C("source", 5, "grep -REq '^[[:space:]]*(server|pool)[[:space:]]+redhat\\.domain7\\.example\\.com([[:space:]]|$)' /etc/chrony.conf /etc/chrony.d/*.conf 2>/dev/null",
                  "Chrony source is configured", "redhat.domain7.example.com is not configured as a chrony source"),
                C("service", 5, "systemctl is-enabled --quiet chronyd && systemctl is-active --quiet chronyd",
                  "chronyd is enabled and active", "chronyd is not enabled and active"),
            ]),

        PaperTask("n1_14_podman_image", 1, "containers", 12,
            "As user aletha, download the unmodified Containerfile from http://domain.exam.com/rhel9/Containerfile and build a Podman image named monitor.", [
                C("aletha_exists", 2, "id aletha >/dev/null",
                  "aletha exists", "User aletha does not exist"),
                C("containerfile", 3, "test -f /home/aletha/Containerfile",
                  "Containerfile is present in aletha home", "Containerfile was not found in /home/aletha"),
                C("monitor_image", 7, "runuser -u aletha -- bash -lc 'export XDG_RUNTIME_DIR=/run/user/$(id -u); podman image exists monitor || podman image exists localhost/monitor'",
                  "monitor image exists for aletha", "monitor image was not found for aletha"),
            ]),

        PaperTask("n1_15_podman_container_service", 1, "containers", 18,
            "As user aletha, create container asciipdf from image monitor. Bind-mount /opt/input to /opt/incoming and /opt/output to /opt/processed with SELinux labeling. Configure container-asciipdf.service to start and stop with boot.", [
                C("host_dirs", 3, "test -d /opt/input -a -d /opt/output && test \"$(stat -c %U /opt/input)\" = aletha && test \"$(stat -c %U /opt/output)\" = aletha",
                  "Host directories exist and are owned by aletha", "Host directories missing or not owned by aletha"),
                C("container", 4, "runuser -u aletha -- bash -lc 'export XDG_RUNTIME_DIR=/run/user/$(id -u); podman container exists asciipdf'",
                  "asciipdf container exists for aletha", "asciipdf container was not found for aletha"),
                C("mounts", 4, "runuser -u aletha -- bash -lc 'export XDG_RUNTIME_DIR=/run/user/$(id -u); podman inspect asciipdf --format \"{{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}\"' | grep -q '/opt/input:/opt/incoming' && runuser -u aletha -- bash -lc 'export XDG_RUNTIME_DIR=/run/user/$(id -u); podman inspect asciipdf --format \"{{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}\"' | grep -q '/opt/output:/opt/processed'",
                  "Container volume mounts are correct", "Container mounts are incorrect"),
                C("systemd_user_service", 4, "test -f /home/aletha/.config/systemd/user/container-asciipdf.service && grep -q 'asciipdf' /home/aletha/.config/systemd/user/container-asciipdf.service",
                  "container-asciipdf.service exists", "User systemd service is missing"),
                C("linger", 3, "loginctl show-user aletha -p Linger --value | grep -qx yes",
                  "linger is enabled for aletha", "linger is not enabled for aletha"),
            ]),

        RootRecoveryTask("n2_01_root_password", 2, "boot_recovery", 20,
            "On node2, reset the root password to postroll using the RHEL 9 rd.break rescue procedure.", [], requires_persistence=True),

        PaperTask("n2_02_repositories", 2, "repos", 12,
            f"On node2, configure DNF repositories for BaseOS at {NODE1_REPO_BASEOS} and AppStream at {NODE1_REPO_APPSTREAM}. Enable both and disable GPG checking.", [
                C("baseos", 6, f"grep -Rqs 'baseurl={NODE1_REPO_BASEOS}' /etc/yum.repos.d && grep -Rqs '^\\[BaseOS\\]' /etc/yum.repos.d",
                  "BaseOS repository is configured", "BaseOS repository missing or incorrect", remote=True),
                C("appstream", 6, f"grep -Rqs 'baseurl={NODE1_REPO_APPSTREAM}' /etc/yum.repos.d && grep -Rqs '^\\[AppStream\\]' /etc/yum.repos.d",
                  "AppStream repository is configured", "AppStream repository missing or incorrect", remote=True),
            ]),

        PaperTask("n2_03_resize_data_lv", 2, "lvm", 16,
            "On node2, resize the existing logical volume named data to a final size of 750 MiB without losing data. The ext4 filesystem must also be resized.", [
                C("lv_size", 8, "size=$(lvs --noheadings --units m --nosuffix -S 'lv_name=data' -o lv_size 2>/dev/null | awk 'NR==1{print int($1)}'); test -n \"$size\" && test $size -ge 749 && test $size -le 753",
                  "data LV final size is about 750 MiB", "data LV is not about 750 MiB", remote=True),
                C("filesystem_ext4", 4, "lv=$(lvs --noheadings -S 'lv_name=data' -o lv_path 2>/dev/null | awk 'NR==1{print $1}'); test -n \"$lv\" && blkid -o value -s TYPE \"$lv\" | grep -qx ext4",
                  "data filesystem is ext4", "data filesystem is not ext4", remote=True),
                C("fs_resized", 4, "mnt=$(findmnt -rn -S $(lvs --noheadings -S 'lv_name=data' -o lv_path 2>/dev/null | awk 'NR==1{print $1}') -o TARGET 2>/dev/null); if [ -n \"$mnt\" ]; then df -m --output=size \"$mnt\" | awk 'NR==2{exit !($1>=700)}'; else lv=$(lvs --noheadings -S 'lv_name=data' -o lv_path 2>/dev/null | awk 'NR==1{print $1}'); dumpe2fs -h \"$lv\" 2>/dev/null | awk '/Block count:/{bc=$3}/Block size:/{bs=$3} END{exit !((bc*bs)/1048576>=700)}'; fi",
                  "ext4 filesystem is resized", "ext4 filesystem was not resized", remote=True),
            ]),

        PaperTask("n2_04_swap", 2, "swap", 14,
            "On node2, create an additional 512 MiB swap partition, enable it immediately, and make it persistent without modifying existing swap.", [
                C("active_swap", 7, "swapon --show --bytes --noheadings --output SIZE | awk '$1 >= 530000000 && $1 <= 545000000 {ok=1} END {exit !ok}'",
                  "Additional 512 MiB swap is active", "No active 512 MiB swap was detected", remote=True),
                C("fstab_swap", 7, "grep -Ev '^[[:space:]]*(#|$)' /etc/fstab | grep -Eq '[[:space:]]+swap[[:space:]]+defaults'",
                  "Swap is persistent in /etc/fstab", "Persistent swap entry was not found", remote=True),
            ]),

        PaperTask("n2_05_exam_lv_mount", 2, "lvm", 18,
            "On node2, create volume group Exam and logical volume RHCSA sized 750 MiB. Format it as ext3 and mount it persistently at /root/exam.", [
                C("vg", 3, "vgs Exam >/dev/null 2>&1",
                  "VG Exam exists", "VG Exam does not exist", remote=True),
                C("lv", 3, "lvs /dev/Exam/RHCSA >/dev/null 2>&1",
                  "LV Exam/RHCSA exists", "LV /dev/Exam/RHCSA does not exist", remote=True),
                C("size", 3, "s=$(lvs --noheadings --units m --nosuffix -o lv_size /dev/Exam/RHCSA 2>/dev/null | awk '{print int($1)}'); test -n \"$s\" && test $s -ge 749 && test $s -le 753",
                  "LV size is about 750 MiB", "LV size is not about 750 MiB", remote=True),
                C("ext3", 3, "blkid -o value -s TYPE /dev/Exam/RHCSA | grep -qx ext3",
                  "Filesystem is ext3", "Filesystem is not ext3", remote=True),
                C("mounted", 3, "findmnt -rn /root/exam | grep -Eq '/dev/mapper/Exam-RHCSA|/dev/Exam/RHCSA'",
                  "/root/exam is mounted from Exam/RHCSA", "/root/exam is not mounted from Exam/RHCSA", remote=True),
                C("fstab", 3, "grep -Ev '^[[:space:]]*(#|$)' /etc/fstab | grep -Eq '[[:space:]]/root/exam[[:space:]]+ext3[[:space:]]'",
                  "Persistent /root/exam fstab entry exists", "Persistent /root/exam ext3 entry missing", remote=True),
            ]),

        PaperTask("n2_06_tuned", 2, "services", 10,
            "On node2, install and enable tuned, then apply the tuned profile recommended for the system.", [
                C("enabled_active", 4, "systemctl is-enabled --quiet tuned && systemctl is-active --quiet tuned",
                  "tuned is enabled and active", "tuned is not enabled and active", remote=True),
                C("recommended", 6, "test \"$(tuned-adm active | sed 's/.*: //')\" = \"$(tuned-adm recommend)\"",
                  "Recommended tuned profile is active", "Active tuned profile is not the recommended profile", remote=True),
            ]),
    ]
    return tasks
