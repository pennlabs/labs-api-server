from flask import g, jsonify

from server import app
from server.auth import auth
from server.notifications import get_notification_settings
from server.privacy import get_privacy_settings


@app.route("/account/settings", methods=["GET"])
@auth()
def get_account_settings():
    notifSettings = get_notification_settings(g.account)
    privacySettings = get_privacy_settings(g.account)
    return jsonify({"notifications": notifSettings, "privacy": privacySettings, })
