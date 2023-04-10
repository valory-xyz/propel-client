# PCLI

propel client to perform openai requests.

## Install
installation `pip install .`


## Usage
cli command named: `propel`

use `propel login -u some_user` to obtain credentials store locally

use `propel logout` to logout on propel server and remove local credentials

use `propel call /v1/models` to perform openai call.


use `propel call /v1/models "{}"` to perform openai call with json encoded payload

or `echo "{}" | propel call /v1/models -` to perform openai call with json encoded payload from stdin


