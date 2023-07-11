#!/bin/bash
set -e
export BASE_URL=https://app.propel-dev1.autonolas.tech/
export CMD="propel  -U $BASE_URL"
export AGENT_NAME=test_agent1_2
export KEY_ID=1
export IPFS_HASH=bafybeiaw2tv3ew5b5pjw57aiex5ylmliqalzuy42xlas4khr3zyf52qtom
export VARIABLES=ALL_PARTICIPANTS
export SERVICE_PREFIX="service_1"
# perform user login
#$CMD login -u **** -p ****


# create variables by name, second call replaces the first value
$CMD variables create ALL_PARTICIPANTS ALL_PARTICIPANTS '["0x933EA6bFb60437fD006c17455a09A5F169dDA953"]' >/dev/null
$CMD variables create ALL_PARTICIPANTS ALL_PARTICIPANTS '[]' >/dev/null


for i in "agent1 3" "agent2 4" "agent3 5" "agent4 6";
do
    IFS=' ' read -r -a array <<< "$i"
    AGENT_ID=${array[0]}
    KEY_ID=${array[1]}

    # check user has seats to perform agent creation
    $CMD seats ensure
    export AGENT_NAME=${SERVICE_PREFIX}_${AGENT_ID}
    
    # remove agent by name if needed
    $CMD agents ensure-deleted $AGENT_NAME

    # cerate agent. name has to be unique. will not allow create several agents with same name and/or key
    $CMD agents create --name $AGENT_NAME --key $KEY_ID --service-ipfs-hash $IPFS_HASH --variables $VARIABLES

    # wait for deployed. but it actually started. callr restart to have clean STARTED  state
    $CMD agents wait $AGENT_NAME DEPLOYED --timeout=120

    # restart the agent
    $CMD agents restart $AGENT_NAME

    # wait it started
    $CMD agents wait $AGENT_NAME STARTED --timeout=120


done




