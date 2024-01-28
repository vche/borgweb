import asyncio
import os
import logging
import signal
import sys
import time

from discord import SyncWebhook
from flask import Flask, render_template
from flask import g as flaskg

from borgweb.borg import BorgClient
from borgweb.cache import BackupsData, BackupLogs
from threading import Thread
from .views import blueprint

log = logging.getLogger(__name__)


class BorgwebApp(Flask):

    def __init__(self, config_class, config_env: None):
        super().__init__(__name__)
        self._load_config(config_class, config_env)
        self.register_blueprint(blueprint)
        self.jinja_env.globals['flaskg'] = flaskg
        self.register_error_handler(404, self.err404)
        self._borg_client = BorgClient(self.config["BORG_PATH"])
        self.backup_data = BackupsData(
            self.config["STATUS_CACHE_PATH"],
            self.config["BACKUP_REPOS"],
            self._borg_client,
            self.config['LOG_DIR'],
        )

    def _load_config(self, config_class, config_env):
        self.config.from_object(config_class)
        if config_env and os.environ.get(config_env):
            self.config.from_envvar(config_env)

    def err404(error):
        return render_template('error.html', error=error), 404

    def run(self):
        """Start the web app."""
        # Don't use the reloader as it restarts the app dynamically, creating a new collector
        super().run(host=self.config["HOST"], port=self.config["PORT"], debug=self.config["DEBUG"], use_reloader=False)
        self.logger.info(f"Borgweb app started, listening on port {self.config['PORT']}")


def setup_logging(logfile=None, loglevel=logging.INFO):
    logging.basicConfig(
        filename=logfile or None,
        level=loglevel,
        format='[%(levelname)-7s %(asctime)s %(name)s,%(filename)s:%(lineno)d] %(message)s'
    )


class BorgBackupAlarmNotifier:
    DEFAULT_MESSAGE = "{} new connections:\n\n{}"
    DEFAULT_MESSAGE_DEVICE = "- {}, {}, {}, {}\n"

    def __init__(self, config):
        self._config = config
        self.logger = logging.getLogger(__name__)
        self.loop = asyncio.new_event_loop()
        self._message_device = self._config.get("DISCORD_MESSAGE_DEVICE", self.DEFAULT_MESSAGE_DEVICE)
        self._message = self._config.get("DISCORD_MESSAGE", self.DEFAULT_MESSAGE)
        self._enabled = self._config.get("ENABLE_DISCORD_ALARMING", False)
        if self._enabled:
            self._webhook = SyncWebhook.from_url(self._config.get("DISCORD_WEBHOOK"))
            self._user = self._config.get("DISCORD_WEBHOOK_USER")

    def _build_message(self, alarms):
        if not alarms:
            return None

        content = ""
        for repo,repo_data in alarms:
            content += self._message_device.format(
                repo, repo_data['last_result'], repo_data['last_date'], repo_data['last_time']
            )
        return self._message.format(len(alarms), content)

        # Backups failed:
        # - {repo}: On {repo_data['last_date']} at {repo_data['last_time']} Statue: {repo_data['last_result']}
        # "- {}: Failed with status {} on {} at {}\n"
        # Dashboard: http://192.168.0.199:5000

    def detect_and_alarm(self, old_data, new_data):
        alarms =  self.detect_alarms(old_data, new_data)
        self.raise_alarm(alarms)

    def detect_alarms(self, old_data, new_data):
        alarms = []
        for repo in new_data["repos"]:
            repo_data = new_data["repos"][repo]
            old_repo_data = old_data.get("repos", {}).get(repo) if old_data else {}

            # If the backup failed
            if repo_data.get("last_result") != BackupLogs.SUCCESS:
                # Check if it was already failing (then alarm was trigguered) or if it is new
                if (
                        old_repo_data and
                        old_repo_data["last_date"] == repo_data["last_date"] and
                        old_repo_data["last_time"] == repo_data["last_time"]
                    ):
                    continue

                log.info(f"Alarm raised for repo {repo}, backup on {repo_data['last_date']} at {repo_data['last_time']} failed ({repo_data['last_log']})")
                alarms.append((repo, repo_data))
        return alarms

    def raise_alarm(self, alarms):
        content = self._build_message(alarms)

        if content and self._enabled:
            self._webhook.send(content, username=self._user)

    def close(self):
        self.loop.run_until_complete(self.bot.shutdown())
        self.loop.close()

class BorgwebScanner(Thread):
    def __init__(self, config, app_backup_data):
        super().__init__(name=__name__, daemon=True)
        self._config = config
        self._backup_data = app_backup_data
        self._period = self._config["STATUS_CACHE_UPDATE_PERIOD"]
        self._alarming = BorgBackupAlarmNotifier(self._config)

    def _build_message(self, device_list):
        if not device_list:
            return None

        content = ""
        for dev in device_list:
            content += self._message_device.format(dev.mac, dev.manufacturer, dev.ip, dev.hostname)
        return self._message.format(len(device_list), content)

    def run(self):
        """Run the thread periodically polling log files."""
        self._running = True

        while self._running:
            log.info("Rescanning backup data")

            # Rescan data
            old_data = self._backup_data.backup_data
            new_data = self._backup_data.create()
            
            # Detect new backup failures
            self._alarming.detect_and_alarm(old_data, new_data)

            time.sleep(self._period)

    def stop(self):
        self._running = False


def main():
    application = BorgwebApp('borgweb.config.Config', 'BORGWEB_CONFIG')
    setup_logging(logfile=application.config["LOG_FILE"], loglevel=application.config.get("LOG_LEVEL"))
    log.info("Borgweb initialized")

    scanner = BorgwebScanner(application.config, application.backup_data)

    def signal_handler(sig, frame):
        scanner.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGILL, signal_handler)

    scanner.start()
    application.run()


if __name__ == '__main__':
    main()
