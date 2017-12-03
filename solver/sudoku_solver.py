""" Sudoku solver that uses graph coloring to solve boards. """
__author__ = 'Claus Martinsen'


class Vertex:
    """ A vertex in a graph, with atributes to be used for sudoku solving. """

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
        """ Adds a number to the list of illegal numbers. Returns wether the number was there from before or not. """
        if number in self.number_options:
            self.number_options.remove(number)
        if number not in self.illegal_numbers:
            self.illegal_numbers.append(number)
            return True
        return False

    def rank(self):
        return len(self.neighbors)

    def __str__(self):
        return 'Vertex: ' + str(self.number)

    def __repr__(self):
        return '<Vertex: R=' + str(self.rank()) + ', C=' + str(self.number) + ', XY=' + str(self.coord) + '>'


class Graph:
    """ A graph containing vertecies. To be used for sudoku solving. """

    def __init__(self, vertices=list()):
        self.vertices = vertices

    def add(self, vertex):
        self.vertices.append(vertex)

    @staticmethod
    def connect(vertex1, vertex2):
        vertex1.add_neighbor(vertex2)

    def edge_count(self):
        i = 0
        for vertex in self:
            i += vertex.rank()
        i //= 2  # Each edge gets counted exactly twice
        return i

    def __add__(self, other):
        return self.vertices + other.vertices

    def __iadd__(self, other):
        self.vertices += other.vertices

    def __len__(self):
        return len(self.vertices)

    def __contains__(self, vertex):
        return vertex in self.vertices

    def __getitem__(self, index):
        return self.vertices[index]

    def __setitem__(self, index, vertex):
        self.vertices[index] = vertex

    def __iter__(self):
        return self.vertices.__iter__()

    def __str__(self):
        return str(self.vertices)

    def __repr__(self):
        return repr(self.vertices)


class Sudoku_solver:
    def __init__(self, sudoku_board, dim=3):
        """ Initializes a new sudoku solver based on the board and dimentions given. """
        self.board = sudoku_board
        self.graph = Graph()
        self.dim = dim
        self.memory = []
        self._setup()  # Sets up the sudoku board and graph

    def _setup(self):
        """ Sets up the internal graph structure based on the sudoku board. """
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

    def save_legal_state(self, uncertian_vertex, uncertain_number):
        """
        Saves the board numbers and the illegal numbers for all cells on the
        board. Also remembers the cell wich a uncertain number is placed, so
        that the uncertian number is remembered.
        """
        state = [[0 for _ in range(self.dim ** 2)] for _ in range(self.dim ** 2)]
        illegal_numbers = [[[] for _ in range(self.dim ** 2)] for _ in range(self.dim ** 2)]
        for i, row in enumerate(self.board):
            for j, vertex in enumerate(row):
                state[i][j] = vertex.number
                illegal_numbers[i][j] = vertex.illegal_numbers.copy()

        self.memory.append((state, illegal_numbers, uncertian_vertex, uncertain_number))

    def load_previous_legal_state(self):
        """
        Updates the board numbers and the illegal numbers for all cells on the
        board according to the last saved state. The wrong guess made when the
        state was saved is added to the cells illegal numbers.
        """
        if len(self.memory) < 1:
            raise IndexError('No previous state: len(self.memory < 1).')
        state, illegal_numbers, vertex, illegal_number = self.memory.pop()
        for i, row in enumerate(state):
            for j, number in enumerate(row):
                self.board[i][j].number = number
                self.board[i][j].illegal_numbers = illegal_numbers[i][j]

        vertex.add_illegal_number(illegal_number)

    def update_possible_numbers(self):
        """ Goes through all cells, updating each cells possible numbers. """
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
        if len(lkv.number_options) == 0:
            return

        i = min(lkv.number_options)
        self.save_legal_state(lkv, i)
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

    """
    def intersection_removal(self):
        for b_y in range(0, self.dim ** 2, 3):
            for b_x in range(0, self.dim ** 2, 3):
                pos_pointing_pair = []
                for n in range(1, self.dim + 1):
                    
                for y in range(self.dim):
                    for p in self.board[b_y + y][b_x]
                for x in range(self.dim):"""

    def x_wing(self):
        num_pairs = [[] for _ in range(self.dim ** 2)]
        for y, row in enumerate(self.board):
            occurences = [0] * (self.dim ** 2)
            for cell in row:
                for pos in cell.number_options:
                    occurences[pos - 1] += 1
            for num, occ in enumerate(occurences):
                if occ == 2:
                    pair = [y]
                    for x, cell in enumerate(row):
                        if num + 1 in cell.number_options:
                            pair.append(x)
                    num_pairs[num].append(pair)

        x_winged_cols = []
        for num, pairs in enumerate(num_pairs):
            n = len(pairs)
            if n > 1:
                for i in range(n):
                    for j in range(n):
                        if i != j:
                            if pairs[i][1] == pairs[j][1] and pairs[i][2] == pairs[j][2]:
                                x_winged_cols.append((num, pairs[i][1], pairs[i][0], pairs[j][0]))
        change = False
        for x_wing in x_winged_cols:
            for r in range(self.dim ** 2):
                if r != x_wing[2] and r != x_wing[3]:
                    change = change or self.board[r][x_wing[1]].add_illegal_number(x_wing[0])

        return change

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
                if vertex1.number == 0 and len(vertex1.number_options) == 0:
                    return False
                for vertex2 in vertex1.neighbors:
                    if vertex2.number != 0 and vertex1.number == vertex2.number:
                        return False
        return True

    def pprint(self):
        """ Pretty-prints the board. """
        for row in self.board:
            for cell in row:
                print(cell.number, end=' ')
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
            cont_1, cont_2 = True, True
            while cont_1 or cont_2:
                cont_1 = self.fill_in_sole_candidates()
                self.update_possible_numbers()
                cont_2 = self.fill_in_unique_candidates()
                self.update_possible_numbers()
                # cont_3 = self.x_wing()
                # self.update_possible_numbers()

            while not self.is_legal_board():
                self.load_previous_legal_state()
                self.update_possible_numbers()

            self.numerate_least_known_vertex()

        return self.is_legal_board()

    def __repr__(self):
        return '<Solver: Dim=' + str(self.dim) + ', Solved=' + str(self.is_solved()) + '>'


if __name__ == '__main__':
    # Only executed when this module is run directly
    # The following is an example of how to use the module

    import json

    current_board = None

    with open('sudoku_boards.json') as board_file:
        boards = json.load(board_file)
        current_board = boards['sudoku_extreme']

    solver = Sudoku_solver(current_board, dim=3)
    t = solver.solve()
    print(t)
    solver.pprint()
