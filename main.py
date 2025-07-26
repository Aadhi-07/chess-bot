import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import chess
import chess.engine
import os
import tkinter.ttk as ttk


class ChessApp:
    def __init__(self, master):
        self.master = master
        master.title("Chess")

        self.theme = "Classic Blue"
        self.theme_colors = {
            "Classic Blue": {
                "light": "#e0f0ff", "dark": "#4a90e2", "highlight": "#88c0ff",
                "button_bg": "#cce4ff", "hover": "#b3d1ff", "pressed": "#99bbff"
            },
            "Modern Dark": {
                "light": "#2e2e2e", "dark": "#1c1c1c", "highlight": "#3a3a3a",
                "button_bg": "#444", "hover": "#555", "pressed": "#333"
            }
        }

        self.board = chess.Board()
        self.engine_path = os.path.join(os.getcwd(), "stockfish.exe" if os.name == "nt" else "stockfish")
        self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)

        self.images = self.load_images()
        self.canvas = tk.Canvas(master, width=512, height=512)
        self.canvas.pack()

        self.theme_selector = ttk.Combobox(master, values=list(self.theme_colors.keys()), state="readonly")
        self.theme_selector.set(self.theme)
        self.theme_selector.pack(pady=5)
        self.theme_selector.bind("<<ComboboxSelected>>", self.change_theme)

        self.reset_button = self.create_animated_button(master, "New Game", self.reset_game)
        self.reset_button.pack(pady=5)

        self.undo_button = self.create_animated_button(master, "Undo Move", self.undo_move)
        self.undo_button.pack(pady=5)

        self.hint_button = self.create_animated_button(master, "Hint", self.show_hint)
        self.hint_button.pack(pady=5)

        self.canvas.bind("<Button-1>", self.on_piece_press)
        self.canvas.bind("<B1-Motion>", self.on_drag_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_piece_release)

        self.drag_data = {"start": None, "image": None, "id": None}
        self.highlight_squares = []
        self.last_move = None

        self.draw_board()

    def load_images(self):
        pieces = ["wp", "wn", "wb", "wr", "wq", "wk",
                  "bp", "bn", "bb", "br", "bq", "bk"]
        images = {}
        for piece in pieces:
            image = Image.open(f"images/{piece}.png").resize((64, 64), Image.Resampling.LANCZOS)
            images[piece] = ImageTk.PhotoImage(image)
        return images

    def draw_board(self):
        self.canvas.delete("all")
        theme = self.theme_colors[self.theme]
        colors = [theme["light"], theme["dark"]]

        for row in range(8):
            for col in range(8):
                color = colors[(row + col) % 2]
                x0, y0 = col * 64, (7 - row) * 64
                self.canvas.create_rectangle(x0, y0, x0 + 64, y0 + 64, fill=color, outline="")

        if self.last_move:
            for sq in [self.last_move.from_square, self.last_move.to_square]:
                col = chess.square_file(sq)
                row = 7 - chess.square_rank(sq)
                x0, y0 = col * 64, row * 64
                self.canvas.create_rectangle(x0, y0, x0 + 64, y0 + 64, fill=theme["highlight"])

        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                prefix = 'w' if piece.color == chess.WHITE else 'b'
                piece_code = prefix + piece.symbol().lower()
                col = chess.square_file(square)
                row = 7 - chess.square_rank(square)
                self.canvas.create_image(col * 64, row * 64, image=self.images[piece_code], anchor="nw")

        for sq in self.highlight_squares:
            col = chess.square_file(sq)
            row = 7 - chess.square_rank(sq)
            x, y = col * 64 + 32, row * 64 + 32
            self.canvas.create_oval(x - 10, y - 10, x + 10, y + 10, fill="#888", outline="")

    def on_piece_press(self, event):
        col = event.x // 64
        row = 7 - (event.y // 64)
        square = chess.square(col, row)
        piece = self.board.piece_at(square)

        if piece and piece.color == chess.WHITE:
            self.drag_data["start"] = square
            self.highlight_squares = [
                move.to_square for move in self.board.legal_moves if move.from_square == square
            ]
            prefix = 'w'
            piece_code = prefix + piece.symbol().lower()
            self.drag_data["image"] = self.images[piece_code]
            self.drag_data["id"] = self.canvas.create_image(event.x - 32, event.y - 32, image=self.drag_data["image"])
            self.draw_board()

    def on_drag_motion(self, event):
        if self.drag_data["id"]:
            self.canvas.coords(self.drag_data["id"], event.x - 32, event.y - 32)

    def on_piece_release(self, event):
        if self.drag_data["start"] is None:
            return

        col = event.x // 64
        row = 7 - (event.y // 64)
        target_square = chess.square(col, row)

        move = chess.Move(self.drag_data["start"], target_square)
        self.canvas.delete(self.drag_data.get("id"))
        self.drag_data = {"start": None, "image": None, "id": None}
        self.highlight_squares = []

        if move in self.board.legal_moves:
            self.animate_piece_move(move, is_engine=False)
        else:
            self.draw_board()

    def animate_piece_move(self, move, is_engine=False):
        from_sq = move.from_square
        to_sq = move.to_square
        piece = self.board.piece_at(from_sq)
        if not piece:
            return

        prefix = 'w' if piece.color == chess.WHITE else 'b'
        piece_img = self.images[prefix + piece.symbol().lower()]

        from_x = chess.square_file(from_sq) * 64
        from_y = (7 - chess.square_rank(from_sq)) * 64
        to_x = chess.square_file(to_sq) * 64
        to_y = (7 - chess.square_rank(to_sq)) * 64

        dx = (to_x - from_x) / 10
        dy = (to_y - from_y) / 10

        anim_piece = self.canvas.create_image(from_x, from_y, image=piece_img, anchor="nw")

        def step(i=0):
            if i < 10:
                self.canvas.move(anim_piece, dx, dy)
                self.master.after(20, step, i + 1)
            else:
                self.canvas.delete(anim_piece)
                self.board.push(move)
                self.last_move = move
                self.draw_board()
                if self.board.is_game_over():
                    self.show_result()
                elif not is_engine:
                    self.master.after(300, self.make_engine_move)

        step()

    def make_engine_move(self):
        if self.board.is_game_over():
            return
        result = self.engine.play(self.board, chess.engine.Limit(time=0.1))
        self.animate_piece_move(result.move, is_engine=True)

    def reset_game(self):
        self.board.reset()
        self.last_move = None
        self.highlight_squares = []
        self.drag_data = {"start": None, "image": None, "id": None}
        self.draw_board()

    def undo_move(self):
        if len(self.board.move_stack) >= 2:
            self.board.pop()
            self.board.pop()
            self.last_move = None
            self.draw_board()

    def show_hint(self):
        if self.board.turn == chess.WHITE and not self.board.is_game_over():
            hint_move = self.engine.play(self.board, chess.engine.Limit(time=0.1)).move
            self.highlight_squares = [hint_move.from_square, hint_move.to_square]
            self.draw_board()

    def show_result(self):
        result = self.board.result()
        if self.board.is_checkmate():
            msg = "Checkmate. " + ("You win!" if self.board.turn == chess.BLACK else "Stockfish wins!")
        elif self.board.is_stalemate():
            msg = "Stalemate."
        elif self.board.is_insufficient_material():
            msg = "Draw by insufficient material."
        else:
            msg = f"Game over. Result: {result}"
        messagebox.showinfo("Game Over", msg)

    def create_animated_button(self, parent, text, command):
        style_name = f"{text}.TButton"
        theme = self.theme_colors[self.theme]

        style = ttk.Style()
        style.configure(style_name,
                        font=("Segoe UI", 10, "bold"),
                        foreground="black",
                        background=theme["button_bg"],
                        padding=6,
                        relief="flat")
        style.map(style_name,
                  background=[("active", theme["hover"]), ("pressed", theme["pressed"])])

        btn = ttk.Button(parent, text=text, style=style_name, command=command)

        def on_enter(e):
            style.configure(style_name, background=theme["hover"])

        def on_leave(e):
            style.configure(style_name, background=theme["button_bg"])

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    def change_theme(self, event=None):
        self.theme = self.theme_selector.get()
        self.reset_buttons()
        self.draw_board()

    def reset_buttons(self):
        self.reset_button.destroy()
        self.undo_button.destroy()
        self.hint_button.destroy()

        self.reset_button = self.create_animated_button(self.master, "New Game", self.reset_game)
        self.reset_button.pack(pady=5)

        self.undo_button = self.create_animated_button(self.master, "Undo Move", self.undo_move)
        self.undo_button.pack(pady=5)

        self.hint_button = self.create_animated_button(self.master, "Hint", self.show_hint)
        self.hint_button.pack(pady=5)

    def close(self):
        self.engine.quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChessApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()
