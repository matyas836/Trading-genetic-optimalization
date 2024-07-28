from tkinter import Tk
from MainGUI import MainWindow
from backtest_window import backTestWindow
from optimalize_window import optimizeWindow
from patern_window import paternFinder

def handle_button_click(button_name):
    if button_name == "Backtest strategy button":
        backTestWindow()
    if button_name == "Genetic optimalization button":
        optimizeWindow()
    if button_name == "Find candlestick paterns button":
        paternFinder()


if __name__ == "__main__":
    root = Tk()
    app = MainWindow(root, handle_button_click)
    root.mainloop()
