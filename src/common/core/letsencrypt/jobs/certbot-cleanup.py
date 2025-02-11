#!/usr/bin/python3

from os import getenv
from pathlib import Path
from sys import exit as sys_exit, path as sys_path
from threading import Lock
from traceback import format_exc

sys_path.extend(
    (
        "/usr/share/bunkerweb/deps/python",
        "/usr/share/bunkerweb/utils",
        "/usr/share/bunkerweb/api",
        "/usr/share/bunkerweb/db",
    )
)

from Database import Database
from logger import setup_logger
from API import API

logger = setup_logger("Lets-encrypt", getenv("LOG_LEVEL", "INFO"))
status = 0

try:
    # Get env vars
    bw_integration = None
    if getenv("KUBERNETES_MODE", "no").lower() == "yes":
        bw_integration = "Kubernetes"
    elif getenv("SWARM_MODE", "no").lower() == "yes":
        bw_integration = "Swarm"
    elif getenv("AUTOCONF_MODE", "no").lower() == "yes":
        bw_integration = "Autoconf"
    elif Path("/usr/share/bunkerweb/INTEGRATION").exists():
        bw_integration = Path("/usr/share/bunkerweb/INTEGRATION").read_text().strip()
    token = getenv("CERTBOT_TOKEN", "")

    # Cluster case
    if bw_integration in ("Docker", "Swarm", "Kubernetes", "Autoconf"):
        db = Database(
            logger,
            sqlalchemy_string=getenv("DATABASE_URI", None),
        )
        lock = Lock()
        with lock:
            instances = db.get_instances()

        for instance in instances:
            endpoint = f"http://{instance['hostname']}:{instance['port']}"
            host = instance["server_name"]
            api = API(endpoint, host=host)
            sent, err, status, resp = api.request(
                "DELETE", "/lets-encrypt/challenge", data={"token": token}
            )
            if not sent:
                status = 1
                logger.error(
                    f"Can't send API request to {api.get_endpoint()}/lets-encrypt/challenge : {err}"
                )
            else:
                if status != 200:
                    status = 1
                    logger.error(
                        f"Error while sending API request to {api.get_endpoint()}/lets-encrypt/challenge : status = {resp['status']}, msg = {resp['msg']}",
                    )
                else:
                    logger.info(
                        f"Successfully sent API request to {api.get_endpoint()}/lets-encrypt/challenge",
                    )
    # Linux case
    else:
        challenge_path = (
            f"/var/tmp/bunkerweb/lets-encrypt/.well-known/acme-challenge/{token}"
        )
        if Path(challenge_path).exists():
            Path(challenge_path).unlink()
except:
    status = 1
    logger.error(f"Exception while running certbot-cleanup.py :\n{format_exc()}")

sys_exit(status)
