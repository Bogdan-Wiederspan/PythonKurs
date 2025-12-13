"""
Implementation of the 2D board for GoL consisting of cells

2023 Johannes Lange
"""

import random

from cell import Cell


class Board:
    def __init__(self, size):
        self.size = size
        # initialize the board with cells
        self.board = []
        for row in range(size):
            self.board.append([Cell() for col in range(size)])

    def __getitem__(self, rowcol):
        """allows you to access a cell of a board object with `board[row, col]`"""
        row, col = rowcol
        return self.board[row][col]

    def print(self):
        for row in range(self.size):
            for col in range(self.size):
                print(self[row, col], end=" ")
            print()
        print()

    def count_alive_neighbours(self, row, col):
        """count the number of alive neighbours of this cell"""
        count = 0
        for dr in range(-1, 2):
            nr = row + dr
            if not 0 <= nr < self.size:
                continue  # out of the board
            for dc in range(-1, 2):
                if dr == dc == 0:
                    continue
                nc = col + dc
                if not 0 <= nc < self.size:
                    continue  # out of the board
                if self[nr, nc].is_alive():
                    count += 1
        return count

    def update_board(self):
        """calculate the new generation status und update THIS board"""

        # store index tuples of alive cells for the next generation
        next_gen_alive = []
        for row in range(self.size):
            for col in range(self.size):
                n_alive = self.count_alive_neighbours(row, col)
                if self[row, col].is_alive() and 2 <= n_alive <= 3:
                    next_gen_alive.append((row, col))
                elif not self[row, col].is_alive() and n_alive == 3:
                    next_gen_alive.append((row, col))

        # next generation: mark all dead first
        for row in range(self.size):
            for col in range(self.size):
                self[row, col].set_dead()
        # set alive the ones we determined
        for rowcol in next_gen_alive:
            row, col = rowcol
            self[row, col].set_alive()

    def initialize_randomly(self, alive_probability):
        """set cells alive with `alive_probability` (between 0 and 1) and dead otherwise"""
        for row in range(self.size):
            for col in range(self.size):
                if random.random() < alive_probability:
                    self[row, col].set_alive()
                else:
                    self[row, col].set_dead()

    def insert_blinker(self, row, col):
        """insert a blinker object at the given position"""
        self[row, col - 1].set_alive()
        self[row, col].set_alive()
        self[row, col + 1].set_alive()

    def insert_glider(self, row, col):
        """insert a glider object at the given position"""
        self[row, col].set_alive()
        self[row + 1, col + 1].set_alive()
        self[row + 2, col + 1].set_alive()
        self[row + 2, col].set_alive()
        self[row + 2, col - 1].set_alive()
