#!/bin/bash
set -e
export BASE_URL=https://app.propel.staging.valory.xyz
export CMD="propel  -U $BASE_URL"
export AGENT_NAME=test_agent1_2
export KEY_ID=188
export IPFS_HASH=bafybeifbyghd5robjp3vklbaaa2gsawly27hfgtscjnhbwzcxbau6cuwoa
export VARIABLES=ALL_PARTICIPANTS
export SERVICE_PREFIX="service_1"
# perform user login
#$CMD login -u **** -p ****


# create variables by name, second call replaces the first value
$CMD variables create ALL_PARTICIPANTS ALL_PARTICIPANTS '["0x933EA6bFb60437fD006c17455a09A5F169dDA953"]' >/dev/null
$CMD variables create ALL_PARTICIPANTS ALL_PARTICIPANTS '[]' >/dev/null
export AGENT_NAME=${SERVICE_PREFIX}_${AGENT_ID}
$CMD agents ensure-deleted $AGENT_NAME
echo $CMD agents deploy --name $AGENT_NAME --key $KEY_ID --service-ipfs-hash $IPFS_HASH --variables $VARIABLES

#$CMD agents wait $AGENT_NAME DEPLOYED --timeout=120

#$CMD agents restart $AGENT_NAME

#$CMD agents wait $AGENT_NAME STARTED --timeout=120





