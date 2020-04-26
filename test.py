import tkinter as tk
from tkinter import filedialog
import os
import hashlib

# root = tk.Tk()
# root.withdraw()
# file_path = filedialog.askopenfilename()
# print(file_path)
# file_name = os.path.basename(file_path)
# print(file_name)
# tse = "This is a Test String & @ 123"
# print(tse.encode('utf-8'))
# inv_tse = hashlib.md5(tse.encode('utf-8')).hexdigest().encode('utf-8')
# print(len(inv_tse))
tse = "Hello This is Sharan"
# print(tse.encode('utf-8'))
inv_tse = hashlib.md5(tse.encode('utf-8')).hexdigest().encode('utf-8')
# print(len(inv_tse))
data = "11102ec8956637a99787bd197eacd77acce5e"
no_packets = data[1:int(data[0])+1]
seq_digits = int(data[int(data[0])+1])
seq_num = data[int(data[0])+2: int(data[0])+2 + seq_digits]
data_string = data[int(data[0])+2 + seq_digits: len(data) - 32]
checksum = data[len(data) - 32:]
print(no_packets)
print(seq_num)
print(data_string)
print(hashlib.md5(data[int(data[0]) + 1: len(data) - 32].encode('utf-8')).hexdigest())
print(checksum)
