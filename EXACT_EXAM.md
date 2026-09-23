# Exact RHCSA v9 Practice Paper Build

This build is locked to the exact 21-question paper used in Krishan's RHCSA v9 practice session.

- Node1: 15 questions
- Node2: 6 questions
- Duration: 180 minutes
- Default mode: fixed paper only
- Random upstream tasks are not selected in Exam Mode

## Question Set

### Node1

1. Configure hostname `node1.domain7.example.com` and network `172.24.7.10/24`, gateway/DNS `172.24.7.254`.
2. Configure BaseOS/AppStream repositories from `http://content.example.com/rhel9/x86_64/dvd/` with `gpgcheck=0`.
3. Configure `httpd` on ports `80` and `82` with SELinux and firewall rules.
4. Create group `adminuser`; users `harry`, `natasha`, `sarah`; set required shells, memberships, and passwords.
5. Configure `natasha` cron job at `14:23` to run `/bin/echo Haiya`.
6. Configure collaborative directory `/home/admin` with group `adminuser` and mode `2770`.
7. Create user `alex` with UID `3456`.
8. Copy regular files owned by `aletha` to `/root/find` preserving attributes.
9. Save words containing `asse` from `/usr/share/dict/words` to `/root/lines`.
10. Configure autofs for `/remote/remoteuser20` from `172.24.20.250:/home/remoteuser20`.
11. Create `/root/backup.tar.bz2` containing `/usr/local`.
12. Create executable `/usr/local/bin/myscript` to find SGID files under `/usr/share` smaller than 10 MB and write to `/root/script`.
13. Configure chrony source `redhat.domain7.example.com`.
14. As `aletha`, build Podman image `monitor` from the provided `Containerfile`.
15. As `aletha`, create container `asciipdf` with `/opt/input:/opt/incoming`, `/opt/output:/opt/processed`, and user systemd autostart.

### Node2

16. Reset root password to `postroll` using `rd.break` rescue procedure.
17. Configure the same BaseOS/AppStream repositories.
18. Resize existing LV `data` to final size `750 MiB` and resize its ext4 filesystem.
19. Add a new persistent `512 MiB` swap partition.
20. Create VG `Exam`, LV `RHCSA` size `750 MiB`, format ext3, mount persistently at `/root/exam`.
21. Enable tuned and apply the system recommended profile.

## Run

```bash
sudo rhcsa-simulator --exam
```

For a two-node lab, link node2 first if your installation uses SSH validation:

```bash
sudo rhcsa-simulator --link-node2 root@serverb
sudo rhcsa-simulator --prepare-lab
sudo rhcsa-simulator --exam
```

Use disposable VMs or snapshots. The tasks intentionally modify networking, users, storage, SELinux, firewall, services, boot configuration, and containers.