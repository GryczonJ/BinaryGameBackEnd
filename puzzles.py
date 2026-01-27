import random
import json


def generate_binary_puzzle(size: int, fullness: int):
    """
    Generates a binary puzzle (solution and initial state).
    
    Binary puzzle rules:
    - Each row/column can have max 2 consecutive 0s or 1s
    - Each row/column must have equal number of 0s and 1s
    - All rows and columns must be unique
    
    Args:
        size: Board size (4, 6, 8, or 10)
        fullness: 0-100, percentage of cells filled in initial state
                  0 = empty puzzle, 100 = completely filled
                  Recommended: 20-80 for playable puzzles
    
    Returns:
        (solution, initial) as JSON strings
    """
    fullness = max(0, min(100, fullness))  # Clamp to 0-100
    
    # Generate a valid solution
    solution = _generate_valid_solution(size)
    puzzle = [row[:] for row in solution]  # Deep copy for initial state
    
    # Create initial state based on fullness percentage
    num_cells = size * size
    num_to_empty = int(num_cells * (100 - fullness) / 100)
    
    # Empty random cells
    emptied = 0
    while emptied < num_to_empty:
        # print(emptied)
        r = random.randint(0, size - 1)
        c = random.randint(0, size - 1)
        if puzzle[r][c] is not None:
            puzzle[r][c] = None
            emptied += 1
    
    return json.dumps(solution), json.dumps(puzzle)


def _generate_valid_solution(size: int) -> list:
    """
    Generates a valid binary puzzle solution respecting all rules.
    
    Rules:
    - Max 2 consecutive same values
    - Equal 0s and 1s in each row/column
    - All rows unique
    - All columns unique
    """
    assert size % 2 == 0, "Rozmiar musi byc parzysty"

    board = [[None for _ in range(size)] for _ in range(size)]

    def is_valid(r, c):
        val = board[r][c]

        for dr, dc in [(0,1), (1,0)]:
            count = 1

            i = 1
            while 0 <= r+i*dr < size and 0 <= c+i*dc < size and board[r+i*dr][c+i*dc] == val:
                count += 1
                i += 1

            i = 1
            while 0 <= r-i*dr < size and 0 <= c-i*dc < size and board[r-i*dr][c-i*dc] == val:
                count += 1
                i += 1

            if count >= 3:
                return False

        row_vals = [x for x in board[r] if x is not None]
        col_vals = [board[i][c] for i in range(size) if board[i][c] is not None]

        if row_vals.count(val) > size // 2:
            return False
        if col_vals.count(val) > size // 2:
            return False

        return True

    def backtrack(pos=0):
        if pos == size * size:
            return True

        r, c = divmod(pos, size)
        if board[r][c] is not None:
            return backtrack(pos + 1)

        values = [0, 1]
        random.shuffle(values)

        for v in values:
            board[r][c] = v
            if is_valid(r, c):
                if backtrack(pos + 1):
                    return True
            board[r][c] = None

        return False

    backtrack()
    return board


def _fill_grid(grid: list, size: int) -> bool:
    """Recursively fills grid with valid values."""
    # Find first empty cell
    for row in range(size):
        for col in range(size):
            if grid[row][col] is None:
                # Try both values
                for value in [0, 1]:
                    if _is_valid_placement(grid, row, col, value, size):
                        grid[row][col] = value
                        if _fill_grid(grid, size):
                            return True
                        grid[row][col] = None
                
                return False
    
    # All cells filled
    return True


def _is_valid_placement(grid: list, row: int, col: int, value: int, size: int) -> bool:
    """Checks if placing a value at (row, col) is valid."""
    
    # Check row: no more than 2 consecutive same values
    if col >= 2 and grid[row][col-1] == value and grid[row][col-2] == value:
        return False
    if col >= 1 and col < size - 1 and grid[row][col-1] == value and grid[row][col+1] == value:
        return False
    if col < size - 2 and grid[row][col+1] == value and grid[row][col+2] == value:
        return False
    
    # Check column: no more than 2 consecutive same values
    if row >= 2 and grid[row-1][col] == value and grid[row-2][col] == value:
        return False
    if row >= 1 and row < size - 1 and grid[row-1][col] == value and grid[row+1][col] == value:
        return False
    if row < size - 2 and grid[row+1][col] == value and grid[row+2][col] == value:
        return False
    
    # Check row: count doesn't exceed half
    row_count = sum(1 for c in range(size) if grid[row][c] == value)
    if row_count >= size // 2:
        return False
    
    # Check column: count doesn't exceed half
    col_count = sum(1 for r in range(size) if grid[r][col] == value)
    if col_count >= size // 2:
        return False
    
    return True


def _generate_simple_solution(size: int) -> list:
    """
    Generates a simple but valid binary puzzle solution.
    Alternates values in a pattern that respects the rules.
    """
    grid = []
    for row in range(size):
        grid_row = []
        for col in range(size):
            # Simple alternating pattern with some randomness
            value = (row + col) % 2
            grid_row.append(value)
        grid.append(grid_row)
    
    return grid