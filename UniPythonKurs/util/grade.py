#!/usr/bin/env python3

"""
Tool to grade solutions.

Execute this in a singularity/apptainer container.
Use
  --containall --net --network=none
to make sure your system is not exposed to the notebook code and no network requests are possible!

2023 Johannes Lange
"""

import argparse
from collections import defaultdict
import contextlib
import csv
from operator import itemgetter
import os
import pathlib
import signal
import sys
import tempfile
import zipfile
import copy
import ast

import nbconvert
import nbformat
import pandas as pd

import process_nb


def main():
    parser = argparse.ArgumentParser(
        description="Grade a notebook based on a sample solution notebook."
    )
    parser.add_argument(
        "--sample-solution",
        help=".ipynb file with the sample solution",
        required=True,
        type=pathlib.Path,
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--notebook",
        help=".ipynb file with the notebook to be graded",
        type=pathlib.Path,
    )
    input_group.add_argument(
        "--zipfile",
        help="zip file with student solutions as downloaded from moodle",
        type=pathlib.Path,
    )
    parser.add_argument(
        "--grading-csv",
        help="Grading file as downloaded from moodle `Grades-*.csv`."
        "The file will be overwritten!"
        "Required when using --zipfile, but not allowed with --notebook.",
        type=pathlib.Path,
    )
    parser.add_argument(
        "--skip",
        nargs="*",
        help="names of users to skip",
    )
    parser.add_argument(
        "--force-eid",
        action="store_true",
        help="set grade to 0 if the excersise ID does not match the sample solution",
    )
    parser.add_argument(
        "--debug-after",
        help="start grading after this user and do not store grades"
    )
    args = parser.parse_args()
    if args.zipfile and not args.grading_csv:
        parser.error("--zip-file requires --grading-csv")
    elif args.notebook and args.grading_csv:
        parser.error("--grading-csv cannot be used with --notebook")
    if args.skip:
        args.skip = sum((s.split() for s in args.skip), [])
        args.skip = list(filter(bool, args.skip))

    # make paths absolute, so we can change working directory later for execution
    args.sample_solution = args.sample_solution.resolve()
    if args.notebook:
        args.notebook = args.notebook.expanduser().resolve()
    elif args.zipfile:
        args.zipfile = args.zipfile.expanduser().resolve()
        args.grading_csv = args.grading_csv.expanduser().resolve()

    with change_to_tempdir():
        sample_solution, sample_eid = get_sample_solution(args.sample_solution)
    if args.notebook:
        print_single_notebook_grading(args.notebook, sample_solution, sample_eid)
    else:  # args.zipfile:
        id_grades = list(bulk_grade(args.zipfile, sample_solution, sample_eid, skip_names=args.skip, debug_after=args.debug_after))
        print()
        if args.debug_after:
            print("debugging finished")
            return
        users = defaultdict(list)
        df = pd.read_csv(args.grading_csv)
        users_with_eid_mismatch = []
        for participant_id, username, grade, feedback, eid_match in id_grades:
            loc = df.Identifier == f"Participant {participant_id}"
            full_name = df.loc[loc, "Full name"].item()
            users[username].append(full_name)
            if grade <= 0:
                print("maybe look at", participant_id, full_name, username, feedback)
            if not eid_match:
                users_with_eid_mismatch.append(f"{username}:{participant_id}")
            if args.force_eid and not eid_match:
                grade = 0
                feedback = "Submitting notebooks from previous semesters is not allowed."
            df.loc[loc, "Feedback comments"] = feedback
            df.loc[loc, "Grade"] = grade
        df.to_csv(args.grading_csv, index=False, sep=",", quoting=csv.QUOTE_NONNUMERIC)
        print()
        for uname, names in users.items():
            if (n := len(names)) > 1:
                print(f"username {uname} used {n} times:")
                print(names)
        if users_with_eid_mismatch:
            print(f"{len(users_with_eid_mismatch)} user(s) with eid mismatch: {users_with_eid_mismatch}")


@contextlib.contextmanager
def change_to_tempdir():
    """Temporarily change to a random temporary directory.

    Use this as a contextmanager to execute something in a temporary directory and return back afterwards.
    Using tempfile.TemporaryDirectory ensures that it will be deleted if the context is left.
    """
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmpdirname:
        os.chdir(tmpdirname)
        try:
            yield
        finally:
            os.chdir(cwd)


class TimeoutException(Exception):
    pass


@contextlib.contextmanager
def runtime_limit(limit_time):
    """context manager to limit the runtime to limit_time seconds"""

    def signal_handler(signum, frame):
        raise TimeoutException("Runtime too long!")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(limit_time)
    try:
        yield
    finally:
        signal.alarm(0)


def print_single_notebook_grading(notebook_path, sample_solution, sample_eid):
    with change_to_tempdir():
        points_gained, wrong_exercises, username, eid = grade_notebook(
            notebook_path, sample_solution
        )
    points_max = sum(map(itemgetter("points"), sample_solution.values()))
    feedback = str(points_gained)
    if wrong_exercises:
        feedback += "<br>problem_no: expected / yours"
        for pn, txt in wrong_exercises.items():
            feedback += f"<br>{pn}: {txt}"
    print("Username:", username)
    if eid != sample_eid:
        print(f"WARNING: eid {eid} does not match sample eid {sample_eid}")
    print(f"{sum(points_gained.values())} / {points_max} {feedback}")


def bulk_grade(zipfilename, sample_solution, sample_eid, skip_names=None, debug_after=None):
    """Generator that yields tuples (pariticpant_id, username, grade, feedback comments)"""
    in_container = bool(
        os.environ.get("SINGULARITY_CONTAINER")
        or os.environ.get("APPTAINER_CONTAINER")
        or os.getenv("DOCKER_PYTHON_ABK") == "1"
    )
    if not in_container:
        sys.exit(
            "Run bulk grading in a singularity/apptainer/docker container "
            "(with --containall --net --network=none).\n"
            "Do not execute arbitrary notebooks blindly on your own system!"
        )

    print("grading", zipfilename)
    print("skipping", skip_names)
    points_max = sum(map(itemgetter("points"), sample_solution.values()))

    def iter_inputs():
        if os.path.isdir(zipfilename):
            yield from sorted(pathlib.Path(zipfilename).iterdir(), key=str)
        else:
            with zipfile.ZipFile(zipfilename) as myzip:
                yield from sorted(zipfile.Path(myzip).iterdir(), key=str)

    _allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_+-")

    def sanitize(s):
        return "".join(c if c in _allowed_chars else "+" for c in s)

    for folder in iter_inputs():
        actual_folder_name = sanitize(folder.name)
        if not folder.is_dir():
            continue
        if debug_after:
            print("skipping", actual_folder_name)
            if debug_after in actual_folder_name:
                debug_after = None
            continue
        if skip_names and any(skip_name in actual_folder_name for skip_name in skip_names):
            print("skipping", actual_folder_name)
            continue
        print(actual_folder_name, end="")
        participant_id = int(folder.name.split("_")[2])  # the actual participant id is now the third part!
        files = list(folder.iterdir())
        notebook_files = list(filter(lambda f: f.name.endswith(".ipynb"), files))

        if not len(notebook_files) == 1:
            print(
                "\n   Does not contain =1 notebook:",
                list(map(lambda f: f.name, files)),
            )
            yield participant_id, "None", 0, "No .ipynb file was submitted.", True
            continue

        try:
            with change_to_tempdir(), runtime_limit(60):
                points_gained, wrong_exercises, username, eid = grade_notebook(
                    notebook_files[0], sample_solution
                )
        except TimeoutException as e:
            print("\nExecution timeout!")
            yield participant_id, "None", 0, "Notebook could not be executed. Does it contain an infinite loop?", True
            continue

        grade = sum(points_gained.values())
        feedback = str(points_gained)
        if wrong_exercises:
            feedback += "<br>problem_no: expected / yours"
            for pn, txt in wrong_exercises.items():
                feedback += f"<br>{pn}: {txt}"
        feedback = feedback.replace("\n", "<br>")
        print(f" ({username}, {participant_id})")
        print("  ", grade, feedback)
        if eid != sample_eid:
            print(f"WARNING: eid {eid} does not match sample eid {sample_eid}")
        yield participant_id, username, grade, feedback, eid == sample_eid


def grade_notebook(fname, sample_solution):
    """returns a dictionary with points for each exercise (0 if student solution is wrong),
    a dictionary of expected/student results for wrong exercises, and the username from metadata
    """
    # use a dictionary with problem number as key, so there can be no double counting
    points_gained = {}
    wrong_exercises = {}  # problem number -> string "expected/your"

    # don't use open(fname) to make it also work with zipfile.Path
    with fname.open() as f:
        try:
            nb = nbformat.reader.read(f)
        except UnicodeDecodeError:
            return {}, {0: "UNREADABLE"}, "unknown-user"

    try:
        nbformat.validate(nb)
    except nbformat.ValidationError:
        return {}, {0: "NOT A VALID NOTEBOOK FILE"}, "unknown-user"

    username = nb.metadata.get("user", "None")
    eid = nb.metadata.get("eid", "None")

    # append custom tests where necessary
    for cell in nb.cells:
        if "problem" not in cell.metadata.get("tags", []):
            continue
        if "problem_number" not in cell.metadata:
            print("cell tagged 'problem' but no problem_number in metadata!")
            continue
        ssolution = sample_solution[cell.metadata.problem_number]
        if ssolution["has_custom_test"]:
            cell.source += "\n" + ssolution["custom_test_lines"]
        # print(cell.source)

    # execute the notebook top-to-bottom with the custom tests appended where necessary
    ep = nbconvert.preprocessors.ExecutePreprocessor(
        kernel_name="python3", allow_errors=True,
    )
    ep.preprocess(nb)

    # get problem cells
    problem_cells = [
        cell
        for cell in nb.cells
        if "problem" in cell.metadata.get("tags", []) and "problem_number" in cell.metadata
    ]
    if len(problem_cells) != len(sample_solution):
        raise ValueError(
            f"found {len(problem_cells)} problem cells, expected {len(sample_solution)}; found " +
            ",".join(str(c.get("metadata", {}).get("problem_number")) for c in problem_cells),
        )

    # alternative solutions, tuples mapped to problem numbers e.g. 3 -> (alternative1, alternative2)
    alternatives = {}

    for cell in problem_cells:
        # verify the problem number is valid
        problem_no = cell.metadata.problem_number
        if problem_no not in sample_solution:
            raise ValueError(f"problem number {problem_no} not in sample solution")

        # get sample solution and points
        sample_solution_cell = copy.deepcopy(sample_solution[problem_no])
        # round floats when there is no custom test
        round_float = not sample_solution_cell.get("has_custom_test", False)
        sample_solution_str = sample_solution_cell["output"]
        sample_solution_casted = process_nb.cast_output(sample_solution_str, round_float=round_float)
        # extend by custom alternatives for a-posteriori fixes
        accepted_solutions = (sample_solution_casted, *alternatives.get(problem_no, ()))
        points = sample_solution_cell["points"]

        # get the student solution and catch errors
        student_solution_str = process_nb.get_output(cell)
        student_solution_casted = process_nb.cast_output(student_solution_str, round_float=round_float)
        error = process_nb.get_error(cell) if student_solution_casted is None else False

        # actual comparison
        solved = student_solution_casted in accepted_solutions
        points_gained[problem_no] = points if solved else 0

        if error:
            wrong_exercises[problem_no] = f"{error.ename}: {error.evalue}"
        elif not solved:
            wrong_exercises[problem_no] = f"{sample_solution_str} / {student_solution_str}"

    return points_gained, wrong_exercises, username, eid


def get_sample_solution(fname):
    with open(fname) as f:
        nb = nbformat.reader.read(f)
    nbformat.validate(nb)
    # create an executed version to get sample solutions
    ep = nbconvert.preprocessors.ExecutePreprocessor(
        kernel_name="python3", allow_errors=True
    )
    ep.preprocess(nb)
    eid = nb.metadata.get("eid", "None")
    problem_number = 0
    sample_solution = {}  # problem_number: "solution dict"
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        if (pp := process_nb.problem_points(cell)) is None:
            continue
        problem_number += 1
        process_nb.tag_problem(cell, cell, problem_number, pp)
        solution = {
            "points": pp,
            "has_custom_test": False,
            "output": process_nb.get_output(cell),
            "output_type": None,
        }
        if cell.metadata.has_custom_test:
            solution["has_custom_test"] = True
            solution["custom_test_lines"] = get_custom_test_lines(cell)
        else:
            solution["output_type"] = cell.metadata.output_type
        sample_solution[problem_number] = solution
    return sample_solution, eid


def get_custom_test_lines(cell):
    lines = cell.source.splitlines()
    test_lines = []
    found_start = False
    while lines:
        line = lines.pop(0)
        if line.startswith("# PROBLEM-TEST"):
            found_start = True
            continue
        if found_start:
            test_lines.append(line)
    return "\n".join(test_lines) if test_lines else None


if __name__ == "__main__":
    main()
