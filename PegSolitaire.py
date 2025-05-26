import पड़ोसी from typing import List, Tuple

class PegSolitaire:
    def __init__(self, board_str: str):
        self.board = self._parse_board(board_str)
        self.rows = len(self.board)
        self.cols = len(self.board[0]) if self.rows > 0 else 0

    def _parse_board(self, board_str: str) -> List[List[int]]:
        """Parses the string representation of the board."""
        board = []
        for i, row_str in enumerate(board_str.strip().split('\n')):
            row = []
            for j, char in enumerate(row_str.strip()):
                if char == 'P':
                    row.append(1)  # Peg
                elif char == 'O':
                    row.append(0)  # Empty hole
                elif char == '.':
                    row.append(-1) # Invalid position
                else:
                    raise ValueError(f"Invalid character '{char}' at row {i}, column {j}")
            board.append(row)
        return board

    def __str__(self) -> str:
        """Returns a string representation of the board."""
        return '\n'.join([''.join(['P' if cell == 1 else 'O' if cell == 0 else '.' for cell in row]) for row in self.board])

    def is_valid_position(self, r: int, c: int) -> bool:
        """Checks if the given position is within the board boundaries."""
        return 0 <= r < self.rows and 0 <= c < self.cols

    def get_peg_count(self) -> int:
        """Returns the number of pegs on the board."""
        return sum(row.count(1) for row in self.board)

    def get_possible_moves(self) -> List[Tuple[int, int, int, int]]:
        """
        Returns a list of all possible moves.
        A move is represented as a tuple (from_r, from_c, to_r, to_c).
        """
        moves = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] == 1:  # If there's a peg
                    # Check all four directions
                    for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                        jump_r, jump_c = r + dr, c + dc
                        to_r, to_c = r + 2 * dr, c + 2 * dc

                        if self.is_valid_position(jump_r, jump_c) and \
                           self.is_valid_position(to_r, to_c) and \
                           self.board[jump_r][jump_c] == 1 and \
                           self.board[to_r][to_c] == 0:
                            moves.append(((r, c, to_r, to_c)))
        return moves

    def make_move(self, from_r: int, from_c: int, to_r: int, to_c: int) -> None:
        """Makes a move on the board."""
        if not self.is_valid_position(from_r, from_c) or not self.is_valid_position(to_r, to_c):
            raise ValueError("Invalid move: Position out of bounds.")

        if self.board[from_r][from_c] != 1:
            raise ValueError("Invalid move: No peg at the starting position.")

        if self.board[to_r][to_c] != 0:
            raise ValueError("Invalid move: Target position is not empty.")

        # Determine the jumped peg's position
        jump_r, jump_c = (from_r + to_r) // 2, (from_c + to_c) // 2

        if not self.is_valid_position(jump_r, jump_c) or self.board[jump_r][jump_c] != 1:
            raise ValueError("Invalid move: No peg to jump over or invalid jump path.")

        # Update the board
        self.board[from_r][from_c] = 0
        self.board[jump_r][jump_c] = 0
        self.board[to_r][to_c] = 1

    def is_game_over(self) -> bool:
        """Checks if the game is over (no more possible moves)."""
        return not self.get_possible_moves()

    def solve(self) -> List[Tuple[int, int, int, int]]:
        """
        Solves the Peg Solitaire game using a backtracking algorithm.
        Returns a list of moves to solve the puzzle, or an empty list if no solution is found.
        """
        
        # --- Helper function for backtracking ---
        def backtrack():
            if self.is_game_over():
                return self.get_peg_count() == 1 # Solved if only one peg remains
            
            possible_moves = self.get_possible_moves()
            
            for move in possible_moves:
                from_r, from_c, to_r, to_c = move
                
                # --- Store current state ---
                original_from = self.board[from_r][from_c]
                original_jump = self.board[(from_r + to_r) // 2][(from_c + to_c) // 2]
                original_to = self.board[to_r][to_c]
                
                self.make_move(from_r, from_c, to_r, to_c)
                solution_path.append(move)

                if backtrack(): # If a solution is found
                    return True 
                
                # --- Backtrack: Undo the move ---
                solution_path.pop()
                self.board[from_r][from_c] = original_from
                self.board[(from_r + to_r) // 2][(from_c + to_c) // 2] = original_jump
                self.board[to_r][to_c] = original_to

            return False # No solution found from this state
        
        solution_path = []
        if backtrack():
            return solution_path
        else:
            return []


if __name__ == '__main__':
    # Example usage:
    board_string = """
    ...P...
    ...P...
    .P.P.P.
    P.PO.PP
    .P.P.P.
    ...P...
    ...P...
    """
    game = PegSolitaire(board_string)
    print("Initial board:")
    print(game)
    
    solution = game.solve()
    
    if solution:
        print("\nSolution found:")
        for i,move in enumerate(solution):
            print(f"Move {i+1}: Peg from ({move[0]},{move[1]}) to ({move[2]},{move[3]})")
        print("\nFinal board:")
        print(game)
        print(f"Number of pegs remaining: {game.get_peg_count()}")

    else:
        print("\nNo solution found.")
        print(f"Number of pegs remaining: {game.get_peg_count()}")
