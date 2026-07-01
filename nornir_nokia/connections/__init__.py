from typing import Any, Dict, Optional
from pysros.management import connect
from nornir.core.configuration import Config
import logging
from netmiko import ConnectHandler

logger = logging.getLogger(__name__)

CONNECTION_NAME = "nornir_nokia"
CONNECTION_NAME_CLI = "nornir_nokia_cli"


class NornirNokia:
    def open(
        self,
        hostname: Optional[str],
        username: Optional[str],
        password: Optional[str],
        port: Optional[int],
        platform: Optional[str],
        extras: Optional[Dict[str, Any]] = None,
        configuration: Optional[Config] = None,
    ) -> None:
        extras = extras or {}
        parameters: Dict[str, Any] = {
            "host": hostname,
            "username": username,
            "password": password,
            "port": port or 830,
        }

        # Optional pySROS parameters
        if "yang_directory" in extras:
            parameters["yang_directory"] = extras["yang_directory"]
        if "timeout" in extras:
            parameters["timeout"] = extras["timeout"]
        # Default to not verifying host keys so first-time connections don't
        # fail with "Unknown host key". Users can opt-in via extras.
        parameters["hostkey_verify"] = extras.get("hostkey_verify", False)
        if "rebuild" in extras:
            parameters["rebuild"] = extras["rebuild"]

        connection = connect(**parameters)
        self.connection = connection

    def close(self) -> None:
        if hasattr(self, "connection") and self.connection:
            self.connection.disconnect()


class NornirNokiaCLI:
    def open(
        self,
        hostname: Optional[str],
        username: Optional[str],
        password: Optional[str],
        port: Optional[int],
        platform: Optional[str],
        extras: Optional[Dict[str, Any]] = None,
        configuration: Optional[Config] = None,
    ) -> None:
        extras = extras or {}

        # Most inventories use 830 for NETCONF. CLI SSH should default to 22.
        netmiko_port = extras.get("cli_port")
        if netmiko_port is None:
            netmiko_port = 22 if (port or 830) == 830 else (port or 22)

        parameters: Dict[str, Any] = {
            "device_type": extras.get("device_type", "nokia_sros"),
            "host": hostname,
            "username": username,
            "password": password,
            "port": netmiko_port,
            "fast_cli": extras.get("fast_cli", False),
            "timeout": extras.get("timeout", 90),
        }

        # Optional netmiko parameters.
        optional_keys = (
            "global_delay_factor",
            "session_log",
            "session_log_file_mode",
            "banner_timeout",
            "auth_timeout",
            "conn_timeout",
            "read_timeout_override",
            "disabled_algorithms",
        )
        for key in optional_keys:
            if key in extras:
                parameters[key] = extras[key]

        self.connection = ConnectHandler(**parameters)

    def close(self) -> None:
        if hasattr(self, "connection") and self.connection:
            self.connection.disconnect()
