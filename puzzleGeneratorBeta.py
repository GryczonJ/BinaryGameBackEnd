import random

def generate_binary_puzzle(a):
    assert a % 2 == 0, "Rozmiar musi byc parzysty"

    board = [[None for _ in range(a)] for _ in range(a)]

    def is_valid(r, c):
        val = board[r][c]

        stage = 1
        for dr, dc in [(0,1), (1,0)]:

            print(stage)
            stage += 1

            for row in board:
                print(row)
            print("----")

            count = 1

            i = 1
            while 0 <= r+i*dr < a and 0 <= c+i*dc < a and board[r+i*dr][c+i*dc] == val:
                count += 1
                i += 1

            i = 1
            while 0 <= r-i*dr < a and 0 <= c-i*dc < a and board[r-i*dr][c-i*dc] == val:
                count += 1
                i += 1

            if count >= 3:
                return False

        row_vals = [x for x in board[r] if x is not None]
        col_vals = [board[i][c] for i in range(a) if board[i][c] is not None]

        if row_vals.count(val) > a // 2:
            return False
        if col_vals.count(val) > a // 2:
            return False

        return True

    def backtrack(pos=0):
        if pos == a * a:
            return True

        r, c = divmod(pos, a)
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


board = (generate_binary_puzzle(6))
for row in board:
    print(row)