# Krishan RHCSA v9 Simulator

A deterministic, original-worded two-node RHCSA (EX200 v9) mock exam. It
contains one fixed 21-task paper rather than a randomized question bank.

This project is derived from
[TroggoMan/rhcsa-simulator](https://github.com/TroggoMan/rhcsa-simulator)
under the MIT License. The fixed paper in this edition was independently
written from public RHCSA v9 objectives; it does not reproduce a real exam or
third-party answer sheet.

## Coverage

- Node 1: networking, repositories, Apache/SELinux/firewalld, accounts, cron,
  permissions, file tools, autofs/NFS, archives, scripting, chrony, and
  rootless Podman/systemd.
- Node 2: console root recovery, repositories, LVM/filesystem growth, swap,
  persistent ext3 storage, and tuned.
- 21 ordered tasks, three-hour timer, browser task panel, and partial scoring.

## Required lab

Use two disposable RHEL 9, Rocky Linux 9, or AlmaLinux 9 VMs. Take snapshots.

- Node 1: 2 vCPU, 4 GiB RAM, 20 GiB OS disk.
- Node 2: 2 vCPU, 4 GiB RAM, 20 GiB OS disk, plus an unused disk of at least
  3 GiB exposed as `/dev/vdb`.
- Node 1 must reach node 2 over SSH.
- Keep console access to node 2 for boot recovery.

Never run this on a production server or daily-use workstation. The exam
changes users, services, firewall rules, SELinux, storage, mounts, and boot
state.

## Install on node 1

```bash
sudo -i
git clone https://github.com/Krishan195/krishan-rhcsa-v9-simulator.git
cd krishan-rhcsa-v9-simulator
./install.sh
```

Install the required packages on both VMs:

```bash
dnf install -y httpd policycoreutils-python-utils firewalld NetworkManager \
  chrony cronie autofs nfs-utils lvm2 podman tuned bzip2
```

## Link and prepare node 2

Run on node 1, replacing the address with node 2's management IP:

```bash
sudo rhcsa-simulator --link-node2 192.168.56.102
sudo rhcsa-simulator --prepare-lab
```

Preparation creates safe source files, a dummy network profile, container
assets, the NFS export, and a loop-backed node-2 resize exercise. It does not
partition or format `/dev/vdb`; that disposable disk is reserved for the exam.
Take fresh snapshots of both VMs after preparation.

## Start

```bash
sudo rhcsa-simulator --exam
```

Terminal-only mode:

```bash
sudo rhcsa-simulator --exam --no-gui
```

The browser panel uses port 8080. The guarded node-2 recovery scenario verifies
key-based SSH before changing the root password and preserves recovery state.

## Lab notes

- The repository and time-server hostnames are reserved training names. Provide
  matching private services if live connectivity is required.
- Cache the UBI image before disconnecting the lab:

  ```bash
  sudo -u containeruser podman pull registry.access.redhat.com/ubi9/ubi-minimal
  ```
- Revert both VM snapshots after an attempt for the most reliable cleanup.

## License

MIT. See [LICENSE](LICENSE). Retain the existing copyright and license notice
when redistributing modified copies.
