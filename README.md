# nornir_nokia

Nokia SR OS pySROS Plugins for Nornir - supports both YANG model-driven and MD-CLI interactions with Nokia BNG devices.

## Installation

```bash
pip install nornir_nokia
```

## Features

- **Connection Plugin**: Manages pySROS NETCONF connections to Nokia SR OS devices
- **CLI Connection Plugin**: Manages Netmiko CLI SSH sessions via Nornir
- **YANG Configuration**: Configure devices using YANG model-driven paths (`candidate.set`)
- **CLI Configuration**: Configure devices using MD-CLI commands via Netmiko
- **Get Data**: Retrieve operational/configuration data via YANG paths or CLI commands
- **Commit Operations**: commit, commit confirm (with timer), compare, discard, rollback (cancel), lock/unlock

## Usage

### Inventory (hosts.yaml)

```yaml
nokia_bng_01:
  hostname: 192.168.1.1
  username: admin
  password: admin
  port: 830
  platform: nokia_sros
  connection_options:
    nornir_nokia:
      extras:
        yang_directory: ./YANG
        hostkey_verify: false
        timeout: 300
    nornir_nokia_cli:
      extras:
        cli_port: 22
        timeout: 90
        fast_cli: false
```

### YANG Configuration

```python
from nornir import InitNornir
from nornir_nokia.tasks import nokia_yang_config, nokia_commit

nr = InitNornir(config_file="config.yaml")

# Set configuration via YANG
result = nr.run(
    task=nokia_yang_config,
    path='/nokia-conf:configure/system/name',
    value='my-router',
    commit=False,
)

# Compare candidate vs baseline
result = nr.run(task=nokia_commit, action="compare", output_format="md-cli")

# Commit with confirmation timer
result = nr.run(task=nokia_commit, action="commit", timer=60)

# Confirm commit (accept)
result = nr.run(task=nokia_commit, action="commit")

# Rollback (cancel confirmed commit)
result = nr.run(task=nokia_commit, action="rollback")
```

### CLI Configuration

```python
from nornir_nokia.tasks import nokia_cli_config, nokia_get

# Configure via MD-CLI
result = nr.run(
    task=nokia_cli_config,
    commands=[
        '/configure system name "my-router"',
        '/configure router interface "demo1" ipv4 primary address 192.168.1.1 prefix-length 24',
    ],
  mode="commit",
  comment="deploy via nornir",
)

# Compare candidate changes without committing
result = nr.run(
  task=nokia_cli_config,
  config='''
  /configure system location "nornir-compare"
  ''',
  mode="compare",
)

# Confirmed commit with timer
result = nr.run(
  task=nokia_cli_config,
  commands=['/configure system contact "nornir-confirmed"'],
  mode="commit",
  timer=120,
)

# Get operational data via CLI
result = nr.run(task=nokia_get, command='show version')

# Get data via YANG path
result = nr.run(task=nokia_get, path='/nokia-state:state/system/oper-name')
```

## License

MIT
