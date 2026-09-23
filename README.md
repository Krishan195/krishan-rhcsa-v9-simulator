# Krishan Exact RHCSA v9 Simulator

A deterministic two-node RHCSA v9 practice simulator aligned to the exact 21-question paper used in Krishan's practice session.

This project is derived from [TroggoMan/rhcsa-simulator](https://github.com/TroggoMan/rhcsa-simulator) under the MIT License and from the uploaded `krishan-rhcsa-v9-simulator` structure. This edited build replaces the previous generic mock questions with the exact paper tasks and validators.

## Coverage

- Node1: network/hostname, repositories, Apache on 80/82 with SELinux and firewall, users/groups, cron, collaborative directory, UID user, find/copy files, grep, autofs, archive, scripting, chrony, and rootless Podman image/container/systemd.
- Node2: root password reset, repositories, resize existing LV `data`, add persistent swap, create `Exam/RHCSA` ext3 mount, and tuned recommended profile.
- 21 ordered tasks, 180-minute timer, browser task panel, and partial scoring.

## Required lab

Use two disposable RHEL 9, Rocky Linux 9, or AlmaLinux 9 VMs. Take snapshots.

- Node1: 2 vCPU, 4 GiB RAM, 20 GiB OS disk.
- Node2: 2 vCPU, 4 GiB RAM, 20 GiB OS disk, plus an unused disk of at least 3 GiB exposed as `/dev/vdb` or another clearly unused disk.
- Node1 must reach node2 over SSH if you want remote validation for Node2.
- Keep console access to node2 for the root password reset task.

Never run this on a production server or daily-use workstation. The exam changes users, services, firewall rules, SELinux, storage, mounts, networking, containers, and boot state.

## Install on node1

```bash
sudo -i
git clone <your-repo-url>
cd krishan-rhcsa-v9-simulator
./install.sh
```

Install useful packages on both VMs:

```bash
dnf install -y httpd policycoreutils-python-utils firewalld NetworkManager \
  chrony cronie autofs nfs-utils lvm2 podman tuned bzip2 tar wget
```

## Link and prepare node2

Run on node1, replacing the address with node2's management IP or hostname:

```bash
sudo rhcsa-simulator --link-node2 serverb
sudo rhcsa-simulator --prepare-lab
```

Preparation creates safe practice artifacts only. It creates sample files owned by `aletha`, a dictionary file if missing, a local Containerfile copy for offline practice, an NFS export on node2 for local autofs practice, and a loop-backed existing LV named `data` on node2. It does not solve the tasks.

Take fresh VM snapshots after preparation.

## Start exam mode

```bash
sudo rhcsa-simulator --exam
```

Terminal-only mode:

```bash
sudo rhcsa-simulator --exam --no-gui
```

## Exact paper files

- `EXACT_EXAM.md` — exact question list and run notes.
- `docs/EXACT-PAPER-COMMAND-GUIDE.md` — private study guide with command examples.
- `docs/RHEL-9-RHCSA-Exam-Paper.pdf` — uploaded paper reference already included in the repo.

## Important lab notes

- The real paper uses training hostnames/IPs such as `content.example.com`, `redhat.domain7.example.com`, and `172.24.20.250`. Your practice lab may need DNS/hosts entries or local substitutions.
- For your offline Podman lab, the public Red Hat registry may not resolve. The study guide includes the real exam command flow; use a local base image workaround only for practice.
- Revert both VM snapshots after each full attempt for clean scoring.

## License

MIT. See [LICENSE](LICENSE). Retain the existing copyright and license notice when redistributing modified copies.