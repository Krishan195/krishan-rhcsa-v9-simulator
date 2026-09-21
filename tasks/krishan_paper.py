"""Deterministic two-node RHCSA v9 mock paper.

The task wording in this module is original.  It mirrors public EX200 v9
objectives and a two-node practical-exam workflow without reproducing any
third-party question paper.
"""

import os
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
    """Fixed task whose checks are shell predicates (exit 0 means pass)."""

    def __init__(self, task_id, node, category, points, description, checks,
                 requires_persistence=True):
        super().__init__(task_id, category, "exam", points)
        self.node = node
        self.description = description
        self.checks_spec = tuple(checks)
        self.requires_persistence = requires_persistence
        self.requires_lab_machine = node == 2
        self.tags = ["krishan-fixed-paper", f"node-{node}"]
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
                message += f" ({output.strip()[:180]})"
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
            return ValidationResult(
                self.id, False, 0, self.points, [result])
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
        return ValidationResult(
            self.id, score >= self.points * 0.70, score, self.points, rendered)


def C(name, points, script, success, failure, remote=False):
    return ShellCheck(name, points, script, success, failure, remote)


def build_exam_tasks():
    """Return the fixed paper in exam order: node 1, then node 2."""
    tasks = [
        PaperTask("n1_01_network", 1, "networking", 15,
            "On node 1, set the persistent hostname to node1.practice9.example.test. "
            "Create or update a NetworkManager profile for dummy0 with IPv4 address "
            "192.168.56.101/24, gateway 192.168.56.1, DNS 192.168.56.1, manual IPv4, "
            "and autoconnect enabled. Do not change the VM's management interface.", [
                C("hostname", 5, "test \"$(hostnamectl --static)\" = node1.practice9.example.test",
                  "Persistent hostname is correct", "Persistent hostname is incorrect"),
                C("address", 5, "nmcli -g ipv4.addresses con show exam-dummy | grep -Fxq 192.168.56.101/24",
                  "IPv4 address is correct", "Connection exam-dummy does not have the required address"),
                C("network_profile", 5, "test \"$(nmcli -g ipv4.method con show exam-dummy)\" = manual && test \"$(nmcli -g connection.autoconnect con show exam-dummy)\" = yes",
                  "Network profile is persistent", "Manual addressing/autoconnect is not configured"),
            ]),
        PaperTask("n1_02_repositories", 1, "repos", 12,
            "On node 1, configure enabled DNF repositories named training-baseos and "
            "training-appstream. Use http://repo.practice.example/rhel9/BaseOS and "
            "http://repo.practice.example/rhel9/AppStream respectively. Disable GPG "
            "checking for these isolated lab repositories.", [
                C("baseos", 6, "dnf repolist --all 2>/dev/null | grep -q '^training-baseos.*enabled' && grep -Rqs 'baseurl=http://repo.practice.example/rhel9/BaseOS' /etc/yum.repos.d",
                  "BaseOS repository is configured", "BaseOS repository is missing or disabled"),
                C("appstream", 6, "dnf repolist --all 2>/dev/null | grep -q '^training-appstream.*enabled' && grep -Rqs 'baseurl=http://repo.practice.example/rhel9/AppStream' /etc/yum.repos.d",
                  "AppStream repository is configured", "AppStream repository is missing or disabled"),
            ]),
        PaperTask("n1_03_web_security", 1, "selinux", 18,
            "An Apache service on node 1 is configured for TCP ports 80 and 8082. "
            "Make the service start successfully under enforcing SELinux and permit "
            "both ports through the firewall. Preserve the standard HTTP port.", [
                C("service", 6, "systemctl is-active --quiet httpd", "Apache is active", "Apache is not active"),
                C("selinux_port", 6, "semanage port -l | awk '$1==\"http_port_t\" && $2==\"tcp\" {$1=$2=\"\"; print}' | grep -qw 8082",
                  "SELinux permits Apache on 8082", "Port 8082 is not labelled http_port_t"),
                C("firewall", 6, "firewall-cmd --quiet --query-service=http && firewall-cmd --quiet --query-port=8082/tcp && firewall-cmd --quiet --permanent --query-service=http && firewall-cmd --quiet --permanent --query-port=8082/tcp",
                  "Runtime and permanent firewall rules are correct", "Required firewall rules are incomplete"),
            ]),
        PaperTask("n1_04_accounts", 1, "users_groups", 15,
            "Create group opsadmin. Create users leon and nadia with opsadmin as a "
            "supplementary group. Create user mina with a non-interactive shell and "
            "without opsadmin membership. Assign a usable password to all three users.", [
                C("group_members", 6, "getent group opsadmin >/dev/null && id -nG leon | grep -qw opsadmin && id -nG nadia | grep -qw opsadmin",
                  "Group memberships are correct", "opsadmin or required memberships are missing"),
                C("restricted_user", 5, "getent passwd mina | cut -d: -f7 | grep -Eq '(nologin|false)$' && ! id -nG mina | grep -qw opsadmin",
                  "Restricted user is correct", "mina has an interactive shell or incorrect membership"),
                C("passwords", 4, "for u in leon nadia mina; do passwd -S $u | awk '$2==\"P\" {ok=1} END{exit !ok}' || exit 1; done",
                  "All accounts have passwords", "One or more accounts have no usable password"),
            ]),
        PaperTask("n1_05_cron", 1, "scheduling", 10,
            "Schedule /usr/bin/logger 'RHCSA practice heartbeat' for user nadia at "
            "14:23 every day.", [
                C("cron", 10, "crontab -u nadia -l 2>/dev/null | grep -Eq '^23[[:space:]]+14[[:space:]]+\\*[[:space:]]+\\*[[:space:]]+\\*[[:space:]]+/usr/bin/logger[[:space:]]+([\"\x27])?RHCSA practice heartbeat'",
                  "Daily cron job is correct", "Required cron entry was not found"),
            ]),
        PaperTask("n1_06_collaboration", 1, "permissions", 12,
            "Create /srv/ops-share as a collaborative directory owned by group "
            "opsadmin. Group members require full access, other users require no "
            "access, and newly created files must inherit the opsadmin group.", [
                C("ownership", 4, "test \"$(stat -c %G /srv/ops-share)\" = opsadmin",
                  "Group ownership is correct", "Directory group is not opsadmin"),
                C("permissions", 8, "mode=$(stat -c %a /srv/ops-share); test \"$mode\" = 2770",
                  "Permissions and setgid are correct", "Expected mode 2770"),
            ]),
        PaperTask("n1_07_fixed_uid", 1, "users_groups", 8,
            "Create user devtest with UID 3456 and assign a usable password.", [
                C("uid", 5, "test \"$(id -u devtest 2>/dev/null)\" = 3456", "UID is correct", "devtest with UID 3456 was not found"),
                C("password", 3, "passwd -S devtest | awk '$2==\"P\" {ok=1} END{exit !ok}'", "Password is set", "Password is not usable"),
            ]),
        PaperTask("n1_08_find_files", 1, "essential_tools", 10,
            "Locate every regular file owned by user fileowner beneath /var/tmp/exam-source "
            "and copy it into /root/owned-files while preserving file metadata.", [
                C("copies", 10, "src=$(find /var/tmp/exam-source -xdev -user fileowner -type f -printf '%f\\n' | sort); dst=$(find /root/owned-files -maxdepth 1 -user fileowner -type f -printf '%f\\n' 2>/dev/null | sort); test -n \"$src\" && test \"$src\" = \"$dst\"",
                  "All owned files were copied with ownership preserved", "Destination does not contain the complete preserved file set"),
            ], False),
        PaperTask("n1_09_filter_text", 1, "essential_tools", 8,
            "From /opt/exam-assets/words.list, write every complete line containing "
            "the text 'mesh' to /root/mesh-lines. The destination must contain no "
            "blank lines or leading/trailing whitespace.", [
                C("filtered_output", 8, "test -f /root/mesh-lines && diff -u <(grep 'mesh' /opt/exam-assets/words.list | sed '/^[[:space:]]*$/d;s/^[[:space:]]*//;s/[[:space:]]*$//') /root/mesh-lines",
                  "Filtered output is exact", "Filtered file content is incomplete or incorrectly formatted"),
            ], False),
        PaperTask("n1_10_autofs", 1, "network_storage", 18,
            "Configure autofs on node 1 so the remote user's NFS home exported as "
            "node2:/exports/home/labuser is available on demand at /remote/labuser. "
            "The mounted home must be writable by labuser.", [
                C("autofs_config", 6, "grep -RqsE '^/remote[[:space:]]+' /etc/auto.master /etc/auto.master.d && grep -RqsE '^labuser[[:space:]]+.*node2:/exports/home/labuser' /etc/auto.*",
                  "Autofs maps are configured", "Required master/direct map entries were not found"),
                C("autofs_service", 4, "systemctl is-enabled --quiet autofs && systemctl is-active --quiet autofs",
                  "Autofs is enabled and active", "Autofs is not enabled and active"),
                C("mount", 8, "timeout 10 bash -c 'ls /remote/labuser >/dev/null' && findmnt -rn /remote/labuser >/dev/null",
                  "Remote home mounts on demand", "Remote home did not mount at /remote/labuser"),
            ]),
        PaperTask("n1_11_archive", 1, "essential_tools", 10,
            "Create the bzip2-compressed archive /root/local-config.tar.bz2 containing "
            "the complete /usr/local directory tree.", [
                C("archive", 10, "test -f /root/local-config.tar.bz2 && tar -tjf /root/local-config.tar.bz2 | grep -Eq '(^|/)usr/local/?$|^usr/local/'",
                  "Compressed archive is valid", "Archive is missing, invalid, or lacks /usr/local"),
            ], False),
        PaperTask("n1_12_script", 1, "scripting", 15,
            "Create executable script /usr/local/bin/find-special-files. When run, it "
            "must overwrite /root/special-files with paths of regular files under "
            "/usr/share that are at most 10 MiB and have the set-group-ID bit set.", [
                C("script", 5, "test -x /usr/local/bin/find-special-files && head -1 /usr/local/bin/find-special-files | grep -q '^#!'",
                  "Executable script exists", "Script is missing or not executable"),
                C("result", 10, "/usr/local/bin/find-special-files && diff -u <(find /usr/share -type f -size -10M -perm -2000 | sort) <(sort /root/special-files)",
                  "Script produces the required file list", "Script output does not match the requirement"),
            ], False),
        PaperTask("n1_13_time", 1, "time_services", 10,
            "Configure chronyd on node 1 to use time.practice9.example.test with "
            "iburst. Ensure chronyd is enabled and running.", [
                C("source", 5, "grep -RqsE '^[[:space:]]*(server|pool)[[:space:]]+time\\.practice9\\.example\\.test([[:space:]]+.*)?iburst' /etc/chrony.conf /etc/chrony.d 2>/dev/null",
                  "Chrony source is configured", "Required time source with iburst was not found"),
                C("service", 5, "systemctl is-enabled --quiet chronyd && systemctl is-active --quiet chronyd",
                  "Chronyd is enabled and active", "Chronyd is not enabled and active"),
            ]),
        PaperTask("n1_14_image", 1, "containers", 12,
            "As user containeruser, build a local Podman image named report-tool from "
            "/opt/exam-assets/Containerfile. Do not edit the supplied Containerfile.", [
                C("image", 12, "runuser -u containeruser -- podman image exists localhost/report-tool:latest",
                  "Required image exists for containeruser", "report-tool image was not found for containeruser"),
            ], False),
        PaperTask("n1_15_container_service", 1, "containers", 20,
            "As user containeruser, create container report-worker from report-tool. "
            "Map /opt/report/in to /work/in and /opt/report/out to /work/out with "
            "SELinux-compatible labels. Configure it as a user systemd service named "
            "container-report-worker.service that starts automatically after boot.", [
                C("container", 6, "runuser -u containeruser -- podman inspect report-worker >/dev/null",
                  "Container exists", "report-worker container was not found"),
                C("mounts", 6, "runuser -u containeruser -- podman inspect report-worker --format '{{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}' | grep -q '/opt/report/in:/work/in' && runuser -u containeruser -- podman inspect report-worker --format '{{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}' | grep -q '/opt/report/out:/work/out'",
                  "Bind mounts are correct", "One or both bind mounts are incorrect"),
                C("service", 8, "test -f /home/containeruser/.config/systemd/user/container-report-worker.service && loginctl show-user containeruser -p Linger --value | grep -qx yes && runuser -u containeruser -- env XDG_RUNTIME_DIR=/run/user/$(id -u containeruser) systemctl --user is-enabled --quiet container-report-worker.service",
                  "Persistent user service is enabled", "User service or lingering is not configured"),
            ]),
        RootRecoveryTask("n2_01_root_recovery", 2, "boot_recovery", 20,
            "At the node 2 console, recover administrative access by assigning a new "
            "root password. Boot node 2 normally afterward and ensure SELinux labels "
            "remain correct.", []),
        PaperTask("n2_02_repositories", 2, "repos", 12,
            "On node 2, configure the same enabled training-baseos and "
            "training-appstream repositories used on node 1, with GPG checking "
            "disabled for this isolated lab.", [
                C("baseos", 6, "dnf repolist --all 2>/dev/null | grep -q '^training-baseos.*enabled'", "BaseOS repository is enabled", "BaseOS repository is not enabled", True),
                C("appstream", 6, "dnf repolist --all 2>/dev/null | grep -q '^training-appstream.*enabled'", "AppStream repository is enabled", "AppStream repository is not enabled", True),
            ]),
        PaperTask("n2_03_resize_lv", 2, "lvm", 18,
            "On node 2, extend logical volume /dev/ExamData/data and its existing "
            "ext4 filesystem to 750 MiB without losing the file already stored on it.", [
                C("lv_size", 8, "size=$(lvs --noheadings --nosuffix --units m -o lv_size ExamData/data | xargs | cut -d. -f1); test \"$size\" -ge 740", "Logical volume size is correct", "Logical volume is smaller than required", True),
                C("filesystem", 6, "findmnt -rn /srv/existing-data >/dev/null && test $(df -Pm /srv/existing-data | awk 'NR==2 {print $2}') -ge 700", "Filesystem was grown", "Mounted filesystem was not grown", True),
                C("data", 4, "test -s /srv/existing-data/keep-this-file", "Existing data was preserved", "Baseline data is missing", True),
            ]),
        PaperTask("n2_04_swap", 2, "swap", 15,
            "On node 2, create an additional swap area of approximately 512 MiB "
            "using unused space on /dev/vdb. Activate it and make it persistent. "
            "Do not remove existing swap.", [
                C("active_swap", 8, "swapon --show --bytes --noheadings --output SIZE | awk '$1>=500*1024*1024 && $1<=540*1024*1024 {ok=1} END{exit !ok}'", "Additional swap is active", "No active swap of approximately 512 MiB was found", True),
                C("persistent", 7, "grep -vE '^[[:space:]]*#|^[[:space:]]*$' /etc/fstab | awk '$3==\"swap\" {ok=1} END{exit !ok}'", "Swap has a persistent fstab entry", "Persistent swap entry was not found", True),
            ]),
        PaperTask("n2_05_new_lvm", 2, "lvm", 20,
            "Using unused space on /dev/vdb, create volume group ProjectVG and a "
            "750 MiB logical volume named ProjectLV. Format it as ext3 and mount it "
            "persistently at /srv/project.", [
                C("lvm", 8, "lvs ProjectVG/ProjectLV >/dev/null && size=$(lvs --noheadings --nosuffix --units m -o lv_size ProjectVG/ProjectLV | xargs | cut -d. -f1); test \"$size\" -ge 740", "VG and LV are correct", "ProjectVG/ProjectLV is missing or incorrectly sized", True),
                C("filesystem", 6, "test \"$(blkid -s TYPE -o value /dev/ProjectVG/ProjectLV)\" = ext3", "Filesystem is ext3", "Logical volume is not formatted as ext3", True),
                C("mount", 6, "findmnt -rn /srv/project >/dev/null && grep -vE '^[[:space:]]*#' /etc/fstab | grep -qE '[[:space:]]/srv/project[[:space:]]'", "Persistent mount is correct", "Mount is not active and persistent", True),
            ]),
        PaperTask("n2_06_tuned", 2, "services", 10,
            "On node 2, enable tuned and activate the profile recommended for that "
            "virtual machine.", [
                C("service", 4, "systemctl is-enabled --quiet tuned && systemctl is-active --quiet tuned", "Tuned is enabled and active", "Tuned is not enabled and active", True),
                C("profile", 6, "test \"$(tuned-adm active 2>/dev/null | sed -n 's/^Current active profile: //p')\" = \"$(tuned-adm recommend 2>/dev/null)\"", "Recommended tuned profile is active", "Active tuned profile is not the recommended profile", True),
            ]),
    ]
    for index, task in enumerate(tasks, 1):
        task.task_order = index
    return tasks


PAPER_TASK_COUNT = 21
PAPER_MAX_SCORE = sum(t.points for t in build_exam_tasks())
