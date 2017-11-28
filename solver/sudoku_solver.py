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


class Stack:
    def __init__(self):
        self.stack = []

    def push(self, element):
        self.stack.append(element)

    def pop(self):
        return self.stack.pop()

    def __str__(self):
        s = ''
        for item in self.stack:
            s += str(item) + '/'
        return s


class Sudoku_solver:
    def __init__(self, sudoku, dim=3):
        self.sudoku = sudoku
        self.graph = Graph()
        self.dim = dim
        self.memory = []

        k = dim ** 2
        for v_y in range(k):
            for v_x in range(k):
                n = sudoku[v_y][v_x]
                sudoku[v_y][v_x] = Vertex(x=v_x, y=v_y)
                if n != 0:
                    sudoku[v_y][v_x].number = n

        for v_y in range(k):
            for v_x in range(k):
                for x in range(k):
                    if x != v_x:
                        sudoku[v_y][v_x].add_neighbor(sudoku[v_y][x])
                for y in range(k):
                    if y != v_y:
                        sudoku[v_y][v_x].add_neighbor(sudoku[y][v_x])

                q_y, q_x = dim * (v_y // dim), dim * (v_x // dim)
                for y in range(dim):
                    for x in range(dim):
                        if q_y + y != v_y or q_x + x != v_x:
                            sudoku[v_y][v_x].add_neighbor(sudoku[q_y + y][q_x + x])

        for row in sudoku:
            for vertex in row:
                self.graph.add(vertex)

    def save_state(self, uncertian_vertex, uncertain_number):
        state = [[0 for _ in range(self.dim ** 2)] for _ in range(self.dim ** 2)]
        illegal_numbers = [[[] for _ in range(self.dim ** 2)] for _ in range(self.dim ** 2)]
        for i, row in enumerate(self.sudoku):
            for j, vertex in enumerate(row):
                state[i][j] = vertex.number
                illegal_numbers[i][j] = vertex.illegal_numbers.copy()

        self.memory.append((state, illegal_numbers, uncertian_vertex, uncertain_number))

    def load_state(self):
        state, illegal_numbers, vertex, illegal_number = self.memory.pop()
        for i, row in enumerate(state):
            for j, number in enumerate(row):
                self.sudoku[i][j].number = number
                self.sudoku[i][j].illegal_numbers = illegal_numbers[i][j]

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
        lkv = self.graph[0]
        for vertex in self.graph:
            if len(vertex.number_options) > len(lkv.number_options):
                lkv = vertex

        i = min(lkv.number_options)
        self.save_state(lkv, i)
        lkv.number = i

    def fill_in_simples(self):
        changed = False
        for vertex in self.graph:
            if len(vertex.number_options) == 1:
                vertex.number = vertex.number_options[0]
                changed = True
        return changed

    def fill_in_hidden_simples(self):
        changed = False
        for v_y, row in enumerate(self.sudoku):
            for v_x, vertex in enumerate(row):
                for number in vertex.number_options:

                    hidden_row, hidden_col, hidden_box = True, True, True
                    for x in range(self.dim ** 2):
                        if x != v_x:
                            if number in self.sudoku[v_y][x].number_options:
                                hidden_row = False
                                break
                    if hidden_row:
                        vertex.number = number
                        changed = True
                        continue

                    for y in range(self.dim ** 2):
                        if y != v_y:
                            if number in self.sudoku[y][v_x].number_options:
                                hidden_col = False
                                break
                    if hidden_col:
                        vertex.number = number
                        changed = True
                        continue

                    q_y, q_x = self.dim * (v_y // self.dim), self.dim * (v_x // self.dim)
                    for y in range(self.dim):
                        for x in range(self.dim):
                            if q_y + y != v_y or q_x + x != v_x:
                                if number in self.sudoku[q_y + y][q_x + x].number_options:
                                    hidden_box = False
                    if hidden_box:
                        vertex.number = number
                        changed = True
                        continue
        return changed

    def is_solved(self):
        for vertex in self.graph:
            if vertex.number == 0:
                return False
        return True

    def is_legal_board(self):
        for row in self.sudoku:
            for vertex1 in row:
                if vertex1.number == 0 and len(vertex1.number_options) < 1:
                    return False
                for vertex2 in self.graph:
                    if vertex2.number != 0:
                        if vertex2 in vertex1.neighbors and vertex1.number == vertex2.number:
                            return False
        return True

    def pprint(self):
        for row in self.sudoku:
            for cell in row:
                print(cell, end=' ')
            print()
        print()

    def sovle(self, visual=False):
        while not self.is_solved():
            self.update_possible_numbers()
            if visual:
                self.pprint()

            changed_simple, changed_hidden = True, True
            while changed_simple or changed_hidden:
                changed_simple = self.fill_in_simples()
                self.update_possible_numbers()
                changed_hidden = self.fill_in_hidden_simples()
                self.update_possible_numbers()

            while not self.is_legal_board():
                self.load_state()
                self.update_possible_numbers()

            if not self.is_solved():
                self.numerate_least_known_vertex()
                self.update_possible_numbers()

        return self.is_legal_board()


if __name__ == '__main__':
    sudoku_2d = [
        [0, 0, 0, 0],
        [0, 3, 0, 0],
        [1, 0, 2, 0],
        [0, 0, 0, 4]]

    sudoku_test = [
        [2, 9, 5, 7, 0, 0, 8, 6, 0],
        [0, 3, 1, 8, 6, 5, 0, 2, 0],
        [8, 0, 6, 0, 0, 0, 0, 0, 0],
        [0, 0, 7, 0, 5, 0, 0, 0, 6],
        [0, 0, 0, 3, 8, 7, 0, 0, 0],
        [5, 0, 0, 0, 1, 6, 7, 0, 0],
        [0, 0, 0, 5, 0, 0, 1, 0, 9],
        [0, 2, 0, 6, 0, 0, 3, 5, 0],
        [0, 5, 4, 0, 0, 8, 6, 7, 2]]

    sudoku_simple = [
        [8, 0, 9, 0, 0, 0, 7, 0, 2],
        [0, 7, 0, 0, 5, 0, 0, 1, 0],
        [1, 0, 0, 7, 0, 4, 0, 0, 9],
        [0, 0, 8, 1, 0, 0, 3, 0, 0],
        [0, 4, 0, 0, 6, 0, 0, 8, 0],
        [0, 0, 6, 3, 0, 0, 5, 0, 0],
        [4, 0, 0, 9, 0, 2, 0, 0, 6],
        [0, 9, 0, 0, 8, 0, 0, 7, 0],
        [7, 0, 2, 0, 0, 0, 4, 0, 8]]

    sudoku_easy = [
        [0, 0, 0, 3, 0, 4, 0, 0, 0],
        [0, 0, 0, 0, 2, 0, 0, 8, 0],
        [0, 0, 0, 1, 0, 0, 0, 6, 5],
        [0, 9, 0, 0, 0, 0, 5, 3, 7],
        [2, 5, 0, 0, 0, 3, 0, 0, 0],
        [0, 4, 0, 0, 0, 0, 0, 0, 1],
        [3, 0, 0, 0, 1, 0, 0, 7, 0],
        [0, 0, 0, 0, 0, 6, 0, 0, 0],
        [0, 0, 6, 8, 0, 5, 9, 0, 0]]

    sudoku_very_hard_1 = [
        [0, 0, 0, 9, 3, 0, 0, 5, 0],
        [0, 0, 0, 0, 0, 7, 0, 0, 3],
        [0, 2, 1, 0, 0, 0, 6, 0, 0],
        [2, 0, 0, 7, 8, 4, 0, 0, 0],
        [1, 9, 0, 0, 0, 0, 0, 0, 2],
        [0, 0, 0, 0, 0, 0, 7, 0, 0],
        [9, 0, 0, 0, 0, 0, 1, 7, 0],
        [7, 0, 0, 0, 0, 0, 0, 2, 8],
        [0, 0, 8, 1, 0, 0, 5, 0, 0]]

    S = Sudoku_solver(sudoku_very_hard_1, dim=3)
    S.sovle()
    S.pprint()
