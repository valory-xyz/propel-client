# PCLI

propel client to operate agents and opeai calls

## Install
installation `pip install .`


## Usage
cli command named: `propel`

use `propel login -u some_user` to obtain credentials store locally

use `propel logout` to logout on propel server and remove local credentials

use `propel openai /v1/models` to perform openai call.

use `propel openai /v1/models "{}"` to perform openai call with json encoded payload

or `echo "{}" | propel openai /v1/models -` to perform openai call with json encoded payload from stdin


please check `--help` for other commands like: agents, keys, variables