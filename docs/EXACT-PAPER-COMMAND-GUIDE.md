# RHCSA Exact Paper Command Guide

This is a private study guide for the exact 21-question simulator profile.  It is not displayed during the exam unless opened manually.

## Node1 Quick Commands

### 1. Network and hostname

```bash
hostnamectl set-hostname node1.domain7.example.com
nmcli con mod "System eth0" ipv4.addresses 172.24.7.10/24 ipv4.gateway 172.24.7.254 ipv4.dns 172.24.7.254 ipv4.method manual connection.autoconnect yes
nmcli con up "System eth0"
```

### 2. Repositories

```bash
cat >/etc/yum.repos.d/rhcsa.repo <<'EOF'
[BaseOS]
name=BaseOS
baseurl=http://content.example.com/rhel9/x86_64/dvd/BaseOS
enabled=1
gpgcheck=0

[AppStream]
name=AppStream
baseurl=http://content.example.com/rhel9/x86_64/dvd/AppStream
enabled=1
gpgcheck=0
EOF
dnf clean all
dnf repolist
```

### 3. Web server, SELinux, firewall

```bash
dnf install -y httpd policycoreutils-python-utils firewalld
cat >/etc/httpd/conf.d/port82.conf <<'EOF'
Listen 82
<VirtualHost *:82>
    DocumentRoot /var/www/html
</VirtualHost>
EOF
semanage port -a -t http_port_t -p tcp 82 || semanage port -m -t http_port_t -p tcp 82
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-port=82/tcp
firewall-cmd --reload
systemctl enable --now httpd
```

### 4. Users and groups

```bash
groupadd adminuser
useradd -G adminuser harry
useradd -G adminuser natasha
useradd -s /sbin/nologin sarah
echo postroll | passwd --stdin harry
echo postroll | passwd --stdin natasha
echo postroll | passwd --stdin sarah
```

### 5. Cron

```bash
crontab -u natasha -e
# add:
23 14 * * * /bin/echo Haiya
```

### 6. Collaborative directory

```bash
mkdir -p /home/admin
chown root:adminuser /home/admin
chmod 2770 /home/admin
```

### 7. User alex

```bash
useradd -u 3456 alex
echo postroll | passwd --stdin alex
```

### 8. Find files owned by aletha

```bash
mkdir -p /root/find
find / -user aletha -type f -exec cp -rvp {} /root/find/ \; 2>/dev/null
```

### 9. Grep asse

```bash
grep 'asse' /usr/share/dict/words > /root/lines
```

### 10. Autofs

```bash
dnf install -y autofs nfs-utils
cat >/etc/auto.master.d/remoteuser.autofs <<'EOF'
/remote /etc/auto.remoteuser
EOF
cat >/etc/auto.remoteuser <<'EOF'
remoteuser20 -rw 172.24.20.250:/home/remoteuser20
EOF
systemctl enable --now autofs
systemctl restart autofs
ls /remote/remoteuser20
```

### 11. Archive

```bash
tar -cjvf /root/backup.tar.bz2 /usr/local/
```

### 12. Script

```bash
cat >/usr/local/bin/myscript <<'EOF'
#!/bin/bash
find /usr/share -type f -size -10M -perm -g=s > /root/script 2>/dev/null
EOF
chmod +x /usr/local/bin/myscript
/usr/local/bin/myscript
```

### 13. Chrony

```bash
dnf install -y chrony
printf 'server redhat.domain7.example.com iburst\n' >> /etc/chrony.conf
systemctl enable --now chronyd
systemctl restart chronyd
```

### 14. Podman image

```bash
su - aletha
wget http://domain.exam.com/rhel9/Containerfile
podman build -t monitor .
podman images
```

### 15. Podman container and user service

```bash
# root
mkdir -p /opt/input /opt/output
chown -R aletha:aletha /opt/input /opt/output
loginctl enable-linger aletha

# aletha
su - aletha
podman run -d --name asciipdf -v /opt/input:/opt/incoming:Z -v /opt/output:/opt/processed:Z localhost/monitor:latest
mkdir -p ~/.config/systemd/user
podman generate systemd --name asciipdf --files --new
mv container-asciipdf.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now container-asciipdf.service
```

## Node2 Quick Commands

### 16. Root password reset

Use GRUB edit, append `rd.break`, then:

```bash
mount -o remount,rw /sysroot
chroot /sysroot
passwd root
touch /.autorelabel
exit
exit
```

### 17. Repositories

Use the same repo file from Node1.

### 18. Resize LV data

```bash
lvextend -r -L 750M /dev/<VG>/data
```

### 19. Add 512 MiB swap

```bash
fdisk /dev/<disk>
# create 512M partition, set type Linux swap
partprobe
mkswap /dev/<partition>
blkid /dev/<partition>
# add UUID to /etc/fstab:
UUID=<uuid> none swap defaults 0 0
swapon -a
swapon --show
```

### 20. Create Exam/RHCSA LV

```bash
pvcreate /dev/<partition>
vgcreate Exam /dev/<partition>
lvcreate -L 750M -n RHCSA Exam
mkfs.ext3 /dev/Exam/RHCSA
mkdir -p /root/exam
blkid /dev/Exam/RHCSA
# add UUID to /etc/fstab:
UUID=<uuid> /root/exam ext3 defaults 0 0
mount -a
findmnt /root/exam
```

### 21. Tuned

```bash
dnf install -y tuned
systemctl enable --now tuned
tuned-adm recommend
tuned-adm profile $(tuned-adm recommend)
tuned-adm active
```
