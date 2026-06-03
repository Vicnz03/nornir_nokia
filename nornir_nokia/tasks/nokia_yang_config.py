from typing import Any, Optional
from nornir.core.task import Result, Task
from nornir_nokia.connections import CONNECTION_NAME
import logging

logger = logging.getLogger(__name__)


def nokia_yang_config(
    task: Task,
    path: str,
    value: Any,
    commit: bool = True,
    method: str = "default",
) -> Result:
    """
    Configure Nokia SR OS device using YANG model-driven interface.

    Uses candidate datastore set() to apply configuration.

    Arguments:
        path: YANG json-instance-path to configure
        value: pySROS data structure or simple value to set
        commit: Whether to commit immediately after set (default True)
        method: Set operation method - 'default', 'merge', or 'replace'

    Returns:
        Result object with:
            * result: status message
            * diff: compare output if commit=True
            * changed: True if configuration was applied
    """
    try:
        dev = task.host.get_connection(CONNECTION_NAME, task.nornir.config)
    except Exception as e:
        logger.error(f"{task.host.name}: Connection error: {e}")
        return Result(host=task.host, result=None, failed=True, exception=e)

    diff = ""
    try:
        # Get compare output before commit if we are committing
        if commit:
            # Set without commit first to get compare
            dev.candidate.set(path, value, commit=False, method=method)
            diff = dev.candidate.compare(output_format="md-cli")
            # Now commit
            dev.candidate.commit()
            result_msg = "Configuration applied and committed successfully"
        else:
            dev.candidate.set(path, value, commit=False, method=method)
            result_msg = "Configuration applied to candidate (not committed)"

        return Result(
            host=task.host,
            result=result_msg,
            diff=diff,
            changed=True,
        )

    except Exception as e:
        logger.error(f"{task.host.name}: YANG config error: {e}")
        return Result(host=task.host, result=None, failed=True, exception=e)
