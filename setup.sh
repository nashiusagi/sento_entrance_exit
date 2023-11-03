#!/bin/bash
set -ue


function print_notice() {
    echo -e "\e[1;35m$*\e[m" # magenta
}

function gpu_confirm() {
    local result
    result=`lspci | grep -i nvidia`
    echo $result
}

function main() {
    poetry config virtualenvs.in-project true
    pyenv local $(printf '%s' $(<.python-version))
    poetry install
    poetry update
}

main