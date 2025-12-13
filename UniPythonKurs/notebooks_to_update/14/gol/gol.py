#!/usr/bin/env python3

"""
Play a game of Conway's Game of Life.

Usage examples:

./gol.py --insert-blinker 4 5
./gol.py --insert-glider 2 3 --update-interval .1
./gol.py --init-random .3

Get the full help with
./gol.py --help

2023 Johannes Lange
"""

import argparse
import os
import sys
import time

from board import Board


def main():
    parser = argparse.ArgumentParser(
        prog="Game of Life", description="Run the Game of Life!"
    )
    parser.add_argument(
        "--size", help="The size of the board (square)", type=int, default=20
    )
    parser.add_argument(
        "--update-interval",
        help="The update interval (in seconds) to display the next gernation",
        type=float,
        default=0.2,
    )
    parser.add_argument(
        "--insert-blinker",
        type=int,
        nargs=2,
        metavar=("ROW", "COL"),
        help="Insert a blinker at the given coordinates",
        default=None,
    )
    parser.add_argument(
        "--insert-glider",
        type=int,
        nargs=2,
        metavar=("ROW", "COL"),
        help="Insert a glider at the given coordinates",
        default=None,
    )
    parser.add_argument(
        "--init-random",
        type=float,
        metavar=("PROBABILITY"),
        help="Initialize the alive state of each cell with the given probability for being alive",
        default=None,
    )
    args = parser.parse_args()

    b = Board(args.size)
    if args.insert_blinker is not None:
        b.insert_blinker(*args.insert_blinker)
    if args.insert_glider is not None:
        b.insert_glider(*args.insert_glider)
    if args.init_random is not None:
        b.initialize_randomly(args.init_random)

    while True:  # continue until user interrupts
        os.system("clear")  # clear terminal
        b.print()  # print the current generation
        b.update_board()  # determine the next generation
        print("Press Ctrl+C to cancel")
        time.sleep(args.update_interval)  # wait for some time for display purposes
    return 0


if __name__ == "__main__":
    sys.exit(main())
