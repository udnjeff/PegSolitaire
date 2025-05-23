import copy
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.font import Font

class PegSolitaireGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("孔明棋")
        
        # 遊戲狀態
        self.board = [
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 0, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0]
        ]
        self.history = []
        self.redo_stack = []
        self.move_history = []  # 記錄移動步驟
        
        # 選擇狀態
        self.selected_peg = None
        self.peg_size = 40
        self.board_padding = 20
        
        # 創建主框架
        main_frame = tk.Frame(self.window)
        main_frame.pack(padx=10, pady=10)
        
        # 創建畫布
        canvas_size = self.peg_size * 7 + self.board_padding * 2
        self.canvas = tk.Canvas(main_frame, width=canvas_size, height=canvas_size, bg='#F0F0F0')
        self.canvas.pack(pady=5)
        
        # 創建按鈕框架
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=5)
        
        # 創建按鈕（使用Unicode符號）
        undo_all_button = tk.Button(button_frame, text="⏪", command=self.undo_all, width=3)
        undo_all_button.pack(side=tk.LEFT, padx=2)
        
        undo_button = tk.Button(button_frame, text="◀", command=self.undo, width=3)
        undo_button.pack(side=tk.LEFT, padx=2)
        
        redo_button = tk.Button(button_frame, text="▶", command=self.redo, width=3)
        redo_button.pack(side=tk.LEFT, padx=2)
        
        redo_all_button = tk.Button(button_frame, text="⏩", command=self.redo_all, width=3)
        redo_all_button.pack(side=tk.LEFT, padx=2)
        
        new_game_button = tk.Button(button_frame, text="新遊戲", command=self.new_game)
        new_game_button.pack(side=tk.LEFT, padx=5)
        
        # 創建移動記錄顯示區域
        history_frame = tk.Frame(main_frame)
        history_frame.pack(pady=5, fill=tk.X)
        
        history_label = tk.Label(history_frame, text="移動記錄：")
        history_label.pack(anchor=tk.W)
        
        self.history_text = tk.Text(history_frame, height=10, width=40)
        self.history_text.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        scrollbar = tk.Scrollbar(history_frame, command=self.history_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_text.config(yscrollcommand=scrollbar.set)
        
        # 綁定滑鼠事件
        self.canvas.bind('<Button-1>', self.on_click)
        
        # 繪製初始棋盤
        self.draw_board()
        
    def draw_board(self):
        """繪製棋盤和棋子"""
        self.canvas.delete("all")
        
        # 繪製棋盤背景
        for i in range(7):
            for j in range(7):
                # 跳過四個角落
                if (i < 2 and j < 2) or (i < 2 and j > 4) or (i > 4 and j < 2) or (i > 4 and j > 4):
                    continue
                    
                x = j * self.peg_size + self.board_padding
                y = i * self.peg_size + self.board_padding
                self.canvas.create_rectangle(x, y, x + self.peg_size, y + self.peg_size,
                                          fill='#E0E0E0', outline='#A0A0A0')
        
        # 繪製列標籤 (A-G)
        for j in range(7):
            x = j * self.peg_size + self.board_padding + self.peg_size // 2
            y = self.board_padding - 10
            self.canvas.create_text(x, y, text=chr(65 + j), font=("Arial", 10, "bold"))
        
        # 繪製行標籤 (1-7)
        for i in range(7):
            x = self.board_padding - 10
            y = i * self.peg_size + self.board_padding + self.peg_size // 2
            self.canvas.create_text(x, y, text=str(i + 1), font=("Arial", 10, "bold"))
        
        # 繪製棋子
        for i in range(7):
            for j in range(7):
                if self.board[i][j] == 1:
                    x = j * self.peg_size + self.board_padding + self.peg_size // 2
                    y = i * self.peg_size + self.board_padding + self.peg_size // 2
                    color = '#FF0000' if (i, j) == self.selected_peg else '#000000'
                    self.canvas.create_oval(x - 15, y - 15, x + 15, y + 15,
                                         fill=color, outline='#404040')
    
    def get_cell_from_pos(self, x, y):
        """將滑鼠座標轉換為棋盤座標"""
        col = (x - self.board_padding) // self.peg_size
        row = (y - self.board_padding) // self.peg_size
        if 0 <= row < 7 and 0 <= col < 7:
            # 檢查是否在有效區域
            if (row < 2 and col < 2) or (row < 2 and col > 4) or (row > 4 and col < 2) or (row > 4 and col > 4):
                return None
            return row, col
        return None
    
    def format_move(self, from_row, from_col, to_row, to_col):
        """格式化移動記錄"""
        from_col_char = chr(65 + from_col)
        to_col_char = chr(65 + to_col)
        return f"{from_col_char}{from_row + 1} over {to_col_char}{to_row + 1}"
    
    def update_history_display(self):
        """更新移動記錄顯示"""
        self.history_text.delete(1.0, tk.END)
        for i, move in enumerate(self.move_history, 1):
            self.history_text.insert(tk.END, f"{i}. {move}\n")
    
    def is_valid_move(self, from_row, from_col, to_row, to_col):
        """檢查移動是否合法"""
        if not (0 <= from_row < 7 and 0 <= from_col < 7 and 0 <= to_row < 7 and 0 <= to_col < 7):
            return False
        
        if self.board[from_row][from_col] != 1:
            return False
        
        if self.board[to_row][to_col] != 0:
            return False
        
        if abs(from_row - to_row) == 2 and from_col == to_col:
            mid_row = (from_row + to_row) // 2
            if self.board[mid_row][from_col] != 1:
                return False
            return True
        elif abs(from_col - to_col) == 2 and from_row == to_row:
            mid_col = (from_col + to_col) // 2
            if self.board[from_row][mid_col] != 1:
                return False
            return True
        
        return False
    
    def make_move(self, from_row, from_col, to_row, to_col):
        """執行移動"""
        if not self.is_valid_move(from_row, from_col, to_row, to_col):
            return False
        
        # 保存當前狀態
        self.history.append(copy.deepcopy(self.board))
        self.redo_stack.clear()
        
        # 記錄移動
        move = self.format_move(from_row, from_col, to_row, to_col)
        self.move_history.append(move)
        
        # 執行移動
        self.board[from_row][from_col] = 0
        self.board[to_row][to_col] = 1
        
        # 移除被跳過的棋子
        if from_row == to_row:
            mid_col = (from_col + to_col) // 2
            self.board[from_row][mid_col] = 0
        else:
            mid_row = (from_row + to_row) // 2
            self.board[mid_row][from_col] = 0
        
        # 更新移動記錄顯示
        self.update_history_display()
        return True
    
    def undo_all(self):
        """撤銷所有移動"""
        if not self.history:
            return
        
        # 保存當前狀態到重做堆疊
        self.redo_stack.append(copy.deepcopy(self.board))
        # 直接回到初始狀態
        self.board = self.history[0]
        # 清空歷史記錄
        self.history = []
        # 清空移動記錄
        self.move_history = []
        self.selected_peg = None
        self.update_history_display()
        self.draw_board()
    
    def redo_all(self):
        """重做所有移動"""
        if not self.redo_stack:
            return
        
        # 保存當前狀態到歷史記錄
        self.history.append(copy.deepcopy(self.board))
        # 直接回到最後一個狀態
        self.board = self.redo_stack[-1]
        # 清空重做堆疊
        self.redo_stack = []
        # 更新移動記錄
        self.move_history = []
        for i in range(len(self.history)):
            # 這裡需要重新計算每一步的移動
            if i < len(self.history) - 1:
                prev_board = self.history[i]
                curr_board = self.history[i + 1]
                # 找出移動的起點和終點
                for row in range(7):
                    for col in range(7):
                        if prev_board[row][col] == 1 and curr_board[row][col] == 0:
                            # 找到起點
                            for dr, dc in [(0, 2), (0, -2), (2, 0), (-2, 0)]:
                                new_row, new_col = row + dr, col + dc
                                if (0 <= new_row < 7 and 0 <= new_col < 7 and 
                                    curr_board[new_row][new_col] == 1):
                                    # 找到終點
                                    self.move_history.append(
                                        self.format_move(row, col, new_row, new_col)
                                    )
                                    break
        self.selected_peg = None
        self.update_history_display()
        self.draw_board()
    
    def undo(self):
        """撤銷上一步"""
        if not self.history:
            messagebox.showinfo("提示", "無法撤銷！")
            return
        
        # 保存當前狀態到重做堆疊
        self.redo_stack.append(copy.deepcopy(self.board))
        # 恢復上一步狀態
        self.board = self.history.pop()
        self.selected_peg = None
        if self.move_history:
            self.move_history.pop()
        self.update_history_display()
        self.draw_board()
    
    def redo(self):
        """重做上一步"""
        if not self.redo_stack:
            messagebox.showinfo("提示", "無法重做！")
            return
        
        # 保存當前狀態到歷史記錄
        self.history.append(copy.deepcopy(self.board))
        # 恢復下一步狀態
        self.board = self.redo_stack.pop()
        self.selected_peg = None
        # 重新計算移動記錄
        if len(self.history) > 1:
            prev_board = self.history[-2]
            curr_board = self.board
            # 找出移動的起點和終點
            for row in range(7):
                for col in range(7):
                    if prev_board[row][col] == 1 and curr_board[row][col] == 0:
                        # 找到起點
                        for dr, dc in [(0, 2), (0, -2), (2, 0), (-2, 0)]:
                            new_row, new_col = row + dr, col + dc
                            if (0 <= new_row < 7 and 0 <= new_col < 7 and 
                                curr_board[new_row][new_col] == 1):
                                # 找到終點
                                self.move_history.append(
                                    self.format_move(row, col, new_row, new_col)
                                )
                                break
        self.update_history_display()
        self.draw_board()
    
    def auto_redo(self, steps):
        """自動重做指定步數"""
        if not self.redo_stack:
            return
        
        for _ in range(steps):
            if not self.redo_stack:
                break
            self.redo()
            self.window.update()  # 更新視窗
            self.window.after(1000)  # 延遲100毫秒
    
    def auto_undo(self, steps):
        """自動撤銷指定步數"""
        if not self.history:
            return
        
        for _ in range(steps):
            if not self.history:
                break
            self.undo()
            self.window.update()  # 更新視窗
            self.window.after(100)  # 延遲100毫秒
    
    def new_game(self):
        """開始新遊戲"""
        self.board = [
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 0, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [0, 0, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0]
        ]
        self.history = []
        self.redo_stack = []
        self.move_history = []
        self.selected_peg = None
        self.update_history_display()
        self.draw_board()
    
    def show_winner_animation(self):
        """顯示勝利動畫"""
        # 創建一個新視窗
        winner_window = tk.Toplevel(self.window)
        winner_window.title("恭喜！")
        
        # 設置視窗大小和位置
        window_width = 400
        window_height = 200
        screen_width = winner_window.winfo_screenwidth()
        screen_height = winner_window.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        winner_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # 創建標籤
        label = tk.Label(winner_window, text="恭喜你贏了！", font=("Arial", 24, "bold"))
        label.pack(expand=True)
        
        # 3秒後自動關閉
        winner_window.after(3000, winner_window.destroy)
    
    def check_game_over(self):
        """檢查遊戲是否結束"""
        pegs = sum(row.count(1) for row in self.board)
        if pegs == 1:
            self.show_winner_animation()
            return
        
        # 檢查是否還有可能的移動
        for i in range(7):
            for j in range(7):
                if self.board[i][j] == 1:
                    directions = [(0, 2), (0, -2), (2, 0), (-2, 0)]
                    for di, dj in directions:
                        ni, nj = i + di, j + dj
                        if self.is_valid_move(i, j, ni, nj):
                            return
        
        messagebox.showinfo("遊戲結束", "沒有更多可能的移動了！")
    
    def on_click(self, event):
        """處理滑鼠點擊事件"""
        cell = self.get_cell_from_pos(event.x, event.y)
        if cell is None:
            return
        
        row, col = cell
        
        if self.selected_peg is None:
            # 選擇棋子
            if self.board[row][col] == 1:
                self.selected_peg = (row, col)
                self.draw_board()
        else:
            # 移動棋子
            from_row, from_col = self.selected_peg
            if self.make_move(from_row, from_col, row, col):
                self.selected_peg = None
                self.draw_board()
                self.check_game_over()
            else:
                # 如果移動無效，取消選擇
                self.selected_peg = None
                self.draw_board()
    
    def run(self):
        """運行遊戲"""
        self.window.mainloop()

if __name__ == "__main__":
    game = PegSolitaireGUI()
    game.run()
