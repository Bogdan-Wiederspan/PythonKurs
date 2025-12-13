#!/usr/bin/env python3

"""
Process notebooks to tag cells and strip solutions.

2023 Johannes Lange
"""

import argparse
import ast
import copy
import json
import re

import nbconvert
import nbformat


def main():
    parser = argparse.ArgumentParser(
        description="Process notebooks to tag cells and strip solutions."
    )
    parser.add_argument("files", nargs="+", help="Files to process")
    parser.add_argument(
        "--tag", action="store_true", help="tag the cells containing problems"
    )
    parser.add_argument(
        "--strip-solutions",
        action="store_true",
        help="strip solutions initiated with `# SOLUTION`",
    )
    parser.add_argument(
        "--strip-custom-tests",
        action="store_true",
        help="strip custom tests initiated with `# PROBLEM-TEST`",
    )
    parser.add_argument(
        "--strip-live-demos",
        action="store_true",
        help="strip live demos between `# BEGIN-LIVE` and `# END-LIVE`",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="overwrite the input files (otherwise print to stdout)",
    )
    args = parser.parse_args()

    for fname in args.files:
        with open(fname) as f:
            nb = nbformat.reader.read(f)
        # create an executed version to get sample solutions
        nbex = copy.deepcopy(nb)
        ep = nbconvert.preprocessors.ExecutePreprocessor(
            kernel_name="python3", allow_errors=True,
        )
        ep.preprocess(nbex)

        # set user in metadata to dummy user
        # (to be altered by the mechanism through which the students get their notebook)
        nb.metadata.user = "DUMMYUSER"

        # additional metadata for tracking solution validity
        nb.metadata.ubsf = "DUMMY64USER"

        problem_number = 0
        for cell, cellex in zip(nb.cells, nbex.cells):
            if cell.cell_type != "code":
                continue
            if args.tag and (pp := problem_points(cell)) is not None:
                problem_number += 1
                tag_problem(cell, cellex, problem_number, pp)
            if args.strip_live_demos:
                strip_live_demo(cell)
            if args.strip_custom_tests:
                strip_custom_test(cell)
            if args.strip_solutions:
                strip_solution(cell, cellex)
        if args.in_place:
            nbformat.write(nb, fname)
        else:
            print(nbformat.writes(nb))


def problem_points(cell):
    """returns: number of points if the cell contains a problem, None otherwise"""
    for line in cell.source.splitlines():
        if m := re.match(r"^.*#\s*problem\s*\((\d+)\).*$", line.lower()):
            groups = m.groups()
            assert len(groups) == 1
            return int(groups[0])
    return None


def tag_problem(cell, cellex, problem_number, problem_points):
    cell.metadata.deletable = False
    cell.metadata.tags = cell.metadata.get("tags", []) + ["problem"]
    cell.metadata.problem_number = problem_number
    cell.metadata.points = problem_points
    cell.metadata.output_type = get_output_type(cellex)
    cell.metadata.has_custom_test = any(line.startswith("# PROBLEM-TEST") for line in cell.source.splitlines())


def strip_live_demo(cell):
    lines = cell.source.splitlines()
    if "# BEGIN-LIVE" not in lines:
        return
    assert "# END-LIVE" in lines, "you need BEGIN-LIVE and END-LIVE"
    lines = (
        lines[: lines.index("# BEGIN-LIVE")]
        + ["# do this live together"]
        + lines[lines.index("# END-LIVE") + 1 :]
    )
    cell.source = "\n".join(lines)


def strip_solution(cell, cellex):
    lines = cell.source.splitlines()
    if "# SOLUTION" not in lines:
        return
    lines = lines[: lines.index("# SOLUTION")]
    lines.append(
        "# enter your SOLUTION in this cell below this comment (do not change anything in or above this line)",
    )
    if not cell.metadata.get("has_custom_test", False):
        lines.append(f"# hint: expected result type is {get_output_type(cellex)}")

    cell.source = "\n".join(lines) + "\n"


def strip_custom_test(cell):
    lines = cell.source.splitlines()
    stripped = []
    for line in lines:
        if line.startswith("# PROBLEM-TEST"):
            break
        stripped.append(line)
    cell.source = "\n".join(stripped)


def get_output_entry(cell, output_type):
    """
    Returns one entry from the "outputs" field, assuming there is only one entry.
    Otherwise it will fail. If no matching entry is found, None is returned.

    `output_type` is supposed to be "execute_result" or "error"
    """
    if "outputs" not in cell.keys():
        return None
    outputs = list(filter(lambda o: o["output_type"] == output_type, cell.outputs))
    if not outputs:
        return None
    assert len(outputs) == 1
    return outputs[0]


def get_output(cell):
    output = get_output_entry(cell, "execute_result")
    if not output:
        return None
    output = list(output.data.values())
    assert len(output) == 1
    return output[0]


def get_error(cell):
    """returns the dict-like error object, containing ename and evalue"""
    output = get_output_entry(cell, "error")
    if not output:
        return None
    return output


def get_output_type(cell):
    return _get_output_type(get_output(cell))


def _get_output_type(output):
    try:
        return type(ast.literal_eval(output)).__name__
    except ValueError:
        return "None"


def cast_output(output, round_float=False):
    # when output is not a string, return it as is assuming it is already casted
    if not isinstance(output, str):
        return output

    # try a literal evaluation
    # if the output is not broken in any way, this fails for literal strings in which case we
    # can just return the output as is
    try:
        casted = ast.literal_eval(output)
    except (ValueError, SyntaxError):
        return output

    # round floats in several simply nested structures
    rnd = (lambda f: round(float(f), 2)) if round_float else (lambda f: f)
    if isinstance(casted, float):
        return rnd(casted)
    if isinstance(casted, (list, tuple)):
        return type(casted)((rnd(v) if isinstance(v, float) else v) for v in casted)

    # return as is
    return casted


if __name__ == "__main__":
    main()
