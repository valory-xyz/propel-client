# PCLI

propel client to perform openai requests.

## Install
installation `pip install .`


## Usage
cli command named: `pcli`

use `pcli login -u some_user` to obtain credentials store locally

use `pcli logout` to logout on propel server and remove local credentials

use `pcli call /v1/models` to perform openai call.


use `pcli call /v1/models "{}"` to perform openai call with json encoded payload

or `echo "{}" | pcli call /v1/models -` to perform openai call with json encoded payload from stdin


