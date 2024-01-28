"""
backup view
"""

import logging
import time

from flask import current_app, render_template, jsonify
from . import blueprint
from . import logs
import os
from borgweb.borg import BorgClient
import json
from pathlib import Path

log = logging.getLogger(__name__)


@blueprint.route('/cacheflush', methods=['GET'])
def invalidate_backup_cache():
    try:
        current_app.backup_data.flush()
        return "{'status':'ok'}"
    except Exception as e:
        error_str = f"Error processing cache invalidate request {e.__class__.__name__}: {e}"
        log.exception(error_str) if log.isEnabledFor(logging.DEBUG) else log.error(error_str)
        return {"error": error_str}


@blueprint.route('/backups', methods=['GET'])
def get_backups():
    try:
        # Get data from cache, and if invalid create it
        backup_data = current_app.backup_data.load()
        return json.dumps(backup_data)
    except Exception as e:
        error_str = f"Error processing backups request {e.__class__.__name__}:{e}"
        log.exception(error_str) if log.isEnabledFor(logging.DEBUG) else log.error(error_str)
        return {"error": error_str}
