import socket
import os
import sys
import tkinter as tk
from tkinter import filedialog

BUFFER_SIZE = 1024
FILE_BUFFER_SIZE = 100


def catch_sabotage(or_address, curr_address, sock):
	if not or_address == curr_address:
		sock.sendto('You have attempted to sabotage the server'.encode('ascii'), curr_address)
		print('Client', curr_address, 'has tried to sabotage')
		return True


def secure_receive(sock_name, sock, buffer_size):
	data, address = sock.recvfrom(buffer_size)
	if catch_sabotage(sock_name, address, sock):
		raise Exception('attempted sabotage')
	return data.decode('ascii')


def accept_server_file(sock, sock_name, file_name):
	data = secure_receive(sock_name, sock, BUFFER_SIZE)
	sock.sendto(file_name.encode('ascii'), sock_name)
	data = secure_receive(sock_name, sock, BUFFER_SIZE)
	file_name, size, expected_packets = data.split('@')
	dir_path = os.path.dirname(os.path.realpath(__file__))
	file_dir_path = os.path.join(dir_path, 'files', 'client_' + sock.getsockname())
	try:
		os.makedirs(file_dir_path, exist_ok=True)
		print("Directory created successfully")
	except OSError as error:
		print("Directory can not be created")
	file_path = os.path.join(file_dir_path, file_name)
	file = open(file_path, 'w+')
	sock.sendto('send file now'.encode('ascii'), sock_name)
	bytes_received = 0
	while bytes_received < size:
		data = secure_receive(sock_name, sock, FILE_BUFFER_SIZE)
		file.write(data)
		bytes_received += FILE_BUFFER_SIZE
	file.close()
	sock.sendto('File Received'.encode('ascii'), sock_name)
	print('Received File:', file_name, 'from client:', sock_name)


def send_file(sock, address):
	secure_receive(address, sock, BUFFER_SIZE)
	root = tk.Tk()
	root.withdraw()
	file_path = filedialog.askopenfilename()
	file_name = os.path.basename(file_path)
	file_size = sys.getsizeof(file_path)
	expected_packets = (file_size / FILE_BUFFER_SIZE) + 1
	print(file_path, file_size, expected_packets)
	data = file_name + '@' + str(file_size) + '@' + str(expected_packets)
	sock.sendto(data.encode('ascii'), address)
	secure_receive(address, sock, BUFFER_SIZE)
	file = open(file_path, 'r')
	bytes_sent = 0
	while bytes_sent < file_size:
		chunk = file.read(FILE_BUFFER_SIZE)
		sock.sendto(chunk, address)
		bytes_sent += FILE_BUFFER_SIZE
	data = secure_receive(address, sock, BUFFER_SIZE)
	if len(data) == 0:
		raise Exception('Error listing directory, client may not be available')


def get_files(sock, address):
	no_files = secure_receive(address, sock, BUFFER_SIZE)
	sock.sendto(str(no_files).encode('ascii'), address)
	files_list = []
	for i in range(no_files):
		file_name = secure_receive(address, sock, BUFFER_SIZE)
		files_list.append(file_name)
		print((i + 1), ':', file_name)
	index = int(input('Choose the index of choice to select the file: '))
	sock.sendto(files_list[index - 1].encode('ascii'), address)
	return files_list[index - 1]


def view_files(sock, address):
	no_files = secure_receive(address, sock, BUFFER_SIZE)
	sock.sendto(str(no_files).encode('ascii'), address)
	files_list = []
	for i in range(no_files):
		file_name = secure_receive(address, sock, BUFFER_SIZE)
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
		sock.sendto(choices[index - 1].encode('ascii'), server_address)
		if choices[index - 1] == 'send':
			send_file(sock, server_address)
		elif choices[index - 1] == 'receive':
			data = get_files(sock, server_address)
			accept_server_file(sock, server_address, data)
		elif choices[index - 1] == 'browse':
			view_files(sock, server_address)
