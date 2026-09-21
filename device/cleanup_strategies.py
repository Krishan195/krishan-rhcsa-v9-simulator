"""
Cleanup strategies for different resource types.

These are more granular cleanup implementations that can be used
for specific scenarios beyond the DeviceManager's default cleanup.
"""

import subprocess
import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


logger = logging.getLogger(__name__)


class CleanupStrategy(ABC):
    """Base class for cleanup strategies."""

    @abstractmethod
    def cleanup(self, identifier: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Execute cleanup. Returns True if successful."""
        pass

    @abstractmethod
    def can_cleanup(self, identifier: str) -> bool:
        """Check if resource exists and can be cleaned up."""
        pass

    def _run_command(self, cmd: List[str], timeout: int = 15) -> subprocess.CompletedProcess:
        """Run a command with timeout and capture output."""
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


class LVMCleanupStrategy(CleanupStrategy):
    """
    Comprehensive LVM cleanup strategy.

    Handles full LVM stack cleanup in the correct order:
    1. Unmount any filesystems
    2. Deactivate swap
    3. Remove LVs
    4. Remove VGs
    5. Remove PVs
    6. Wipe device
    """

    def can_cleanup(self, identifier: str) -> bool:
        """Check if device has LVM structures."""
        result = self._run_command(['pvs', '--noheadings', identifier])
        return result.returncode == 0

    def cleanup(self, identifier: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Clean entire LVM stack on a device."""
        logger.info(f"Starting full LVM cleanup on {identifier}")

        # 1. Find all VGs that use this PV
        vgs = self._get_vgs_for_pv(identifier)

        for vg in vgs:
            # 2. Find all LVs in this VG
            lvs = self._get_lvs_for_vg(vg)

            for lv_path in lvs:
                # 3. Unmount if mounted
                self._unmount_lv(lv_path)
                # 4. Deactivate if swap
                self._deactivate_swap(lv_path)
                # 5. Remove LV
                self._remove_lv(lv_path)

            # 6. Remove VG
            self._remove_vg(vg)

        # 7. Remove PV
        self._remove_pv(identifier)

        # 8. Wipe device
        self._wipe_device(identifier)

        logger.info(f"LVM cleanup complete on {identifier}")
        return True

    def _get_vgs_for_pv(self, pv: str) -> List[str]:
        """Get list of VGs that use a PV."""
        result = self._run_command(['pvs', '--noheadings', '-o', 'vg_name', pv])
        vgs = []
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                vg = line.strip()
                if vg:
                    vgs.append(vg)
        return vgs

    def _get_lvs_for_vg(self, vg: str) -> List[str]:
        """Get list of LV paths in a VG."""
        result = self._run_command(['lvs', '--noheadings', '-o', 'lv_path', vg])
        lvs = []
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                lv = line.strip()
                if lv:
                    lvs.append(lv)
        return lvs

    def _unmount_lv(self, lv_path: str) -> bool:
        """Unmount an LV if mounted."""
        # Check if mounted
        result = self._run_command(['findmnt', '-n', '-o', 'TARGET', lv_path])
        if result.returncode == 0 and result.stdout.strip():
            mount_point = result.stdout.strip()
            logger.info(f"Unmounting {mount_point}")
            umount_result = self._run_command(['umount', '-f', mount_point])
            return umount_result.returncode == 0
        return True

    def _deactivate_swap(self, lv_path: str) -> bool:
        """Deactivate swap if LV is swap."""
        result = self._run_command(['swapoff', lv_path])
        return True  # Ignore errors if not swap

    def _remove_lv(self, lv_path: str) -> bool:
        """Remove a logical volume."""
        logger.info(f"Removing LV: {lv_path}")
        result = self._run_command(['lvremove', '-f', lv_path])
        return result.returncode == 0

    def _remove_vg(self, vg: str) -> bool:
        """Remove a volume group."""
        logger.info(f"Removing VG: {vg}")
        result = self._run_command(['vgremove', '-f', vg])
        return result.returncode == 0

    def _remove_pv(self, pv: str) -> bool:
        """Remove a physical volume."""
        logger.info(f"Removing PV: {pv}")
        result = self._run_command(['pvremove', '-f', '-y', pv])
        return result.returncode == 0

    def _wipe_device(self, device: str) -> bool:
        """Wipe device signatures."""
        logger.info(f"Wiping device: {device}")
        result = self._run_command(['wipefs', '-a', device])
        return result.returncode == 0


class MountCleanupStrategy(CleanupStrategy):
    """Cleanup strategy for mount points."""

    def can_cleanup(self, identifier: str) -> bool:
        """Check if mount point is active."""
        result = self._run_command(['findmnt', '-n', identifier])
        return result.returncode == 0

    def cleanup(self, identifier: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Unmount and optionally remove mount point directory."""
        metadata = metadata or {}

        # Unmount
        logger.info(f"Unmounting {identifier}")
        result = self._run_command(['umount', '-f', identifier])

        if result.returncode != 0:
            # Try lazy unmount
            result = self._run_command(['umount', '-l', identifier])

        # Remove mount point directory if requested
        if metadata.get('remove_dir', False):
            try:
                if os.path.exists(identifier) and os.path.isdir(identifier):
                    os.rmdir(identifier)
            except Exception as e:
                logger.warning(f"Could not remove mount point dir: {e}")

        return True


class SwapCleanupStrategy(CleanupStrategy):
    """Cleanup strategy for swap space."""

    def can_cleanup(self, identifier: str) -> bool:
        """Check if swap is active."""
        result = self._run_command(['swapon', '--show=NAME', '--noheadings'])
        return identifier in result.stdout

    def cleanup(self, identifier: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Deactivate swap."""
        logger.info(f"Deactivating swap: {identifier}")
        result = self._run_command(['swapoff', identifier])
        return result.returncode == 0


class UserCleanupStrategy(CleanupStrategy):
    """Cleanup strategy for users."""

    # System users that should never be removed
    PROTECTED_USERS = {
        'root', 'bin', 'daemon', 'adm', 'lp', 'sync', 'shutdown', 'halt',
        'mail', 'operator', 'games', 'ftp', 'nobody', 'systemd-network',
        'dbus', 'polkitd', 'sshd', 'postfix', 'chrony', 'austin', 'ntp',
        'apache', 'nginx', 'mysql', 'postgres'
    }

    def can_cleanup(self, identifier: str) -> bool:
        """Check if user exists and can be removed."""
        if identifier in self.PROTECTED_USERS:
            return False
        result = self._run_command(['id', identifier])
        return result.returncode == 0

    def cleanup(self, identifier: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Remove user and optionally home directory."""
        if identifier in self.PROTECTED_USERS:
            logger.warning(f"Refusing to remove protected user: {identifier}")
            return False

        metadata = metadata or {}
        remove_home = metadata.get('remove_home', True)

        logger.info(f"Removing user: {identifier}")

        if remove_home:
            result = self._run_command(['userdel', '-rf', identifier])
        else:
            result = self._run_command(['userdel', identifier])

        return result.returncode == 0


class GroupCleanupStrategy(CleanupStrategy):
    """Cleanup strategy for groups."""

    # System groups that should never be removed
    PROTECTED_GROUPS = {
        'root', 'bin', 'daemon', 'sys', 'adm', 'tty', 'disk', 'lp',
        'mem', 'kmem', 'wheel', 'cdrom', 'mail', 'man', 'dialout',
        'floppy', 'games', 'tape', 'video', 'ftp', 'lock', 'audio',
        'nobody', 'users', 'utmp', 'utempter', 'input', 'systemd-journal',
        'systemd-network', 'dbus', 'polkitd', 'ssh_keys', 'sshd'
    }

    def can_cleanup(self, identifier: str) -> bool:
        """Check if group exists and can be removed."""
        if identifier in self.PROTECTED_GROUPS:
            return False
        result = self._run_command(['getent', 'group', identifier])
        return result.returncode == 0

    def cleanup(self, identifier: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Remove group."""
        if identifier in self.PROTECTED_GROUPS:
            logger.warning(f"Refusing to remove protected group: {identifier}")
            return False

        logger.info(f"Removing group: {identifier}")
        result = self._run_command(['groupdel', identifier])
        return result.returncode == 0


class FstabCleanupStrategy(CleanupStrategy):
    """Cleanup strategy for /etc/fstab entries."""

    def can_cleanup(self, identifier: str) -> bool:
        """Check if identifier exists in fstab."""
        try:
            with open('/etc/fstab', 'r') as f:
                return identifier in f.read()
        except Exception:
            return False

    def cleanup(self, identifier: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Remove fstab entry containing identifier."""
        try:
            with open('/etc/fstab', 'r') as f:
                lines = f.readlines()

            new_lines = []
            removed = False
            for line in lines:
                if identifier not in line:
                    new_lines.append(line)
                else:
                    logger.info(f"Removing fstab entry: {line.strip()}")
                    removed = True

            if removed:
                with open('/etc/fstab', 'w') as f:
                    f.writelines(new_lines)

            return True
        except Exception as e:
            logger.error(f"Failed to clean fstab: {e}")
            return False


class FileCleanupStrategy(CleanupStrategy):
    """Cleanup strategy for files."""

    def can_cleanup(self, identifier: str) -> bool:
        """Check if file exists."""
        return os.path.isfile(identifier)

    def cleanup(self, identifier: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Remove file."""
        try:
            if os.path.exists(identifier):
                os.remove(identifier)
                logger.info(f"Removed file: {identifier}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove file {identifier}: {e}")
            return False


class DirectoryCleanupStrategy(CleanupStrategy):
    """Cleanup strategy for directories."""

    # Protected directories
    PROTECTED_DIRS = {
        '/', '/home', '/root', '/etc', '/var', '/tmp', '/usr',
        '/bin', '/sbin', '/lib', '/lib64', '/boot', '/dev',
        '/proc', '/sys', '/run', '/opt', '/srv'
    }

    def can_cleanup(self, identifier: str) -> bool:
        """Check if directory exists and can be removed."""
        if identifier in self.PROTECTED_DIRS:
            return False
        return os.path.isdir(identifier)

    def cleanup(self, identifier: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Remove directory."""
        if identifier in self.PROTECTED_DIRS:
            logger.warning(f"Refusing to remove protected directory: {identifier}")
            return False

        try:
            if os.path.exists(identifier):
                import shutil
                shutil.rmtree(identifier)
                logger.info(f"Removed directory: {identifier}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove directory {identifier}: {e}")
            return False


# Factory to get appropriate strategy
def get_cleanup_strategy(resource_type: str) -> Optional[CleanupStrategy]:
    """Get the appropriate cleanup strategy for a resource type."""
    strategies = {
        'lvm': LVMCleanupStrategy(),
        'mount_point': MountCleanupStrategy(),
        'swap': SwapCleanupStrategy(),
        'user': UserCleanupStrategy(),
        'group': GroupCleanupStrategy(),
        'fstab_entry': FstabCleanupStrategy(),
        'file': FileCleanupStrategy(),
        'directory': DirectoryCleanupStrategy(),
    }
    return strategies.get(resource_type)
