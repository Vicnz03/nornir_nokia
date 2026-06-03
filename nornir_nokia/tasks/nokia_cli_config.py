from typing import Dict, List, Optional
from nornir.core.task import Result, Task
import logging
from .report import add_to_report
from netmiko.exceptions import NetmikoAuthenticationException, NetmikoTimeoutException
from nornir_nokia.connections import CONNECTION_NAME_CLI
from time import sleep
logger = logging.getLogger(__name__)
import re

PRIVATE_CONFIG_CHECK = "[pr:/configure]"
PRIVATE_CONFIG_PATTERN = r"\[pr:.*\]\s*A:.*#"
EXEC_PROMPT_PATTERN = r"A:.*#"


def _looks_like_cli_error(output: str) -> bool:
    error_tokens = (
        "MINOR:",
        "MAJOR:",
        "CRITICAL:",
        "ERROR:",
        "Error:",
        "Unknown command",
        "Invalid token",
        "failed",
    )
    return any(token in output for token in error_tokens)


def nokia_cli_config(
    task: Task,
    config: Optional[str] = None,
    mode: str = "commit",
    timer: Optional[int] = 2,
    comment: Optional[str] = '',
) -> Result:
    """
    Configure Nokia SR OS devices using Netmiko over MD-CLI.

    Modes:
        - commit: load config and commit (supports comment/timer)
        - compare: load config, compare, then discard
        - config_only: load config only (no compare/commit/discard)

    Arguments:
        commands: List of MD-CLI commands to execute.
        config: Multi-line MD-CLI configuration text.
        mode: Operation mode - commit, compare, or config_only.
        timer: Confirmed-commit timer in seconds (commit mode).
        comment: Commit comment text (commit mode).
        CLI connection is managed by Nornir connection plugin `nornir_nokia_cli`.
        Use host connection_options -> nornir_nokia_cli.extras to tune timeout/port.

    Returns:
        Result object with:
            * result: dict mapping each command to its output
            * diff: compare output for mode='compare'
            * changed: True if running config is committed
    """
    if mode not in {"commit", "compare", "commit_check", "config_only"}:
        return Result(
            host=task.host,
            result=None,
            failed=True,
            exception=ValueError(
                f"Unsupported mode '{mode}'. Valid modes: commit, compare, commit_check, config_only"
            ),
        )
        
    task.host['config'] = config
    if 'password' in config and mode == 'commit':
        report_list = [[mode, 'config', 'hidden because include password']]
    else:
        report_list = [[mode, 'config', config]]

    if mode == 'config_only':
        add_to_report(task_host=task.host,report_list = report_list)
        return Result(host=task.host, diff='')
    
    try:
        conn = task.host.get_connection(CONNECTION_NAME_CLI, task.nornir.config)

        # For Nokia private mode, netmiko's generic config_mode() may still use
        # exclusive-mode checks internally and raise a false negative. Enter and verify explicitly.
        if not conn.check_config_mode():
            output = conn.config_mode()
            
        config_output = conn.send_config_set(
            config_commands=[line.strip() for line in config.splitlines() if line.strip()],
            exit_config_mode=False,
        )
        if _looks_like_cli_error(config_output):
            raise Exception(f"Command failed:\n{config_output}")

        diff = conn.send_command('compare')

        if diff == '':
            task.host['compare'] = 'NO DIFF'
        else:
            task.host['compare'] = diff
        report_list.append([mode, 'compare',task.host['compare']])        
        
        if mode == "compare":
            conn.send_command("discard")
            
        elif mode == "commit_check":
            commit_check_output = conn.send_command("validate")
            task.host['commit_check'] = commit_check_output
            report_list.append([mode, 'commit_check', task.host['commit_check']])

        if mode == "commit":
            if timer is not None and timer > 0:
                logger.info(f"{task.host.name}: Using confirmed commit with timer {timer} seconds")
                commit_output = conn.send_command(f"commit confirmed {timer} comment {comment}", read_timeout=120)
                task.host['commit'] = commit_output
                report_list.append([mode, 'commit', task.host['commit']])
                sleep(10)
                confirm_output = conn.send_command("commit confirmed accept", read_timeout=120)
            else:
                commit_output = conn.send_command(f"commit comment {comment}", read_timeout=120)
                task.host['commit'] = commit_output
                report_list.append([mode, 'commit', task.host['commit']])

        add_to_report(task_host=task.host, report_list=report_list)
        return Result(host=task.host, result=report_list, diff=task.host.get('compare', ''), changed=True)


    except (NetmikoTimeoutException, NetmikoAuthenticationException) as e:
        logger.error(f"{task.host.name}: Netmiko connection error: {e}")
        return Result(host=task.host, result=None, failed=True, exception=e)
    except Exception as e:
        logger.error(f"{task.host.name}: CLI config error: {e}")
        return Result(host=task.host, result=report_list, failed=True, exception=e)
    finally:
        try:
            if conn is not None and conn.check_config_mode():
                conn.exit_config_mode(
                    exit_config="/exit all",
                )
        except Exception as e:
            logger.debug(f"{task.host.name}: Failed to exit config mode cleanly: {e}")
