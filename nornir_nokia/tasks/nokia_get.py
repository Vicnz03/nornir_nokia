from typing import Optional
from nornir.core.task import Result, Task
from nornir_nokia.connections import CONNECTION_NAME
import logging

logger = logging.getLogger(__name__)


def nokia_get(
    task: Task,
    path: Optional[str] = None,
    command: Optional[str] = None,
    datastore: str = "running",
    defaults: bool = False,
    config_only: bool = False,
) -> Result:
    """
    Retrieve data from Nokia SR OS device using YANG path or MD-CLI command.

    Arguments:
        path: YANG json-instance-path to retrieve data from (model-driven)
        command: MD-CLI command to execute (CLI mode)
        datastore: Datastore to read from - 'running' or 'candidate' (YANG mode only)
        defaults: Include default values (YANG mode only)
        config_only: Return only configuration data (YANG mode only)

    Returns:
        Result object with:
            * result: retrieved data (pySROS data structure or CLI string)
    """
    if not path and not command:
        return Result(
            host=task.host,
            result=None,
            failed=True,
            exception=ValueError("Either 'path' or 'command' must be provided"),
        )

    try:
        dev = task.host.get_connection(CONNECTION_NAME, task.nornir.config)
    except Exception as e:
        logger.error(f"{task.host.name}: Connection error: {e}")
        return Result(host=task.host, result=None, failed=True, exception=e)

    try:
        if command:
            # CLI mode
            result = dev.cli(command)
            return Result(host=task.host, result=result)
        else:
            # YANG model-driven mode
            if datastore == "running":
                ds = dev.running
            elif datastore == "candidate":
                ds = dev.candidate
            else:
                return Result(
                    host=task.host,
                    result=None,
                    failed=True,
                    exception=ValueError(f"Unsupported datastore: {datastore}"),
                )

            result = ds.get(path, defaults=defaults, config_only=config_only)
            return Result(host=task.host, result=result)

    except Exception as e:
        logger.error(f"{task.host.name}: Get error: {e}")
        return Result(host=task.host, result=None, failed=True, exception=e)
