from typing import Optional, List
from nornir.core.task import Result, Task
from nornir_nokia.connections import CONNECTION_NAME
from .report import add_to_report
import logging

logger = logging.getLogger(__name__)


def nokia_get(
    task: Task,
    path: Optional[str] = None,
    commands: Optional[List[str]] = None,
    datastore: str = "running",
    defaults: bool = False,
    config_only: bool = False,
) -> Result:
    """
    Retrieve data from Nokia SR OS device using YANG path or MD-CLI command.

    Arguments:
        path: YANG json-instance-path to retrieve data from (model-driven)
        commands: MD-CLI commands to execute (CLI mode)
        datastore: Datastore to read from - 'running' or 'candidate' (YANG mode only)
        defaults: Include default values (YANG mode only)
        config_only: Return only configuration data (YANG mode only)

    Returns:
        Result object with:
            * result: retrieved data (pySROS data structure or CLI string)
    """
    if not path and not commands:
        return Result(
            host=task.host,
            result=None,
            failed=True,
            exception=ValueError("Either 'path' or 'commands' must be provided"),
        )

    try:
        dev = task.host.get_connection(CONNECTION_NAME, task.nornir.config)
    except Exception as e:
        logger.error(f"{task.host.name}: Connection error: {e}")
        return Result(host=task.host, result=None, failed=True, exception=e)
    report_result = []
    try:
        if commands:
            # CLI mode
            for command in commands:
                result = dev.cli(command)
                report_result.append(['collect', command, result])
            
            add_to_report(task_host=task.host, report_list=report_result)
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
