from pathlib import Path
from tkinter import Tk, Canvas, Button, PhotoImage, Toplevel

OUTPUT_PATH = Path(__file__).parent

# Set ASSETS_PATH relative to the OUTPUT_PATH
ASSETS_PATH = OUTPUT_PATH / "assets" / "frame0"

class MainWindow:
    def __init__(self, root, button_callback):
        self.root = root
        self.button_callback = button_callback
        self.root.geometry("1111x777")
        self.root.configure(bg="#EAEAEA")
        
        self.canvas = Canvas(
            self.root,
            bg="#EAEAEA",
            height=777,
            width=1111,
            bd=0,
            highlightthickness=0,
            relief="ridge"
        )
        
        self.canvas.place(x=0, y=0)
        self.image_image_1 = PhotoImage(file=self.relative_to_assets("image_1.png"))
        self.image_1 = self.canvas.create_image(555.0, 54.0, image=self.image_image_1)
        
        self.button_image_1 = PhotoImage(file=self.relative_to_assets("button_1.png"))
        self.button_1 = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=self.on_button_1_click,
            relief="flat"
        )
        self.button_1.place(x=40.0, y=606.0, width=249.0, height=60.0)
        
        self.button_image_2 = PhotoImage(file=self.relative_to_assets("button_2.png"))
        self.button_2 = Button(
            image=self.button_image_2,
            borderwidth=0,
            highlightthickness=0,
            command=self.on_button_2_click,
            relief="flat"
        )
        self.button_2.place(x=787.0, y=606.0, width=290.0, height=60.0)
        
        self.button_image_3 = PhotoImage(file=self.relative_to_assets("button_3.png"))
        self.button_3 = Button(
            image=self.button_image_3,
            borderwidth=0,
            highlightthickness=0,
            command=self.on_button_3_click,
            relief="flat"
        )
        self.button_3.place(x=415.0, y=606.0, width=282.0, height=60.17909240722656)
        
        self.image_image_2 = PhotoImage(file=self.relative_to_assets("image_2.png"))
        self.image_2 = self.canvas.create_image(164.0, 391.0, image=self.image_image_2)
        
        self.image_image_3 = PhotoImage(file=self.relative_to_assets("image_3.png"))
        self.image_3 = self.canvas.create_image(555.0, 378.0, image=self.image_image_3)
        
        self.image_image_4 = PhotoImage(file=self.relative_to_assets("image_4.png"))
        self.image_4 = self.canvas.create_image(922.0, 388.0, image=self.image_image_4)
        
        self.image_image_5 = PhotoImage(file=self.relative_to_assets("image_5.png"))
        self.image_5 = self.canvas.create_image(556.0, 52.0, image=self.image_image_5)
        
        self.root.resizable(False, False)
        
    def relative_to_assets(self, path: str) -> Path:
        return ASSETS_PATH / Path(path)

    def on_button_1_click(self):
        self.button_callback("Backtest strategy button")

    def on_button_2_click(self):
        self.button_callback("Find candlestick paterns button")

    def on_button_3_click(self):
        self.button_callback("Genetic optimalization button")

