#!/usr/bin/env python
"""
Update-checker module for the Command and Control (CAC) Core package.

This module allows any package to check for updates and notify the user when newer versions are available.
It supports checking both cac-core itself and any dependent packages.
"""

import os
import sys
import json
import logging
import importlib.metadata
import requests
from datetime import datetime, timedelta
from pathlib import Path
from packaging.version import parse as parse_version

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger.addHandler(handler)

class UpdateChecker:
    """
    A class to check for updates to any Python package.

    This class checks for updates to specified packages and notifies the user if new versions are available.
    It uses the PyPI API or GitHub API to check for the latest release version.

    Attributes:
        package_name (str): The name of the package to check for updates
        current_version (str): The current version of the package
        check_interval (timedelta): The interval between update checks
        source (str): The source to check for updates ('pypi' or 'github')
    """

    def __init__(self, package_name, check_interval=timedelta(hours=1), source='pypi', repo=None):
        """
        Initialize the UpdateChecker.

        Args:
            package_name (str): The name of the package to check for updates.
            check_interval (timedelta): How often to check for updates.
            source (str): Where to check for updates ('pypi' or 'github').
            repo (str): GitHub repo in format 'owner/repo' (only needed for GitHub source).
        """
        self.package_name = package_name
        self.source = source.lower()
        self.repo = repo

        # Get the current version
        try:
            self.current_version = importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            logger.warning(f"Package '{package_name}' not found in installed packages.")
            self.current_version = "0.0.0"

        self.check_interval = check_interval

        # Set the update URL based on source
        if self.source == 'github' and repo:
            self.update_url = f"https://api.github.com/repos/{repo}/releases/latest"
        else:
            self.update_url = f"https://pypi.org/pypi/{package_name}/json"
            self.source = 'pypi'  # Default to PyPI if GitHub not properly configured

        # Set up data storage
        try:
            # Use a more platform-independent approach for determining config location
            if os.name == 'nt':  # Windows
                app_data = os.environ.get('APPDATA', os.path.expanduser('~'))
                self.data_dir = Path(app_data) / package_name
            else:  # macOS, Linux, etc.
                self.data_dir = Path(os.path.expanduser(os.path.join("~", ".config", package_name)))

            self.data_dir.mkdir(exist_ok=True, parents=True)
        except (PermissionError, OSError) as e:
            logger.warning(f"Could not create data directory {self.data_dir}: {e}")
            # Fall back to a temporary directory
            import tempfile
            self.data_dir = Path(tempfile.gettempdir()) / package_name
            self.data_dir.mkdir(exist_ok=True, parents=True)

        self.data_file = self.data_dir / "update.json"

        # Load existing data
        self.update_data = self._load_update_data()

    def _load_update_data(self):
        """Load update data from the local file."""
        try:
            if self.data_file.exists():
                with open(self.data_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Convert string to datetime
                    if data.get("last_check"):
                        data["last_check"] = datetime.fromisoformat(data["last_check"])
                    return data
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug(f"Error loading update data: {e}")
        except UnicodeDecodeError as e:
            logger.debug(f"Encoding error reading update data: {e}")

        # Return default data if file doesn't exist or has errors
        return {
            "last_check": None,
            "latest_version": None,
            "current_version": self.current_version
        }

    def _save_update_data(self):
        """Save update data to the local file."""
        try:
            # Convert datetime to string for JSON serialization
            save_data = self.update_data.copy()
            if save_data.get("last_check"):
                save_data["last_check"] = save_data["last_check"].isoformat()

            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.debug(f"Error saving update data: {e}")

    def check_for_updates(self, force=False):
        """
        Check for updates to the package.

        Args:
            force (bool): Force an update check even if the interval hasn't elapsed.

        Returns:
            dict: Update status containing current_version, latest_version, and update_available.
        """
        last_check = self.update_data.get("last_check")

        # Check if we need to perform an update check
        need_check = force or not last_check
        if not need_check and isinstance(last_check, datetime):
            try:
                need_check = (datetime.now() - last_check) > self.check_interval
            except (TypeError, ValueError):
                # If comparison fails, force a check
                need_check = True
        elif not need_check:
            # If last_check exists but isn't a datetime, force a check
            need_check = True

        if need_check:
            latest_version = self._fetch_latest_version()

            # Update the data
            self.update_data["last_check"] = datetime.now()
            self.update_data["latest_version"] = latest_version
            self.update_data["current_version"] = self.current_version

            # Save the updated data
            self._save_update_data()

        # Return update status
        return self.get_update_status()

    def _fetch_latest_version(self):
        """Fetch the latest version from the configured source."""
        try:
            response = requests.get(self.update_url, timeout=5)
            response.raise_for_status()

            if self.source == 'github':
                data = response.json()
                return data.get("tag_name", "0.0.0").lstrip("v")
            else:  # PyPI
                data = response.json()
                return data.get("info", {}).get("version", "0.0.0")

        except requests.RequestException as e:
            logger.debug(f"Error checking for updates: {e}")
            return self.update_data.get("latest_version") or self.current_version
        except (json.JSONDecodeError, KeyError) as e:
            logger.debug(f"Error parsing update response: {e}")
            return self.update_data.get("latest_version") or self.current_version

    def get_update_status(self):
        """
        Get the update status.

        Returns:
            dict: Update status containing current_version, latest_version, and update_available.
        """
        current = parse_version(self.current_version)
        latest = parse_version(self.update_data.get("latest_version") or "0.0.0")

        return {
            "package_name": self.package_name,
            "current_version": self.current_version,
            "latest_version": self.update_data.get("latest_version"),
            "update_available": latest > current,
            "last_checked": self.update_data.get("last_check")
        }

    def notify_if_update_available(self, quiet=False):
        """
        Notify the user if an update is available.

        Args:
            quiet (bool): If True, don't print anything if no update is available.

        Returns:
            bool: True if an update is available, False otherwise.
        """
        status = self.get_update_status()

        if status["update_available"]:
            logger.info(f"Update available for {self.package_name}:")
            logger.info(f"  Current version: {status['current_version']}")
            logger.info(f"  Latest version: {status['latest_version']}")
            logger.info(f"  Update with: pip install -U {self.package_name}")
            return True
        elif not quiet:
            logger.info(f"{self.package_name} is up to date ({status['current_version']}).")

        return False


# Convenience function for quick checks
def check_package_for_updates(package_name, notify=True, force=False, quiet=True):
    """
    Check a package for updates.

    Args:
        package_name (str): The name of the package to check
        notify (bool): Whether to print a notification
        force (bool): Whether to force a check regardless of interval
        quiet (bool): Don't print anything if no update is available

    Returns:
        dict: Update status
    """
    checker = UpdateChecker(package_name)
    status = checker.check_for_updates(force=force)

    if notify:
        checker.notify_if_update_available(quiet=quiet)

    return status


# Example usage
if __name__ == "__main__":
    # Check for updates to this package
    if len(sys.argv) > 1:
        package_name = sys.argv[1]
    else:
        package_name = "cac-core"

    status = check_package_for_updates(package_name, force=True)

    # Show status code to indicate if update is available
    sys.exit(0 if not status["update_available"] else 1)
