# RHCSA Simulator V3 Release Plan

## Overview
This document outlines the implementation plan for achieving 100% RHCSA EX200 exam objective coverage.

**Target:** Complete RHCSA EX200 coverage
**Current Coverage:** ~75-80%
**Post-V3 Coverage:** 100%

---

## 1. Shell Scripting Module (HIGH PRIORITY)

### Why Critical
- Shell scripting appears on nearly every RHCSA exam
- Typically 1-2 questions worth 5-10% of total score
- Tests fundamental Linux understanding

### New File: `tasks/scripting.py`

#### Task 1.1: CreateBasicScriptTask
- **Objective:** Write a script that performs a simple task
- **Skills tested:**
  - Shebang line (#!/bin/bash)
  - Making scripts executable (chmod +x)
  - Running scripts
- **Validation:**
  - Script exists and is executable
  - Script runs without errors
  - Script produces expected output

#### Task 1.2: ScriptWithArgumentsTask
- **Objective:** Write script that accepts positional parameters
- **Skills tested:**
  - Using $1, $2, $@, $#
  - Validating argument count
- **Example:** Script that creates a user with username from $1
- **Validation:**
  - Script accepts arguments
  - Handles missing arguments gracefully

#### Task 1.3: ScriptWithConditionalsTask
- **Objective:** Write script with if/else logic
- **Skills tested:**
  - if/then/else/fi syntax
  - Test conditions: -f, -d, -e, -z, -n
  - String and numeric comparisons
- **Example:** Script that checks if file exists before processing
- **Validation:**
  - Correct behavior for both branches

#### Task 1.4: ScriptWithLoopsTask
- **Objective:** Write script with for/while loops
- **Skills tested:**
  - for loops (for i in ...; do; done)
  - while loops
  - Loop over files, arguments, ranges
- **Example:** Script that processes all .log files in a directory
- **Validation:**
  - Loop executes correct number of times
  - All items processed

#### Task 1.5: ScriptExitCodesTask
- **Objective:** Handle exit codes in scripts
- **Skills tested:**
  - Checking $? after commands
  - Using exit with codes
  - Conditional execution (&&, ||)
- **Example:** Script that exits with error if command fails
- **Validation:**
  - Correct exit code returned

#### Task 1.6: ScriptCommandOutputTask
- **Objective:** Capture and use command output
- **Skills tested:**
  - Command substitution $(command) or `command`
  - Storing output in variables
  - Processing output
- **Example:** Script that counts users and reports
- **Validation:**
  - Output correctly captured and used

### Validation Approach
- Create temporary test scripts
- Execute with controlled inputs
- Check exit codes and output
- Verify file/system state changes

### Dependencies
- None (new standalone module)

---

## 2. NFS and Autofs Module (HIGH PRIORITY)

### Why Critical
- NFS mounting is a core sysadmin skill
- Autofs appears frequently on exams
- Tests understanding of network filesystems

### New File: `tasks/network_storage.py`

#### Task 2.1: MountNFSShareTask
- **Objective:** Mount an NFS share manually
- **Skills tested:**
  - showmount -e to discover exports
  - mount -t nfs syntax
  - NFS mount options (ro, rw, sync, async)
- **Validation:**
  - Mount point exists
  - Share is mounted (check /proc/mounts)
  - Correct options applied

#### Task 2.2: PersistentNFSMountTask
- **Objective:** Configure NFS mount in /etc/fstab
- **Skills tested:**
  - fstab NFS syntax
  - _netdev option for network mounts
  - Mount options for NFS
- **Validation:**
  - fstab entry exists with correct format
  - Mount works after systemctl daemon-reload

#### Task 2.3: ConfigureAutofsMasterTask
- **Objective:** Configure autofs master map
- **Skills tested:**
  - /etc/auto.master syntax
  - Understanding mount points and map files
  - Restarting autofs service
- **Validation:**
  - auto.master has correct entry
  - autofs service running

#### Task 2.4: ConfigureAutofsDirectMapTask
- **Objective:** Create autofs direct map for NFS
- **Skills tested:**
  - Direct map syntax (/- in master)
  - Map file format
  - NFS options in autofs
- **Validation:**
  - Map file exists with correct syntax
  - Mount triggers on access

#### Task 2.5: ConfigureAutofsIndirectMapTask
- **Objective:** Create autofs indirect map
- **Skills tested:**
  - Indirect map concept (relative paths)
  - Wildcard mounts (*)
  - Home directory automounting
- **Validation:**
  - Indirect mount works
  - Subdirectories auto-mount

#### Task 2.6: AutofsHomeDirectoriesTask
- **Objective:** Configure autofs for NFS home directories
- **Skills tested:**
  - /home automounting pattern
  - Wildcard substitution (&)
  - Integration with user login
- **Validation:**
  - User home directories mount on login

### Infrastructure Needed
- Mock NFS server simulation OR
- Documentation that user needs NFS server available
- Helper function to check NFS availability

### Dependencies
- Networking module (for connectivity)
- Services module (for autofs service)

---

## 3. Package Management Module (HIGH PRIORITY)

### Why Critical
- Installing packages is fundamental
- Repository configuration is commonly tested
- Every sysadmin needs these skills

### New File: `tasks/packages.py`

#### Task 3.1: InstallPackageTask
- **Objective:** Install a package using dnf
- **Skills tested:**
  - dnf install syntax
  - Confirming installation (-y flag)
  - Verifying installation
- **Validation:**
  - rpm -q shows package installed
  - Package files exist

#### Task 3.2: RemovePackageTask
- **Objective:** Remove a package
- **Skills tested:**
  - dnf remove syntax
  - Understanding dependencies
- **Validation:**
  - Package no longer installed

#### Task 3.3: InstallPackageGroupTask
- **Objective:** Install a package group
- **Skills tested:**
  - dnf group list
  - dnf group install
  - Understanding group structure
- **Validation:**
  - Group packages installed

#### Task 3.4: ConfigureRepoTask
- **Objective:** Add a new repository
- **Skills tested:**
  - /etc/yum.repos.d/ structure
  - Repository file format
  - gpgcheck, enabled, baseurl options
- **Validation:**
  - Repo file exists with correct format
  - dnf repolist shows new repo

#### Task 3.5: ConfigureRepoFromURLTask
- **Objective:** Add repository using dnf config-manager
- **Skills tested:**
  - dnf config-manager --add-repo
  - Enabling/disabling repos
- **Validation:**
  - Repository added and enabled

#### Task 3.6: SearchPackageTask
- **Objective:** Find packages providing a file/feature
- **Skills tested:**
  - dnf search
  - dnf provides
  - dnf info
- **Validation:**
  - Correct package identified

#### Task 3.7: DowngradePackageTask
- **Objective:** Downgrade to previous version
- **Skills tested:**
  - dnf downgrade
  - dnf history
  - Version management
- **Validation:**
  - Older version installed

#### Task 3.8: EnableModuleStreamTask
- **Objective:** Enable a specific module stream
- **Skills tested:**
  - dnf module list
  - dnf module enable
  - dnf module install
- **Validation:**
  - Correct stream enabled

### Validation Approach
- Use safe, common packages for testing
- Check rpm database
- Verify file installation

### Dependencies
- Network connectivity for repos
- Consider offline/mock mode

---

## 4. Disk Partitioning Module (MEDIUM PRIORITY)

### Why Critical
- Foundation for LVM and filesystems
- Tests understanding of disk structure
- May appear as part of larger storage tasks

### Updates to: `tasks/storage_advanced.py` or new `tasks/partitioning.py`

#### Task 4.1: CreatePartitionFdiskTask
- **Objective:** Create partition using fdisk
- **Skills tested:**
  - fdisk interactive commands (n, p, w)
  - Partition types (primary, extended, logical)
  - MBR partitioning
- **Validation:**
  - lsblk shows new partition
  - Correct size and type

#### Task 4.2: CreatePartitionPartedTask
- **Objective:** Create partition using parted
- **Skills tested:**
  - parted commands (mklabel, mkpart)
  - GPT vs MBR
  - Partition alignment
- **Validation:**
  - Partition exists with correct parameters

#### Task 4.3: CreateGPTPartitionTask
- **Objective:** Create GPT partition table and partitions
- **Skills tested:**
  - GPT advantages and use cases
  - parted mklabel gpt
  - Partition naming (part1, part2)
- **Validation:**
  - GPT label applied
  - Partitions created correctly

#### Task 4.4: ResizePartitionTask
- **Objective:** Resize an existing partition
- **Skills tested:**
  - growpart or parted resizepart
  - Understanding partition boundaries
  - Data preservation
- **Validation:**
  - Partition resized
  - Data intact (if applicable)

#### Task 4.5: DeletePartitionTask
- **Objective:** Safely delete a partition
- **Skills tested:**
  - Unmounting first
  - fdisk d command or parted rm
  - Updating kernel partition table
- **Validation:**
  - Partition removed
  - No orphaned mounts

### Safety Considerations
- Must use practice device only
- Validate device is not system disk
- Clear warnings before destructive operations

### Dependencies
- Device manager (existing)
- Filesystem module (for format after partition)

---

## 5. Time Services Module (MEDIUM PRIORITY)

### Why Critical
- Time synchronization is essential for logging, auth
- chrony is the default in RHEL 8/9
- Simple but must be understood

### New File: `tasks/time_services.py`

#### Task 5.1: ConfigureTimezoneTask
- **Objective:** Set system timezone
- **Skills tested:**
  - timedatectl set-timezone
  - Listing available timezones
  - Verifying timezone
- **Validation:**
  - timedatectl shows correct timezone
  - /etc/localtime symlink correct

#### Task 5.2: ConfigureChronydTask
- **Objective:** Configure chrony time synchronization
- **Skills tested:**
  - /etc/chrony.conf syntax
  - NTP server configuration
  - Restarting chronyd
- **Validation:**
  - chrony.conf has correct servers
  - chronyd service running
  - chronyc sources shows sync

#### Task 5.3: EnableNTPSyncTask
- **Objective:** Enable NTP synchronization
- **Skills tested:**
  - timedatectl set-ntp true
  - Verifying sync status
- **Validation:**
  - NTP synchronized = yes

#### Task 5.4: SetSystemTimeManuallyTask
- **Objective:** Set date/time manually (for learning)
- **Skills tested:**
  - timedatectl set-time
  - date command
  - Understanding when manual setting is needed
- **Validation:**
  - Time set correctly

#### Task 5.5: ConfigureNTPServerPoolTask
- **Objective:** Configure multiple NTP servers
- **Skills tested:**
  - pool vs server directive
  - iburst option
  - Fallback servers
- **Validation:**
  - Multiple sources configured

### Dependencies
- Services module (chronyd)
- Network connectivity for NTP

---

## 6. Repository Configuration Module (MEDIUM PRIORITY)

### Merged with Package Management (Section 3)

Additional tasks to add:

#### Task 6.1: DisableRepoTask
- **Objective:** Disable a repository
- **Skills tested:**
  - dnf config-manager --disable
  - Editing repo files (enabled=0)
- **Validation:**
  - Repo not in dnf repolist

#### Task 6.2: SetRepoPriorityTask
- **Objective:** Configure repository priority
- **Skills tested:**
  - priority= in repo file
  - Understanding repo precedence
- **Validation:**
  - Priority correctly set

#### Task 6.3: CreateLocalRepoTask
- **Objective:** Create repository from local directory
- **Skills tested:**
  - createrepo command
  - file:// baseurl
  - Local package installation
- **Validation:**
  - Repo accessible locally

---

## 7. SSH Module (LOW PRIORITY)

### Why Included
- SSH is ubiquitous but usually tested implicitly
- Key-based auth is important for security

### New File: `tasks/ssh.py`

#### Task 7.1: GenerateSSHKeyTask
- **Objective:** Generate SSH key pair
- **Skills tested:**
  - ssh-keygen command
  - Key types (rsa, ed25519)
  - Passphrase handling
- **Validation:**
  - Key files exist in ~/.ssh/
  - Correct permissions (600)

#### Task 7.2: ConfigureSSHKeyAuthTask
- **Objective:** Set up key-based authentication
- **Skills tested:**
  - ssh-copy-id
  - authorized_keys file
  - Proper permissions
- **Validation:**
  - Key in authorized_keys
  - Permissions correct

#### Task 7.3: SSHConfigFileTask
- **Objective:** Create SSH client config
- **Skills tested:**
  - ~/.ssh/config syntax
  - Host aliases
  - Connection options
- **Validation:**
  - Config file valid syntax

#### Task 7.4: SecureSSHDConfigTask
- **Objective:** Secure SSH server configuration
- **Skills tested:**
  - /etc/ssh/sshd_config
  - PermitRootLogin, PasswordAuthentication
  - Restarting sshd
- **Validation:**
  - Config options set correctly

---

## 8. RAID Module (LOW PRIORITY)

### Why Included
- Sometimes appears on exam
- Good for understanding storage redundancy
- Less common in cloud environments

### Addition to: `tasks/storage_advanced.py`

#### Task 8.1: CreateRAID1Task
- **Objective:** Create RAID 1 (mirror) array
- **Skills tested:**
  - mdadm --create
  - RAID 1 concept (mirroring)
  - /proc/mdstat monitoring
- **Validation:**
  - RAID device exists
  - Correct RAID level
  - Devices synced

#### Task 8.2: CreateRAID5Task
- **Objective:** Create RAID 5 array
- **Skills tested:**
  - RAID 5 concept (striping with parity)
  - Minimum device requirements
  - Spare devices
- **Validation:**
  - RAID 5 created
  - Correct number of devices

#### Task 8.3: ManageRAIDArrayTask
- **Objective:** Add/remove devices from array
- **Skills tested:**
  - mdadm --add
  - mdadm --fail --remove
  - Rebuilding arrays
- **Validation:**
  - Device operations successful

#### Task 8.4: PersistentRAIDConfigTask
- **Objective:** Make RAID configuration persistent
- **Skills tested:**
  - mdadm --detail --scan
  - /etc/mdadm.conf
  - Dracut/initramfs updates
- **Validation:**
  - Config in mdadm.conf
  - Array assembles on boot

---

## 9. SMB/CIFS Module (LOW PRIORITY)

### Why Included
- Mixed environments need Windows share access
- Less common than NFS but still relevant

### Addition to: `tasks/network_storage.py`

#### Task 9.1: MountCIFSShareTask
- **Objective:** Mount a Windows/Samba share
- **Skills tested:**
  - mount -t cifs syntax
  - Credentials file
  - Mount options (username, password, domain)
- **Validation:**
  - Share mounted
  - Accessible

#### Task 9.2: PersistentCIFSMountTask
- **Objective:** Configure CIFS mount in fstab
- **Skills tested:**
  - fstab CIFS syntax
  - credentials= option
  - _netdev option
- **Validation:**
  - fstab entry correct
  - Mount works

#### Task 9.3: AutofsCIFSTask
- **Objective:** Configure autofs for CIFS
- **Skills tested:**
  - CIFS in autofs maps
  - Credential handling
- **Validation:**
  - Auto-mount on access

---

## Implementation Order

### Phase 1: Critical (Do First)
1. Shell Scripting Module (Section 1)
2. Package Management Module (Section 3)
3. NFS/Autofs Module (Section 2)

### Phase 2: Important
4. Time Services Module (Section 5)
5. Disk Partitioning Module (Section 4)

### Phase 3: Complete Coverage
6. SSH Module (Section 7)
7. RAID Module (Section 8)
8. SMB/CIFS Module (Section 9)

---

## Infrastructure Changes Needed

### 1. Safe Executor Updates
Add to `config/settings.py` SAFE_VALIDATION_COMMANDS:
```python
# New commands for V3
'rpm', 'dnf', 'yum',           # Package management
'showmount', 'nfsstat',        # NFS
'chronyc', 'timedatectl',      # Time services
'ssh-keygen',                  # SSH (read-only check)
'mdadm',                       # RAID
'parted', 'fdisk', 'gdisk',    # Partitioning
'createrepo',                  # Repo creation
```

### 2. Device Manager Updates
- Add detection for RAID arrays
- Add NFS mount detection
- Add partition vs whole-disk detection

### 3. New Validator Files
- `validators/script_validators.py` - Script syntax and execution
- `validators/package_validators.py` - Package state checking
- `validators/nfs_validators.py` - NFS mount validation

### 4. Learning Content Updates
Update `core/learn.py` to add:
- Shell Scripting section
- Package Management section
- NFS/Autofs section
- Time Services section
- Partitioning section

---

## Testing Strategy

### Unit Tests
- Each new task class should have pytest tests
- Mock system commands where possible
- Test validation logic separately

### Integration Tests
- Test on fresh RHEL 9 VM
- Verify all tasks generate correctly
- Verify all validations work

### Exam Simulation Tests
- Create full mock exams using new tasks
- Time the completion
- Verify scoring accuracy

---

## Documentation Updates

### User Guide
- Add examples for each new task type
- Document prerequisites (NFS server, etc.)
- Troubleshooting section

### README Updates
- Update feature list
- Add V3 changelog
- Update coverage percentage

---

## Estimated Effort

| Module | New Tasks | Complexity | Est. Hours |
|--------|-----------|------------|------------|
| Shell Scripting | 6 | High | 8-10 |
| NFS/Autofs | 6 | Medium | 6-8 |
| Package Management | 8 | Low | 4-6 |
| Disk Partitioning | 5 | High | 6-8 |
| Time Services | 5 | Low | 3-4 |
| SSH | 4 | Low | 3-4 |
| RAID | 4 | Medium | 4-6 |
| SMB/CIFS | 3 | Low | 2-3 |
| **Total** | **41** | - | **36-49** |

---

## Version Notes

- **V3.0:** All Phase 1 modules (Scripting, Packages, NFS)
- **V3.1:** Phase 2 modules (Time, Partitioning)
- **V3.2:** Phase 3 modules (SSH, RAID, SMB) + polish

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| NFS requires server | High | Document requirements; optional skip |
| Partitioning can destroy data | Critical | Device manager safety checks |
| Script validation complexity | Medium | Use subprocess with timeout |
| Package ops need network | Medium | Support offline mock mode |

---

*Document created: 2026-02-10*
*Target completion: TBD*
*Author: RHCSA Simulator Team*
