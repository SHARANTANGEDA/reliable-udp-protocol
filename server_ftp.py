import socket
import os
import sys
from ReliableUDP.ReliableUDPSocketAPI import ReliableUDPSocket
from collections import OrderedDict

BUFFER_SIZE = 1024
FILE_BUFFER_SIZE = 600


def accept_client_file(sock, sock_name, client_info):
	ReliableUDPSocket().send_data(sock, 'send file name, size and expected_no_packets', sock_name)
	data = ReliableUDPSocket().receive_data(sock, sock_name, OrderedDict(), False)
	ReliableUDPSocket().send_data(sock, 'send file now', sock_name)
	file_name, size, expected_packets = data.split('@')
	dir_path = os.path.dirname(os.path.realpath(__file__))
	file_dir_path = os.path.join(dir_path, 'files', 'server_' + sock.getsockname())
	try:
		os.makedirs(file_dir_path, exist_ok=True)
		print("Directory created successfully")
	except OSError as error:
		print("Directory can not be created")
	file_path = os.path.join(file_dir_path, file_name)
	data_buffer = OrderedDict()
	ReliableUDPSocket().receive_data(sock, sock_name, data_buffer, True, file_path)
	ReliableUDPSocket().send_data(sock, 'File received', sock_name)
	print('Received File:', file_name, 'from client:', sock_name)


def send_file(sock, address, client_info):
	get_files(sock, address, client_info)
	ReliableUDPSocket().send_data(sock, 'enter file name of selected file', address)
	file_name = ReliableUDPSocket().receive_data(sock, address, OrderedDict(), False)
	dir_path = os.path.dirname(os.path.realpath(__file__))
	file_path = os.path.join(dir_path, 'src_files', file_name)
	file_size = sys.getsizeof(file_path)
	expected_packets = (file_size / FILE_BUFFER_SIZE) + 1
	data = file_name + '@' + str(file_size) + '@' + str(expected_packets)
	ReliableUDPSocket().send_data(sock, data, address)
	ReliableUDPSocket().receive_data(sock, address, OrderedDict(), False)
	file = open(file_path, 'r').readlines()
	data = ''
	for line in file:
		data += line
	ReliableUDPSocket().send_data(sock, data, address)
	ReliableUDPSocket().receive_data(sock, address, OrderedDict(), False)


def get_files(sock, address, client_info):
	dir_path = os.path.dirname(os.path.realpath(__file__))
	files = os.path.join(dir_path, 'files')
	files_list = os.listdir(files)
	no_files = len(files_list)
	ReliableUDPSocket().send_data(sock, no_files, address)
	ReliableUDPSocket().receive_data(sock, address, OrderedDict(), False)
	for file in files_list:
		ReliableUDPSocket().send_data(sock, file, address)
	ReliableUDPSocket().receive_data(address, sock, OrderedDict(), False)


def server(host, port):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((host, port))
	client_info = {}
	while True:
		data, address = sock.recvfrom(BUFFER_SIZE)
		client_info[address] = [data]
		text = data.decode('utf-8')
		if text == 'send':
			accept_client_file(sock, address, client_info)
		elif text == 'receive':
			send_file(sock, address, client_info)
		elif text == 'browse':
			get_files(sock, address, client_info)
