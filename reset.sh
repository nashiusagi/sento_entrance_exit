#!/bin/bash
set -ue

curl --location --request PUT '18.179.180.74:3000/api/v1/sentos/34/update_is_opened?is_opened=false'
curl --location --request PUT '18.179.180.74:3000/api/v1/sentos/34/update_is_opened?is_opened=true'