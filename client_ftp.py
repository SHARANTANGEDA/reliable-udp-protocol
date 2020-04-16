import socket
import os
import sys
import tkinter as tk
from tkinter import filedialog
from ReliableUDP.ReliableUDPSocketAPI import ReliableUDPSocket
from collections import OrderedDict
BUFFER_SIZE = 1024
FILE_BUFFER_SIZE = 100


def accept_server_file(sock, sock_name, file_name):
	ReliableUDPSocket().receive_data(sock_name, sock, OrderedDict(), False)
	ReliableUDPSocket().send_data(sock, file_name, sock_name)
	data = ReliableUDPSocket().receive_data(sock_name, sock, OrderedDict(), False)
	file_name, size, expected_packets = data.split('@')
	dir_path = os.path.dirname(os.path.realpath(__file__))
	file_dir_path = os.path.join(dir_path, 'files', 'client_' + sock.getsockname())
	try:
		os.makedirs(file_dir_path, exist_ok=True)
		print("Directory created successfully")
	except OSError as error:
		print("Directory can not be created")
	file_path = os.path.join(file_dir_path, file_name)
	ReliableUDPSocket().send_data(sock, 'send file now', sock_name)
	data_buffer = OrderedDict()
	ReliableUDPSocket().receive_data(sock, sock_name, data_buffer, True, file_path)
	ReliableUDPSocket().send_data(sock, 'File Received', sock_name)
	print('Received File:', file_name, 'from client:', sock_name)


def send_file(sock, address):
	ReliableUDPSocket().receive_data(address, sock, OrderedDict(), False)
	root = tk.Tk()
	root.withdraw()
	file_path = filedialog.askopenfilename()
	file_name = os.path.basename(file_path)
	file_size = sys.getsizeof(file_path)
	expected_packets = (file_size / FILE_BUFFER_SIZE) + 1
	print(file_path, file_size, expected_packets)
	data = file_name + '@' + str(file_size) + '@' + str(expected_packets)
	ReliableUDPSocket().send_data(sock, data, address)
	ReliableUDPSocket().receive_data(address, sock, OrderedDict(), False)
	file = open(file_path, 'r').readlines()
	data = ''
	for line in file:
		data += line
	ReliableUDPSocket().send_data(sock, data, address)
	ReliableUDPSocket().receive_data(address, sock, OrderedDict(), False)


def get_files(sock, address):
	no_files = ReliableUDPSocket().receive_data(address, sock, OrderedDict(), False)
	ReliableUDPSocket().send_data(sock, no_files, address)
	files_list = []
	for i in range(no_files):
		file_name = ReliableUDPSocket().receive_data(address, sock, OrderedDict(), False)
		files_list.append(file_name)
		print((i + 1), ':', file_name)
	index = int(input('Choose the index of choice to select the file: '))
	ReliableUDPSocket().send_data(sock, files_list[index - 1], address)
	return files_list[index - 1]


def view_files(sock, address):
	no_files = ReliableUDPSocket().receive_data(address, sock, OrderedDict(), False)
	ReliableUDPSocket().send_data(sock, no_files, address)
	files_list = []
	for i in range(no_files):
		file_name = ReliableUDPSocket().receive_data(address, sock, OrderedDict(), False)
		files_list.append(file_name)
		print((i + 1), ':', file_name)
	sock.sendto('list received'.encode('ascii'), address)


def client(host, port):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	server_address = (host, port)
	while True:
		choices = ['send', 'receive', 'browse']
		for idx, item in enumerate(choices):
			print((idx + 1), ":", item, 'files')
		index = int(input('Choose the index of choice to run the FTP: '))
		ReliableUDPSocket().send_data(sock, choices[index - 1], server_address)
		if choices[index - 1] == 'send':
			send_file(sock, server_address)
		elif choices[index - 1] == 'receive':
			data = get_files(sock, server_address)
			accept_server_file(sock, server_address, data)
		elif choices[index - 1] == 'browse':
			view_files(sock, server_address)
