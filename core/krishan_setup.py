"""Explicit lab preparation for the exact two-node RHCSA paper.

Preparation creates safe practice artifacts only.  It does not solve any task.
It gives the candidate realistic objects to work on: an existing data LV on
node2, sample files owned by aletha, a dictionary file, and a local copy of the
Containerfile for offline labs.
"""

import os
import subprocess

from core import lab_machine


LOCAL_SETUP = r'''
set -e
getent passwd aletha >/dev/null || useradd -m aletha
mkdir -p /var/tmp/krishan-owned/a /var/tmp/krishan-owned/b /opt/exam-assets
printf 'owned by aletha one\n' >/var/tmp/krishan-owned/a/aletha-one.txt
printf 'owned by aletha two\n' >/var/tmp/krishan-owned/b/aletha-two.txt
chown -R aletha:aletha /var/tmp/krishan-owned
mkdir -p /usr/share/dict
if [ ! -s /usr/share/dict/words ]; then
  cat >/usr/share/dict/words <<'EOF'
passenger
assembled
assessment
classic
classed
asset
message
EOF
fi
cat >/opt/exam-assets/Containerfile <<'EOF'
FROM registry.access.redhat.com/ubi9/ubi
CMD ["sleep", "infinity"]
EOF
mkdir -p /var/www/html
printf 'RHCSA exact paper web service\n' >/var/www/html/index.html
if rpm -q httpd >/dev/null 2>&1; then
  if ! grep -Rqs '^[[:space:]]*Listen[[:space:]]\+82' /etc/httpd/conf /etc/httpd/conf.d 2>/dev/null; then
    cat >/etc/httpd/conf.d/exam-82.conf <<'EOF'
Listen 82
<VirtualHost *:82>
    DocumentRoot /var/www/html
</VirtualHost>
EOF
  fi
fi
'''


REMOTE_SETUP = r'''
set -e
# NFS export used by local practice for the autofs task.  In the real exam the
# server is supplied separately as 172.24.20.250.
getent passwd remoteuser20 >/dev/null || useradd -m remoteuser20
mkdir -p /home/remoteuser20
printf 'autofs test from node2\n' >/home/remoteuser20/testfile
chown -R remoteuser20:remoteuser20 /home/remoteuser20
if command -v exportfs >/dev/null 2>&1; then
  grep -q '^/home/remoteuser20 ' /etc/exports 2>/dev/null || \
    printf '/home/remoteuser20 *(rw,sync,no_root_squash)\n' >>/etc/exports
  systemctl enable --now nfs-server >/dev/null 2>&1 || true
  exportfs -ra || true
fi

# Existing data LV for question 18.  It uses a loop device so preparation does
# not consume or repartition the candidate's real practice disk.
mkdir -p /var/lib/rhcsa-simulator /srv/existing-data
if ! lvs -S 'lv_name=data' --noheadings -o lv_name 2>/dev/null | grep -qw data; then
  truncate -s 1200M /var/lib/rhcsa-simulator/existing-data.img
  loop=$(losetup -f --show /var/lib/rhcsa-simulator/existing-data.img)
  pvcreate -ff -y "$loop"
  vgcreate ExamData "$loop"
  lvcreate -L 400M -n data ExamData
  mkfs.ext4 -F /dev/ExamData/data
fi
if ! grep -qE '[[:space:]]/srv/existing-data[[:space:]]' /etc/fstab; then
  printf '/dev/ExamData/data /srv/existing-data ext4 defaults 0 0\n' >>/etc/fstab
fi
mountpoint -q /srv/existing-data || mount /srv/existing-data || true
printf 'This file must survive the resize.\n' >/srv/existing-data/keep-this-file
'''


def prepare():
    """Prepare local artifacts and a loop-backed node2 baseline."""
    if os.geteuid() != 0:
        return False, "Run lab preparation as root."
    local = subprocess.run(
        ["bash", "-o", "pipefail", "-c", LOCAL_SETUP],
        text=True, capture_output=True)
    if local.returncode:
        return False, "Node1 preparation failed: " + (local.stderr or local.stdout)[-500:]
    if not lab_machine.key_works():
        return False, ("Node1 is prepared, but node2 is not linked. Run "
                       "--link-node2 first, then repeat --prepare-lab.")
    rc, output = lab_machine.run(REMOTE_SETUP, timeout=180)
    if rc != 0:
        return False, "Node2 preparation failed: " + (output or "")[-500:]
    return True, ("Both nodes are prepared for the exact RHCSA paper. Attach an "
                  "unused practice disk to node2 for the swap and Exam/RHCSA "
                  "storage tasks, then take VM snapshots.")
