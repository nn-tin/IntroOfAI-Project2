# helper_02.py
# Xây dựng CNF từ board Hashiwokakero
# Giả sử dùng pysat để encode CNF
# Cần define biến logic, ràng buộc theo đề bài

from pysat.formula import CNF
from pysat.card import CardEnc

def var_bridge(i1, j1, i2, j2, count):
    """
    Đánh số biến đại diện cho việc có 'count' cầu nối giữa đảo (i1,j1) và (i2,j2).
    count = 1 hoặc 2 (vì tối đa 2 cầu nối)
    Quy ước số biến cần nhất quán toàn bộ chương trình.
    """
    # Mã hóa biến: ví dụ một hàm băm hoặc đánh số tuần tự
    # Ở đây ví dụ đơn giản: biến = (i1 * 1000000 + j1 * 10000 + i2 * 100 + j2) * 10 + count
    # Giả sử board max 100x100
    return (i1 * 1000000 + j1 * 10000 + i2 * 100 + j2) * 10 + count


def generate_cnf(board):
    """
    Tạo CNF ràng buộc cho bài toán từ board.
    Ràng buộc chính:
    - Mỗi cặp đảo có tối đa 2 cầu
    - Tổng cầu nối từ mỗi đảo bằng số trên đảo
    - Cầu không chồng lên nhau, đi thẳng theo hàng hoặc cột
    - Cầu không được đi qua đảo khác
    - Kết nối thành 1 tập hợp liên thông (ràng buộc này phức tạp, có thể implement thêm)
    """
    cnf = CNF()
    islands = []
    n = len(board)
    m = len(board[0]) if n > 0 else 0

    # Tìm các đảo
    for i in range(n):
        for j in range(m):
            if board[i][j] != 0:
                islands.append((i, j, board[i][j]))

    # Bước 1: Tạo biến cho các cầu nối có thể có giữa các đảo thẳng hàng ngang hoặc dọc
    # Lấy từng cặp đảo thẳng hàng ngang hoặc dọc, tạo biến
    edges = []  # list biến các cầu
    for idx1, (x1, y1, val1) in enumerate(islands):
        for idx2 in range(idx1 + 1, len(islands)):
            x2, y2, val2 = islands[idx2]
            # Kiểm tra cùng hàng hoặc cùng cột
            if x1 == x2:
                # cùng hàng, cầu nối theo cột
                # Kiểm tra khoảng trống giữa 2 đảo
                blocked = False
                for y in range(min(y1, y2)+1, max(y1, y2)):
                    if board[x1][y] != 0:
                        blocked = True
                        break
                if blocked:
                    continue
                # Tạo biến bridge 1 và 2
                v1 = var_bridge(x1, y1, x2, y2, 1)
                v2 = var_bridge(x1, y1, x2, y2, 2)
                edges.append(((x1, y1, x2, y2), (v1, v2)))

            elif y1 == y2:
                # cùng cột, cầu nối theo hàng
                blocked = False
                for x in range(min(x1, x2)+1, max(x1, x2)):
                    if board[x][y1] != 0:
                        blocked = True
                        break
                if blocked:
                    continue
                v1 = var_bridge(x1, y1, x2, y2, 1)
                v2 = var_bridge(x1, y1, x2, y2, 2)
                edges.append(((x1, y1, x2, y2), (v1, v2)))

    # Bước 2: Ràng buộc mỗi cặp cầu không vượt quá 2
    for edge, (v1, v2) in edges:
        # v1 và v2 không thể đồng thời đúng nếu muốn giới hạn ở max 2 (đã đúng rồi)
        # Thêm ràng buộc không có cầu hơn 2? Tối đa 2 -> đã thể hiện bằng biến
        # Ràng buộc logic: biến v1 và v2 đại diện số cầu 1 hoặc 2
        # Nếu dùng biến True/False cho "có cầu 1" và "có cầu 2", 
        # thêm ràng buộc: Nếu có 2 cầu thì phải có cầu 1 cũng đúng? Có thể xem như thế này:
        # Nhưng đơn giản có thể không cần ràng buộc thêm ở đây.
        pass

    # Bước 3: Ràng buộc tổng số cầu nối tại mỗi đảo bằng số trên đảo
    # Tổng các cầu đi ra đảo = số ghi trên đảo
    # Tính tổng cầu nối của mỗi đảo qua các edges chứa đảo đó

    for i_x, i_y, val in islands:
        vars_for_island = []
        for edge, (v1, v2) in edges:
            x1, y1, x2, y2 = edge
            if (i_x, i_y) == (x1, y1) or (i_x, i_y) == (x2, y2):
                # 1 cầu = 1*var(v1) + 2*var(v2)
                # Biến v1, v2 đều là biến boolean (True/False)
                # Ta cần biểu diễn tổng số cầu (từ biến boolean) = val
                # Tuy nhiên pysat không hỗ trợ trực tiếp tổng trọng số
                # Giải pháp: dùng các biến phụ hoặc dùng ràng buộc bất kỳ
                # Ở đây tạm dùng ràng buộc: sum(v1 * 1 + v2 * 2) = val
                # Cách làm có thể dùng ràng buộc ràng buộc đa ngôi (cardinality)
                vars_for_island.append((v1, 1))
                vars_for_island.append((v2, 2))

        # TODO: biểu diễn ràng buộc tổng này dưới dạng CNF
        # Giải pháp: có thể dùng thư viện ràng buộc trọng số hoặc chuyển sang CNF phức tạp
        # Ở đây để demo tạm không hiện thực chi tiết

    # Bước 4: Ràng buộc cầu không được giao nhau
    # Hai cầu không thể đi chồng lên nhau nếu cắt nhau theo chiều ngang/dọc
    # Kiểm tra các cầu nối giao nhau và thêm ràng buộc phủ định 2 biến tương ứng
    # TODO: hiện thực chi tiết

    # Bước 5: Ràng buộc liên thông (cầu nối tạo thành một thành phần liên thông)
    # Phức tạp, có thể dùng thuật toán DFS trên graph cầu nối kết quả hoặc bổ sung ràng buộc đặc biệt
    # Thường dùng thuật toán sau khi giải CNF kiểm tra, hoặc thêm ràng buộc đặc biệt
    # TODO: bỏ qua hoặc implement nâng cao

    return cnf, edges
