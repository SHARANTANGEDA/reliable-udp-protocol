import tkinter as tk
from tkinter import filedialog
import os

root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename()
print(file_path)
file_name = os.path.basename(file_path)
print(file_name)
