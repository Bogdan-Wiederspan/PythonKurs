#!/usr/bin/env bash

action() {
    local shell_is_zsh="$( [ -z "${ZSH_VERSION}" ] && echo "false" || echo "true" )"
    local this_file="$( ${shell_is_zsh} && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
    local this_dir="$( cd "$( dirname "${this_file}" )" && pwd )"
    local abk_dir="$( cd "$( dirname "${this_dir}" )" && pwd )"
    local teaching_dir="${HOME}/UHH/teaching/python_abk_ss25"

    # local SOLUTION="${abk_dir}/03_exercise_loops.ipynb"
    # local SOLUTION="${abk_dir}/04_exercise_datastructures.ipynb"
    # local SOLUTION="${abk_dir}/05_exercise_flowcontrol.ipynb"
    # local SOLUTION="${abk_dir}/06_exercise_ownfunctions.ipynb"
    local SOLUTION="${abk_dir}/07_exercise_classes.ipynb"
    local TO_GRADE="${teaching_dir}/abgaben07_custom/sahar_rezai.ipynb"

    if [ -z "${TO_GRADE}" ] && [ -f "$1" ]; then
        TO_GRADE="$1"
        shift
    fi

    if [ ! -f "${TO_GRADE}" ]; then
        >&2 echo "notebook to grade does not exist: ${TO_GRADE}"
        return "2"
    fi

    local container_engine
    if [ -z "${container_engine}" ]; then
        if [ ! -z "${1}" ]; then
            container_engine="${1}"
        elif [ "$( uname -s )" = "Darwin" ]; then
            # use docker on mac
            container_engine="docker"
        else
            # use singularity in all other cases
            container_engine="singularity"
        fi
    fi

    if [ "${container_engine}" = "singularity" ]; then
        singularity exec \
            --containall \
            --net \
            --network=none \
            --bind ./util:$HOME/util:ro \
            --bind "${TO_GRADE}":"${TO_GRADE}":ro \
            --bind "${SOLUTION}":$HOME/solution.ipynb:ro \
            singularity/python3.9.2.sif \
            ./util/grade.py --sample-solution solution.ipynb --notebook "${TO_GRADE}"
    elif [ "${container_engine}" = "docker" ]; then
        docker run \
            --rm \
            -ti \
            --network none \
            -v "${SOLUTION}":/root/solution.ipynb:ro \
            -v "${TO_GRADE}":/root/abgabe.ipynb:ro \
            -v "${abk_dir}/util":/root/util:ro \
            python_abk \
            ./util/grade.py --sample-solution "solution.ipynb" --notebook "abgabe.ipynb"
    else
        >&2 "unknown container engine: '${container_engine}'"
        return "1"
    fi
}
action "$@"
