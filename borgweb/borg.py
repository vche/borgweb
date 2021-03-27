"""
borg client wrapper
"""

import subprocess
import os
import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)


class BorgClient:

    def __init__(self, binpath):
        self._borgpath = Path(binpath)
        if not self._borgpath.is_file():
            raise FileNotFoundError()
        self._current_env_list = None
        self._current_repo = None

    def _run_sync(self, args, pwd=None):
        arg_list = [self._borgpath] + args
        env_list = self._current_env_list
        res = None

        # If a pwd is specified, overwrite the one possibly already set
        if pwd:
            env_list = self._set_pwd(env_list, pwd)
        try:
            log.info(f"Executing borg client: {arg_list}")
            res = subprocess.run(arg_list, stdout=subprocess.PIPE, check=True, env=env_list)
        except subprocess.CalledProcessError as e:
            log.exception("Failed to execute borg client: %s", e)
        return res

    def _set_pwd(self, env_list, pwd):
        if not env_list:
            env_list = os.environ.copy()
        env_list["BORG_PASSPHRASE"] = pwd
        return env_list

    def _parse_info_result(self, json_output):
        """Extract a subset of data from the info output to use in borgweb."""
        info  = {}

        try:
            parsed = json.loads(json_output)
            # If we got an archive info
            if "archives" in parsed:
                info["date"] = parsed["archives"][0]["start"]
                info["size"] = parsed["archives"][0]["stats"]["original_size"]
                info["csize"] = parsed["archives"][0]["stats"]["compressed_size"]
                info["dsize"] = parsed["archives"][0]["stats"]["deduplicated_size"]
            else:
                info["size"] = parsed["cache"]["stats"]["total_size"]
                info["csize"] = parsed["cache"]["stats"]["total_csize"]
                info["dsize"] = parsed["cache"]["stats"]["unique_csize"]
        except (json.JSONDecodeError, KeyError) as e:
            log.error("Invalid borg info output: %s", e)
        return info

    def _parse_list_result(self, json_output):
        """Extract a subset of data from the list output to use in borgweb."""
        info  = []
        try:
            parsed = json.loads(json_output)
            info = [{"name": arch["archive"]} for arch in parsed["archives"]]
        except (json.JSONDecodeError, KeyError) as e:
            log.error("Invalid borg list output: %s", e)
        return info

    def set_repo(self, repo, pwd=None):
        self._current_repo = repo
        if pwd:
            self._current_env_list = self._set_pwd(self._current_env_list, pwd)

    def info(self, repo=None, archive=None, pwd=None):
        # Use repo set if none specified
        if not repo:
            repo = self._current_repo
        # Get info on an qrchive if one is specified
        infopath = f"{repo}::{archive}" if archive else repo

        # Run borg client
        log.info(f"Fetching info on {infopath}")
        res = self._run_sync(["info", "--json", infopath], pwd)

        return self._parse_info_result(res.stdout) if res else {}

    def list(self, repo=None, archive=None, pwd=None):
        # Use repo set if none specified
        if not repo:
            repo = self._current_repo
        # Run borg client
        log.info(f"Fetching list on {repo}")
        res = self._run_sync(["list", "--json", repo], pwd)
        return self._parse_list_result(res.stdout) if res else {}

