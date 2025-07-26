import chess, chess.engine, cv2, numpy as np, tkinter as tk
from PIL import ImageGrab
import json
import pyautogui
import time

# === CONFIGURATION ===
STOCKFISH_PATH = "C:\Users\ADMIN\OneDrive\Desktop\chess\stockfish.exe"

# STOCKFISH_PATH = "stockfish.exe"  # Adjust path if needed
BOARD_REGION = (500, 200, 640, 640)  # x, y, width, height — update to match your screen

TEMPLATES = {}
for piece in ['wp','wr','wn','wb','wq','wk','bp','br','bn','bb','bq','bk']:
    TEMPLATES[piece] = cv2.imread(f"templates/{piece}.png", 0)

def capture_board():
    x, y, w, h = BOARD_REGION
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)

def detect_pieces(board_img):
    square_size = BOARD_REGION[2] // 8
    board = [['' for _ in range(8)] for _ in range(8)]
    for name, template in TEMPLATES.items():
        result = cv2.matchTemplate(board_img, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(result >= 0.9)
        for pt in zip(*loc[::-1]):
            col = pt[0] // square_size
            row = pt[1] // square_size
            if 0 <= row < 8 and 0 <= col < 8:
                board[row][col] = name
    return board

def generate_fen(board):
    piece_map = {
        'wp': 'P', 'wn': 'N', 'wb': 'B', 'wr': 'R', 'wq': 'Q', 'wk': 'K',
        'bp': 'p', 'bn': 'n', 'bb': 'b', 'br': 'r', 'bq': 'q', 'bk': 'k',
    }
    fen_rows = []
    for row in board:
        empty = 0
        fen_row = ''
        for cell in row:
            if cell == '':
                empty += 1
            else:
                if empty > 0:
                    fen_row += str(empty)
                    empty = 0
                fen_row += piece_map.get(cell, '')
        if empty > 0:
            fen_row += str(empty)
        fen_rows.append(fen_row)
    return '/'.join(fen_rows) + ' w KQkq - 0 1'

def get_best_move(fen):
    board = chess.Board(fen)
    with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
        result = engine.analyse(board, chess.engine.Limit(time=0.1))
        return result['pv'][0].uci()

def show_overlay(move):
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.85)
    label = tk.Label(root, text=f"Best Move: {move}", font=("Helvetica", 28), fg="white", bg="black")
    label.pack(padx=20, pady=10)
    root.geometry("+100+100")
    root.after(3000, root.destroy)
    root.mainloop()

def square_to_screen(square):
    files = 'abcdefgh'
    col = files.index(square[0])
    row = 8 - int(square[1])
    x0, y0, w, h = BOARD_REGION
    square_size = w // 8
    x = x0 + col * square_size + square_size // 2
    y = y0 + row * square_size + square_size // 2
    return (x, y)

def auto_click_move(move_uci):
    from_sq = move_uci[:2]
    to_sq = move_uci[2:4]
    pyautogui.moveTo(*square_to_screen(from_sq), duration=0.2)
    pyautogui.click()
    time.sleep(0.1)
    pyautogui.moveTo(*square_to_screen(to_sq), duration=0.2)
    pyautogui.click()

if __name__ == "__main__":
    try:
        img = capture_board()
        board = detect_pieces(img)
        fen = generate_fen(board)
        move = get_best_move(fen)
        show_overlay(move)
        auto_click_move(move)
        print(json.dumps({"fen": fen, "best_move": move}))
    except Exception as e:
        print(json.dumps({"error": str(e)}))