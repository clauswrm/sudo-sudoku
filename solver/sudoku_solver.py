""" Sudoku solver that uses graph coloring to solve boards. """
__author__ = 'Claus Martinsen'


class Vertex:
    def __init__(self, x, y):
        self.coord = (x, y)
        self.neighbors = []
        self.number = 0
        self.number_options = []
        self.illegal_numbers = []

    def add_neighbor(self, neighbor):
        if neighbor not in self.neighbors:
            self.neighbors.append(neighbor)
            # if self not in neighbor.neighbors:
            #    neighbor.add_neighbor(self)

    def remove_neighbor(self, neighbor):
        if neighbor in self.neighbors:
            self.neighbors.remove(neighbor)

    def add_illegal_number(self, number):
        if number in self.number_options:
            self.number_options.remove(number)
        if number not in self.illegal_numbers:
            self.illegal_numbers.append(number)

    def rank(self):
        return len(self.neighbors)

    def __str__(self):
        return str(self.number) if self.number is not None else '-'

    def __repr__(self):
        return '<Vertex: R=' + str(self.rank()) + ', C=' + str(self.number) + ', XY=' + str(self.coord) + '>'


class Graph:
    def __init__(self, vertices=list()):
        self.vertices = vertices

    def add(self, vertex):
        self.vertices.append(vertex)

    @staticmethod
    def connect(vertex1, vertex2):
        vertex1.add_neighbor(vertex2)

    def __add__(self, other):
        return self.vertices + other.vertices

    def __iadd__(self, other):
        self.vertices += other.vertices

    def __len__(self):
        return len(self.vertices)

    def edge_count(self):
        i = 0
        for vertex in self:
            i += vertex.rank()
        i //= 2  # Each edge gets counted exactly twice
        return i

    def __contains__(self, item):
        return item in self.vertices

    def __getitem__(self, item):
        return self.vertices[item]

    def __setitem__(self, key, value):
        self.vertices[key] = value

    def __delitem__(self, key):
        del self.vertices[key]

    def __iter__(self):
        return self.vertices.__iter__()

    def __str__(self):
        return str(self.vertices)

    def __repr__(self):
        return repr(self.vertices)


class Sudoku_solver:
    def __init__(self, sudoku_board, dim=3):
        self.board = sudoku_board
        self.graph = Graph()
        self.dim = dim
        self.memory = []
        self._setup()  # Sets up the sudoku board and graph

    def _setup(self):
        k = self.dim ** 2
        for v_y in range(k):
            for v_x in range(k):
                n = self.board[v_y][v_x]
                self.board[v_y][v_x] = Vertex(x=v_x, y=v_y)
                if n != 0:
                    self.board[v_y][v_x].number = n

        for v_y in range(k):
            for v_x in range(k):
                for x in range(k):
                    if x != v_x:
                        self.board[v_y][v_x].add_neighbor(self.board[v_y][x])
                for y in range(k):
                    if y != v_y:
                        self.board[v_y][v_x].add_neighbor(self.board[y][v_x])

                q_y, q_x = self.dim * (v_y // self.dim), self.dim * (v_x // self.dim)
                for y in range(self.dim):
                    for x in range(self.dim):
                        if q_y + y != v_y or q_x + x != v_x:
                            self.board[v_y][v_x].add_neighbor(self.board[q_y + y][q_x + x])

        for row in self.board:
            for vertex in row:
                self.graph.add(vertex)

    def save_state(self, uncertian_vertex, uncertain_number):
        state = [[0 for _ in range(self.dim ** 2)] for _ in range(self.dim ** 2)]
        illegal_numbers = [[[] for _ in range(self.dim ** 2)] for _ in range(self.dim ** 2)]
        for i, row in enumerate(self.board):
            for j, vertex in enumerate(row):
                state[i][j] = vertex.number
                illegal_numbers[i][j] = vertex.illegal_numbers.copy()

        self.memory.append((state, illegal_numbers, uncertian_vertex, uncertain_number))

    def load_previous_legal_state(self):
        state, illegal_numbers, vertex, illegal_number = self.memory.pop()
        for i, row in enumerate(state):
            for j, number in enumerate(row):
                self.board[i][j].number = number
                self.board[i][j].illegal_numbers = illegal_numbers[i][j]

        vertex.add_illegal_number(illegal_number)

    def update_possible_numbers(self):
        for vertex in self.graph:
            if vertex.number == 0:  # Not colored
                nums = [i for i in range(1, self.dim ** 2 + 1)]

                for neighbor in vertex.neighbors:
                    if neighbor.number != 0 and neighbor.number in nums:
                        nums.remove(neighbor.number)
                for illegal_number in vertex.illegal_numbers:
                    if illegal_number in nums:
                        nums.remove(illegal_number)

                vertex.number_options = nums
            else:
                vertex.number_options = []

    def numerate_least_known_vertex(self):
        """
        When no cell can be given a number with 100% certainty, the one that
        is adjacent to the largest number of un-numbered vertices (i.e. the one
        with the most possible numbers) is chosen and numbered to the number
        with the lowest value that is not used by its neighbors.
        """
        lkv = self.graph[0]
        for vertex in self.graph:
            if len(vertex.number_options) > len(lkv.number_options):
                lkv = vertex

        i = min(lkv.number_options)
        self.save_state(lkv, i)
        lkv.number = i

    def fill_in_sole_candidates(self):
        """
        When a specific cell can only contain a single number, that number is a
        "sole candidate". This happens whenever all other numbers but the
        candidate number exists in either the current block, column or row.

        :return: Whether or not a sole candidate was found.
        :rtype: bool
        """
        changed = False
        for vertex in self.graph:
            if len(vertex.number_options) == 1:
                vertex.number = vertex.number_options[0]
                changed = True
        return changed

    def fill_in_unique_candidates(self):
        """
        If a number can only be put in a single cell within a block, column or
        row, then that number is guaranteed to fit there. Such a number is a
        unique canditate.

        :return: Whether or not a unique candidate was found.
        :rtype: bool
        """
        changed = False
        for v_y, row in enumerate(self.board):
            for v_x, vertex in enumerate(row):
                for number in vertex.number_options:

                    hidden_row, hidden_col, hidden_box = True, True, True
                    for x in range(self.dim ** 2):  # Try to find unique in row
                        if x != v_x:
                            if number in self.board[v_y][x].number_options:
                                hidden_row = False
                                break
                    if hidden_row:
                        vertex.number = number
                        changed = True
                        continue

                    for y in range(self.dim ** 2):  # Try to find unique in column
                        if y != v_y:
                            if number in self.board[y][v_x].number_options:
                                hidden_col = False
                                break
                    if hidden_col:
                        vertex.number = number
                        changed = True
                        continue

                    q_y, q_x = self.dim * (v_y // self.dim), self.dim * (v_x // self.dim)
                    for y in range(self.dim):  # Try to find unique in box
                        for x in range(self.dim):
                            if q_y + y != v_y or q_x + x != v_x:
                                if number in self.board[q_y + y][q_x + x].number_options:
                                    hidden_box = False
                    if hidden_box:
                        vertex.number = number
                        changed = True
                        continue
        return changed

    def is_solved(self):
        """ Returns whether or not the board has all cells filled. """
        for vertex in self.graph:
            if vertex.number == 0:
                return False
        return True

    def is_legal_board(self):
        """ Returns whether or not the board is in a legal state by the sudoku rules. """
        for row in self.board:
            for vertex1 in row:
                if vertex1.number == 0 and len(vertex1.number_options) < 1:
                    return False
                for vertex2 in self.graph:
                    if vertex2.number != 0:
                        if vertex2 in vertex1.neighbors and vertex1.number == vertex2.number:
                            return False
        return True

    def pprint(self):
        """ Pretty-prints the board. """
        for row in self.board:
            for cell in row:
                print(cell, end=' ')
            print()
        print()

    def solve(self, visual=False):
        """
        Solves a sudoku board by the folowing algorithm until the board is solved:

        1) While sole or unique candidates exist, fill them in.
        2) If in an illegal state, load last legal state* until in a legal state**.
        3) If no more sole or unique candidates, numerate one and see where it goes.

        *This will only happen if the numeration in step 3 was wrong, or if the
         input board was unsolveable.

        **If the only choice of number in a cell turned out to be illegal, this is
         caused by another bad choice previous in the game chain. Therfore, it
         is necessary to be able to load multiple states back.

        :param visual: Prints the board at each iteration if True. Should only be
         used for debugging or small 4*4 boards.
         :type visual: bool
        :return: Returns whether or not a legal solution was found.
        :rtype: bool
        """
        while not self.is_solved():
            self.update_possible_numbers()
            if visual:
                self.pprint()

            found_sole, found_unique = True, True
            while found_sole or found_unique:
                found_sole = self.fill_in_sole_candidates()
                self.update_possible_numbers()
                found_unique = self.fill_in_unique_candidates()
                self.update_possible_numbers()

            while not self.is_legal_board():
                self.load_previous_legal_state()
                self.update_possible_numbers()

            if not self.is_solved():
                self.numerate_least_known_vertex()
                self.update_possible_numbers()

        return self.is_legal_board()


if __name__ == '__main__':
    # Only executed when this module is run directly
    # The following is an example of how to use the module

    import json

    current_board = None

    with open('sudoku_boards.json') as board_file:
        boards = json.load(board_file)
        current_board = boards['sudoku_very_hard']

    solver = Sudoku_solver(current_board, dim=3)
    solver.solve()
    solver.pprint()

    # TIME: sudoku_extreme -> 1 min 37 sec, others -> ~instant
