# helper_01.py
# Xử lý đọc file input, biểu diễn board và một số hàm tiện ích

def read_input(filename):
    """
    Đọc file input Hashiwokakero, trả về matrix 2D kiểu int,
    với 0 là ô trống, số 1-8 là đảo
    """
    board = []
    with open(filename, 'r') as f:
        for line in f:
            if line.strip() == '':
                continue
            row = [int(x.strip()) for x in line.strip().split(',')]
            board.append(row)
    return board


def print_board(board):
    """
    In board ra màn hình, dùng để debug
    """
    for row in board:
        print(' '.join(str(x) for x in row))


def find_islands(board):
    """
    Tìm vị trí các đảo trên board, trả về list (x,y,value)
    """
    islands = []
    for i, row in enumerate(board):
        for j, val in enumerate(row):
            if val != 0:
                islands.append((i, j, val))
    return islands


if __name__ == "__main__":
    # test đọc input
    board = read_input('Inputs/input-01.txt')
    print_board(board)
    islands = find_islands(board)
    print("Islands:", islands)
