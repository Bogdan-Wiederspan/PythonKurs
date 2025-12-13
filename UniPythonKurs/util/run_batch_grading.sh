#!/usr/bin/env bash

action() {
    local shell_is_zsh="$( [ -z "${ZSH_VERSION}" ] && echo "false" || echo "true" )"
    local this_file="$( ${shell_is_zsh} && echo "${(%):-%x}" || echo "${BASH_SOURCE[0]}" )"
    local this_dir="$( cd "$( dirname "${this_file}" )" && pwd )"
    local abk_dir="$( cd "$( dirname "${this_dir}" )" && pwd )"
    local teaching_dir="${HOME}/UHH/teaching/python_abk_ss25"

    # 01
    # local SOLUTION="${abk_dir}/01_exercise_introduction.ipynb"
    # local TO_GRADE="${teaching_dir}/abgaben01"
    # local CSV="${teaching_dir}/grades01.csv"
    # # teaching nb, reduced sheet
    # local SKIP="Constantin+Loss Anh+Chau+Nguyen"

    # 02
    # local SOLUTION="${abk_dir}/02_exercise_variables.ipynb"
    # local TO_GRADE="${teaching_dir}/abgaben02"
    # local CSV="${teaching_dir}/grades02.csv"
    # # teaching nb
    # local SKIP="Mats+Ri+wick"

    # 03
    # local SOLUTION="${abk_dir}/03_exercise_loops.ipynb"
    # local TO_GRADE="${teaching_dir}/abgaben03"
    # local CSV="${teaching_dir}/grades03.csv"
    # # teaching nb, teaching nb
    # local SKIP="Constantin+Loss Leon+Peitz"
    # local DEBUG_AFTER=""

    # 04
    # local SOLUTION="${abk_dir}/04_exercise_datastructures.ipynb"
    # local TO_GRADE="${teaching_dir}/abgaben04"
    # local CSV="${teaching_dir}/grades04.csv"
    # uploaded lecture nb
    # local SKIP="Umut+Sahin"

    # 05
    # local SOLUTION="${abk_dir}/05_exercise_flowcontrol.ipynb"
    # local TO_GRADE="${teaching_dir}/abgaben05"
    # local CSV="${teaching_dir}/grades05.csv"
    # local SKIP=""

    # 06
    # local SOLUTION="${abk_dir}/06_exercise_ownfunctions.ipynb"
    # local TO_GRADE="${teaching_dir}/abgaben06"
    # local CSV="${teaching_dir}/grades06.csv"
    # local SKIP=""

    # 07
    # local SOLUTION="${abk_dir}/07_exercise_classes.ipynb"
    # local TO_GRADE="${teaching_dir}/abgaben07"
    # local CSV="${teaching_dir}/grades07.csv"
    # local SKIP=""

    # 08
    local SOLUTION="${abk_dir}/08_exercise_data.ipynb"
    local TO_GRADE="${teaching_dir}/abgaben08"
    local CSV="${teaching_dir}/grades08.csv"
    local SKIP=""

    # 09
    # local SOLUTION="${abk_dir}/09_exercise_numpy.ipynb"
    # local TO_GRADE="${teaching_dir}/abgaben09"
    # local CSV="${teaching_dir}/grades09.csv"
    # # empty notebook file
    # local SKIP="Fiona+Bergmann"

    # 10
    # manual grading :)

    # 11
    # local SOLUTION="${abk_dir}/11_exercise_scripts_softwareengineering.ipynb"
    # local TO_GRADE="${teaching_dir}/abgaben11"
    # local CSV="${teaching_dir}/grades11.csv"
    # local SKIP=""

    # 12
    # local SOLUTION="${abk_dir}/12_exercise_sympy.ipynb"
    # local TO_GRADE="${teaching_dir}/abgaben12"
    # local CSV="${teaching_dir}/grades12.csv"
    # local SKIP=""

    # 13
    # local SOLUTION="${abk_dir}/13_exercise_versioncontrol.ipynb"
    # local TO_GRADE="${teaching_dir}/abgaben13"
    # local CSV="${teaching_dir}/grades13.csv"
    # # uploaded lecture notebook, uploaded exercise 12
    # local SKIP="Dilsher+Singh Leon+Zwanziger"

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
            --network=none\
            --bind ./util:$HOME/util:ro \
            --bind "${TO_GRADE}":"${TO_GRADE}":ro \
            --bind "${SOLUTION}":$HOME/solution.ipynb:ro \
            --bind "${CSV}":"${CSV}" \
            singularity/python3.9.2.sif \
            ./util/grade.py --sample-solution solution.ipynb --zipfile "${TO_GRADE}" --grading-csv "${CSV}" --skip "${SKIP}" --debug-after "${DEBUG_AFTER}"
    elif [ "${container_engine}" = "docker" ]; then
        touch "${CSV}"
        docker run \
            --rm \
            -ti \
            --network none \
            -v "${SOLUTION}":/root/solution.ipynb:ro \
            -v "${TO_GRADE}":/root/abgabe.zip:ro \
            -v "${CSV}":/root/grades.csv \
            -v "${abk_dir}/util":/root/util:ro \
            python_abk \
            ./util/grade.py --sample-solution "solution.ipynb" --zipfile "abgabe.zip" --grading-csv "grades.csv" --skip "${SKIP}" --debug-after "${DEBUG_AFTER}"
    else
        >&2 "unknown container engine: '${container_engine}'"
        return "1"
    fi

    # alternative command that one could use to implement cleanups in between (monitor which files appear; delete them)
    # bash -c "./util/grade.py --sample-solution solution.ipynb --notebook $HOME/to_grade/02_functions.ipynb; touch tmp.tmp; ls -la; rm *.*; ls -la"
}
action "$@"
