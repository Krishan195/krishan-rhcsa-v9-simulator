"""Explicit lab preparation for the deterministic two-node paper."""

import os
import subprocess

from core import lab_machine


LOCAL_SETUP = r'''
set -e
getent passwd fileowner >/dev/null || useradd fileowner
getent passwd containeruser >/dev/null || useradd -m containeruser
mkdir -p /var/tmp/exam-source/a /var/tmp/exam-source/b /opt/exam-assets
printf 'one\n' >/var/tmp/exam-source/a/report-one.txt
printf 'two\n' >/var/tmp/exam-source/b/report-two.txt
chown -R fileowner:fileowner /var/tmp/exam-source
cat >/opt/exam-assets/words.list <<'EOF'
mesh
meshed
framework
enmeshment
shell
EOF
cat >/opt/exam-assets/Containerfile <<'EOF'
FROM registry.access.redhat.com/ubi9/ubi-minimal
CMD ["/bin/sh", "-c", "while true; do sleep 3600; done"]
EOF
mkdir -p /opt/report/in /opt/report/out
chown -R containeruser:containeruser /opt/report
if command -v nmcli >/dev/null 2>&1; then
  nmcli con show exam-dummy >/dev/null 2>&1 || \
    nmcli con add type dummy ifname dummy0 con-name exam-dummy ipv4.method disabled ipv6.method disabled
fi
if rpm -q httpd >/dev/null 2>&1; then
  mkdir -p /var/www/html
  printf 'RHCSA practice web service\n' >/var/www/html/index.html
  cat >/etc/httpd/conf.d/exam-8082.conf <<'EOF'
Listen 8082
<VirtualHost *:8082>
    DocumentRoot /var/www/html
</VirtualHost>
EOF
fi
'''


REMOTE_SETUP = r'''
set -e
getent passwd labuser >/dev/null || useradd -m labuser
mkdir -p /exports/home/labuser
chown labuser:labuser /exports/home/labuser
if command -v exportfs >/dev/null 2>&1; then
  grep -q '^/exports/home/labuser ' /etc/exports 2>/dev/null || \
    printf '/exports/home/labuser *(rw,sync,no_subtree_check)\n' >>/etc/exports
  exportfs -ra
fi

# A loop-backed baseline LV keeps preparation away from the VM's real disks.
mkdir -p /var/lib/rhcsa-simulator /srv/existing-data
if ! lvs ExamData/data >/dev/null 2>&1; then
  truncate -s 1100M /var/lib/rhcsa-simulator/existing-data.img
  loop=$(losetup -f --show /var/lib/rhcsa-simulator/existing-data.img)
  pvcreate -ff -y "$loop"
  vgcreate ExamData "$loop"
  lvcreate -L 400M -n data ExamData
  mkfs.ext4 -F /dev/ExamData/data
fi
grep -qE '[[:space:]]/srv/existing-data[[:space:]]' /etc/fstab || \
  printf '/dev/ExamData/data /srv/existing-data ext4 defaults 0 0\n' >>/etc/fstab
mountpoint -q /srv/existing-data || mount /srv/existing-data
printf 'This file must survive the resize.\n' >/srv/existing-data/keep-this-file
'''


def prepare():
    """Prepare safe local artifacts and a loop-backed node-2 baseline.

    This deliberately does not partition /dev/vdb.  The candidate owns that
    disposable practice disk during the exam.
    """
    if os.geteuid() != 0:
        return False, "Run lab preparation as root."
    local = subprocess.run(
        ["bash", "-o", "pipefail", "-c", LOCAL_SETUP],
        text=True, capture_output=True)
    if local.returncode:
        return False, "Node 1 preparation failed: " + (local.stderr or local.stdout)[-500:]
    if not lab_machine.key_works():
        return False, ("Node 1 is prepared, but node 2 is not linked. Run "
                       "--link-node2 first, then repeat --prepare-lab.")
    rc, output = lab_machine.run(REMOTE_SETUP, timeout=180)
    if rc != 0:
        return False, "Node 2 preparation failed: " + (output or "")[-500:]
    return True, ("Both nodes are prepared. Attach an unused 3 GiB or larger "
                  "disk as /dev/vdb on node 2, then take VM snapshots.")

