===========================================
README - Hướng dẫn chạy chương trình Hashiwokakero Solver
===========================================

1. Giới thiệu
-------------
Chương trình này giải bài toán Hashiwokakero bằng nhiều thuật toán khác nhau:
- SAT-based solvers: PySAT, A* SAT, Backtracking SAT, Brute-force SAT
- Graph-based solvers: A* Graph, Backtracking Graph

Chương trình đo thời gian, số node mở rộng, kiểm tra kết nối, xuất kết quả ra file và lưu kết quả tổng hợp vào file CSV.

2. Cấu trúc thư mục
-------------------
- Inputs/: chứa các file input (ví dụ: input-01.txt, input-02.txt, ...)
- Outputs/: chứa các file output kết quả (ví dụ: output-01-pysat.txt, ...)
- Results/: chứa file tổng hợp experiment_results.csv
- visualization.ipynb: Notebook Python dùng để vẽ biểu đồ so sánh thời gian chạy các thuật toán
- Các file .py gồm main.py, helper_01.py, helper_02.py, solver_*.py

3. Yêu cầu hệ thống
------------------
- Python 3.x
- Các thư viện cần cài đặt:
  pip install python-sat numpy matplotlib pandas jupyter

4. Cách chạy
------------
- Chạy tất cả file input mặc định (input-01.txt đến input-10.txt):
    python main.py
  hoặc
    python main.py all

- Chạy một file input cụ thể, ví dụ input-05.txt:
    python main.py input-05.txt

- Chạy nhiều file cùng lúc, ví dụ input-01.txt và input-03.txt:
    python main.py input-01.txt input-03.txt

5. Kết quả đầu ra
-----------------
- File output cho từng solver nằm trong thư mục Outputs/, ví dụ:
  output-05-pysat.txt, output-05-astar_graph.txt, output-05-backtracking.txt, ...
- File tổng hợp kết quả experiment_results.csv nằm trong thư mục Results/

6. Vẽ biểu đồ so sánh thời gian chạy (Visualization)
-----------------------------------------------------
- Mở file `visualization.ipynb` bằng Jupyter Notebook hoặc JupyterLab:
    jupyter notebook visualization.ipynb
- Notebook này dùng file `Results/experiment_results.csv` làm dữ liệu đầu vào để vẽ biểu đồ so sánh thời gian chạy các thuật toán trên từng file input.
- Chạy từng cell trong notebook để hiển thị biểu đồ.

7. Thông tin thêm
-----------------
- Thời gian timeout cho từng solver được cấu hình trong main.py
- Có thể chỉnh sửa solver chạy trong hàm experiment_on_file()

8. Liên hệ
----------
Nếu có thắc mắc hoặc lỗi khi chạy, vui lòng liên hệ người phát triển hoặc xem mã nguồn để biết thêm chi tiết.

===========================================
Chúc bạn sử dụng chương trình thành công!
===========================================
