import socket
import os
import sys
import tkinter as tk
from tkinter import filedialog
from ReliableUDP.ReliableUDPSocketAPI import ReliableUDPSocket
import argparse


# BUFFER_SIZE = 1024
# FILE_BUFFER_SIZE = 100


def accept_server_file(sock, sock_name, file_name):
	# ReliableUDPSocket().receive_data(sock, sock_name, False)
	ReliableUDPSocket().send_data(sock, file_name, sock_name, False)
	# data = ReliableUDPSocket().receive_data(sock, sock_name, False)
	dir_path = os.path.dirname(os.path.realpath(__file__))
	file_dir_path = os.path.join(dir_path, 'files', 'client_' + sock.getsockname()[0])
	try:
		os.makedirs(file_dir_path, exist_ok=True)
		print("Directory created successfully")
	except OSError as error:
		print("Directory can not be created")
	file_path = os.path.join(file_dir_path, file_name)
	# ReliableUDPSocket().send_data(sock, 'send file now', sock_name)
	ReliableUDPSocket().receive_data(sock, sock_name, False, True, file_path)
	# ReliableUDPSocket().send_data(sock, 'File Received', sock_name)
	print('Received File:', file_name, 'from client:', sock_name)


def send_file(sock, address):
	# data = ReliableUDPSocket().receive_data(sock, address, False)
	# print("Received from server:", data)
	root = tk.Tk()
	root.withdraw()
	file_path = filedialog.askopenfilename()
	file_name = os.path.basename(file_path)
	file_size = sys.getsizeof(file_path)
	data_1 = file_name + '@' + str(file_size)
	print('SENDING:', data_1)
	ReliableUDPSocket().send_data(sock, data_1, address, False)
	# ReliableUDPSocket().receive_data(sock, address, False)
	file = open(file_path, 'r')
	data = file.read()
	# data = ''
	# for line in file:
	# 	data += line
	ReliableUDPSocket().send_data(sock, data, address, False)


# ReliableUDPSocket().receive_data(sock, address, False)


def get_files(sock, address):
	no_files = ReliableUDPSocket().receive_data(sock, address, False, False)
	ReliableUDPSocket().send_data(sock, no_files, address, False)
	files_list = []
	for i in range(int(no_files)):
		file_name = ReliableUDPSocket().receive_data(sock, address, False, False)
		files_list.append(file_name)
		print((i + 1), ':', file_name)
	index = int(input('Choose the index of choice to select the file: '))
	# ReliableUDPSocket().send_data(sock, files_list[index - 1], address)
	return files_list[index - 1]


def view_files(sock, address):
	no_files = ReliableUDPSocket().receive_data(sock, address, False, False)
	print(no_files, type(no_files))
	ReliableUDPSocket().send_data(sock, no_files, address, False)
	files_list = []
	for i in range(int(no_files)):
		file_name = ReliableUDPSocket().receive_data(sock, address, False, False)
		files_list.append(file_name)
		print((i + 1), ':', file_name)


# ReliableUDPSocket().send_data(sock, 'list received', address)


def client(host, port):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	server_address = (host, port)
	choices = ['send', 'receive', 'browse']
	for idx, item in enumerate(choices):
		print((idx + 1), ":", item, 'files')
	index = int(input('Choose the index of choice to run the FTP: '))
	if index > 3 or index < 1:
		exit(1)
	# ReliableUDPSocket().send_data(sock, choices[index - 1], server_address)
	try:
		sock.settimeout(10)
		sock.sendto(str(choices[index - 1]).encode('utf-8'), server_address)
		if choices[index - 1] == 'send':
			send_file(sock, server_address)
		elif choices[index - 1] == 'receive':
			data = get_files(sock, server_address)
			accept_server_file(sock, server_address, data)
		elif choices[index - 1] == 'browse':
			view_files(sock, server_address)
		print('Task completed')
	except socket.error:
		print('Unable to contact server, Please try again, and check if the server is reachable')


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Send and receive over TCP')
	parser.add_argument('host', help='interface the server listens at;host the client sends to')
	parser.add_argument('-p', metavar='PORT', type=int, default=1060, help='TCP port (default 1060)')
	args = parser.parse_args()
	client(args.host, args.p)
