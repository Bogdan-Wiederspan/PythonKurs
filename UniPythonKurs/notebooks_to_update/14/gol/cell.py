"""
Implementation of the `Cell` class, representing a single cell of GoL

2023 Johannes Lange
"""


class Cell:
    def __init__(self, alive=False):
        # store the alive state
        self.alive = alive

    def is_alive(self):
        # return the alive state
        return self.alive

    def set_alive(self):
        # set the cell alive
        self.alive = True

    def set_dead(self):
        # set the cell dead
        self.alive = False

    def __str__(self):
        # return the string "o" if alive and " " if dead
        if self.is_alive():
            return "o"
        return " "
