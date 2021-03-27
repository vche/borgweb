"""
repos
"""

import logging
import subprocess
import time

from flask import current_app, render_template, jsonify

from . import blueprint

log = logging.getLogger(__name__)
process = None


@blueprint.route('/repos', methods=['GET'])
def get_repos():
    return jsonify(current_app.config['BACKUP_REPOS'])
