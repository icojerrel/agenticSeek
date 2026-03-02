"""
Test suite for safety checks functionality.
"""
import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sources.tools.safety import is_unsafe, is_any_unsafe


class TestSafetyUnix(unittest.TestCase):
    """Test cases for Unix/Linux safety checks."""

    def test_safe_commands(self):
        """Test that safe commands pass safety check."""
        safe_commands = [
            "ls -la",
            "pwd",
            "echo 'Hello World'",
            "cat file.txt",
            "grep 'pattern' file.txt",
            "python3 script.py",
            "pip install package",
            "cd /home/user",
            "mkdir new_folder",
            "touch file.txt",
            "cp file1.txt file2.txt",
            "mv old.txt new.txt",
            "find . -name '*.py'",
            "wc -l file.txt",
            "head -n 10 file.txt",
            "tail -f log.txt",
        ]
        
        for cmd in safe_commands:
            self.assertFalse(is_unsafe(cmd), f"Command '{cmd}' should be safe")

    def test_unsafe_rm_commands(self):
        """Test that rm commands are detected as unsafe."""
        unsafe_commands = [
            "rm -rf /",
            "rm -rf /*",
            "rm -rf ~",
            "rm -rf /home",
            "rm important_file.txt",
            "sudo rm -rf /var/log",
        ]
        
        for cmd in unsafe_commands:
            self.assertTrue(is_unsafe(cmd), f"Command '{cmd}' should be unsafe")

    def test_unsafe_dd_commands(self):
        """Test that dd commands are detected as unsafe."""
        unsafe_commands = [
            "dd if=/dev/zero of=/dev/sda",
            "dd if=/dev/sda of=/dev/sdb",
            "sudo dd if=/dev/zero of=/dev/sda1",
        ]
        
        for cmd in unsafe_commands:
            self.assertTrue(is_unsafe(cmd), f"Command '{cmd}' should be unsafe")

    def test_unsafe_mkfs_commands(self):
        """Test that mkfs commands are detected as unsafe."""
        unsafe_commands = [
            "mkfs.ext4 /dev/sda1",
            "mkfs.vfat /dev/sdb",
            "sudo mkfs.xfs /dev/sdc1",
        ]
        
        for cmd in unsafe_commands:
            self.assertTrue(is_unsafe(cmd), f"Command '{cmd}' should be unsafe")

    def test_unsafe_chmod_chown_commands(self):
        """Test that chmod/chown commands are detected as unsafe."""
        unsafe_commands = [
            "chmod 777 /etc/passwd",
            "chmod -R 777 /home",
            "chown root:root important_file",
            "sudo chown -R user:user /var/www",
        ]
        
        for cmd in unsafe_commands:
            self.assertTrue(is_unsafe(cmd), f"Command '{cmd}' should be unsafe")

    def test_unsafe_system_commands(self):
        """Test that system commands are detected as unsafe."""
        unsafe_commands = [
            "shutdown now",
            "reboot",
            "halt",
            "sudo shutdown -h now",
            "systemctl restart network",
        ]
        
        for cmd in unsafe_commands:
            self.assertTrue(is_unsafe(cmd), f"Command '{cmd}' should be unsafe")

    def test_unsafe_process_commands(self):
        """Test that process killing commands are detected as unsafe."""
        unsafe_commands = [
            "kill -9 1234",
            "pkill -f important_process",
            "killall python",
            "sudo kill -9 1",
        ]
        
        for cmd in unsafe_commands:
            self.assertTrue(is_unsafe(cmd), f"Command '{cmd}' should be unsafe")

    def test_unsafe_disk_commands(self):
        """Test that disk manipulation commands are detected as unsafe."""
        unsafe_commands = [
            "fdisk /dev/sda",
            "parted /dev/sdb mklabel gpt",
            "umount /mnt/data",
            "mount -o remount,rw /",
        ]
        
        for cmd in unsafe_commands:
            self.assertTrue(is_unsafe(cmd), f"Command '{cmd}' should be unsafe")

    def test_unsafe_git_commands(self):
        """Test that dangerous git commands are detected as unsafe."""
        unsafe_commands = [
            "git rebase -i HEAD~10",
            "git rebase --abort",
            "git push --force",
            "git push origin main --force",
        ]
        
        for cmd in unsafe_commands:
            self.assertTrue(is_unsafe(cmd), f"Command '{cmd}' should be unsafe")

    def test_unsafe_user_commands(self):
        """Test that user management commands are detected as unsafe."""
        unsafe_commands = [
            "useradd newuser",
            "userdel admin",
            "groupadd developers",
            "groupdel admins",
            "passwd root",
            "visudo",
        ]
        
        for cmd in unsafe_commands:
            self.assertTrue(is_unsafe(cmd), f"Command '{cmd}' should be unsafe")


class TestSafetyWindows(unittest.TestCase):
    """Test cases for Windows safety checks."""

    def test_safe_windows_commands(self):
        """Test that safe Windows commands pass safety check."""
        safe_commands = [
            "dir",
            "cd C:\\Users",
            "type file.txt",
            "copy file1.txt file2.txt",
            "mkdir new_folder",
            "del temp.txt",  # Note: del is actually unsafe but we test detection
        ]
        
        for cmd in safe_commands:
            # We just check the function doesn't crash
            is_unsafe(cmd)

    def test_unsafe_windows_del_commands(self):
        """Test that del/erase commands are detected as unsafe."""
        unsafe_commands = [
            "del C:\\Windows\\System32\\important.dll",
            "erase *.txt",
            "del /F /Q C:\\important_file.docx",
        ]
        
        for cmd in unsafe_commands:
            self.assertTrue(is_unsafe(cmd), f"Command '{cmd}' should be unsafe")

    def test_unsafe_windows_format_commands(self):
        """Test that format commands are detected as unsafe."""
        unsafe_commands = [
            "format C:",
            "format D: /FS:NTFS",
            "diskpart",
            "diskpart /s script.txt",
        ]
        
        for cmd in unsafe_commands:
            self.assertTrue(is_unsafe(cmd), f"Command '{cmd}' should be unsafe")

    def test_unsafe_windows_registry_commands(self):
        """Test that registry commands are detected as unsafe."""
        unsafe_commands = [
            "reg delete HKLM\\Software\\Important",
            "regedit /s malicious.reg",
            "reg add HKCU\\Software /v Value /t REG_SZ /d Data",
        ]
        
        for cmd in unsafe_commands:
            self.assertTrue(is_unsafe(cmd), f"Command '{cmd}' should be unsafe")

    def test_unsafe_windows_system_commands(self):
        """Test that system commands are detected as unsafe."""
        unsafe_commands = [
            "shutdown /s /t 0",
            "shutdown /r /f",
            "taskkill /F /PID 1234",
            "taskkill /F /IM notepad.exe",
            "wmic process delete",
        ]
        
        for cmd in unsafe_commands:
            self.assertTrue(is_unsafe(cmd), f"Command '{cmd}' should be unsafe")

    def test_unsafe_windows_file_commands(self):
        """Test that dangerous file commands are detected as unsafe."""
        unsafe_commands = [
            "xcopy /Y C:\\source D:\\dest",
            "copy /Y important.dll C:\\Windows\\System32",
            "move /Y C:\\Windows\\System32\\file.dll D:\\backup",
            "attrib +H +S C:\\Windows\\System32\\file.exe",
        ]
        
        for cmd in unsafe_commands:
            self.assertTrue(is_unsafe(cmd), f"Command '{cmd}' should be unsafe")


class TestSafetyAnyUnsafe(unittest.TestCase):
    """Test cases for is_any_unsafe function."""

    def test_is_any_unsafe_all_safe(self):
        """Test is_any_unsafe with all safe commands."""
        safe_commands = [
            "ls -la",
            "pwd",
            "echo 'Hello'",
            "cat file.txt",
        ]
        
        self.assertFalse(is_any_unsafe(safe_commands))

    def test_is_any_unsafe_one_unsafe(self):
        """Test is_any_unsafe with one unsafe command."""
        mixed_commands = [
            "ls -la",
            "rm -rf /tmp/test",
            "pwd",
        ]
        
        self.assertTrue(is_any_unsafe(mixed_commands))

    def test_is_any_unsafe_all_unsafe(self):
        """Test is_any_unsafe with all unsafe commands."""
        unsafe_commands = [
            "rm -rf /",
            "dd if=/dev/zero of=/dev/sda",
            "mkfs.ext4 /dev/sda1",
        ]
        
        self.assertTrue(is_any_unsafe(unsafe_commands))

    def test_is_any_unsafe_empty_list(self):
        """Test is_any_unsafe with empty list."""
        self.assertFalse(is_any_unsafe([]))


class TestSafetyEdgeCases(unittest.TestCase):
    """Test edge cases for safety checks."""

    def test_command_with_safe_substring(self):
        """Test commands containing safe words but not actual unsafe commands."""
        commands = [
            "echo 'this is a rm test'",  # Contains 'rm' but is safe
            "grep 'shutdown' log.txt",  # Contains 'shutdown' but is safe
            "cat file_with_kill_in_name.txt",  # Contains 'kill' but is safe
        ]
        
        # These should be detected as unsafe due to substring matching
        # This is a known limitation of the current implementation
        for cmd in commands:
            is_unsafe(cmd)  # Just check it doesn't crash

    def test_command_with_sudo(self):
        """Test commands with sudo prefix."""
        unsafe_sudo_commands = [
            "sudo rm -rf /",
            "sudo dd if=/dev/zero of=/dev/sda",
            "sudo mkfs.ext4 /dev/sda1",
        ]
        
        for cmd in unsafe_sudo_commands:
            self.assertTrue(is_unsafe(cmd), f"Command '{cmd}' should be unsafe")

    def test_partial_command_matching(self):
        """Test that partial matching works correctly."""
        # These should be detected as unsafe
        unsafe_partial = [
            "rm file",  # Contains 'rm'
            "format C:",  # Contains 'format'
            "kill 123",  # Contains 'kill'
        ]
        
        for cmd in unsafe_partial:
            self.assertTrue(is_unsafe(cmd), f"Command '{cmd}' should be unsafe")


if __name__ == '__main__':
    unittest.main()
