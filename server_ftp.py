import socket
import os
import sys
from ReliableUDP.ReliableUDPSocketAPI import ReliableUDPSocket
from collections import OrderedDict
import argparse
import threading

BUFFER_SIZE = 1500
FILE_BUFFER_SIZE = 600


def accept_client_file(sock, sock_name, client_info):
	print('Receiving file from Client')
	# ReliableUDPSocket().send_data(sock, 'send file name, size and expected_no_packets', sock_name)
	data = ReliableUDPSocket().receive_data(sock, sock_name, False)
	# ReliableUDPSocket().send_data(sock, 'send file now', sock_name)
	file_name, size = data.split('@')
	dir_path = os.path.dirname(os.path.realpath(__file__))
	file_dir_path = os.path.join(dir_path, 'files', 'server_' + sock.getsockname()[0])
	try:
		os.makedirs(file_dir_path, exist_ok=True)
		print("Directory created successfully")
	except OSError as error:
		print("Directory can not be created")
	file_path = os.path.join(file_dir_path, file_name)
	# data_buffer = OrderedDict()
	ReliableUDPSocket().receive_data(sock, sock_name, True, file_path)
	# ReliableUDPSocket().send_data(sock, 'File received', sock_name)
	# print('Received File:', file_name, 'from client:', sock_name)


def send_file(sock, address, client_info):
	get_files(sock, address, client_info)
	# ReliableUDPSocket().send_data(sock, 'enter file name of selected file', address)
	file_name = ReliableUDPSocket().receive_data(sock, address, False)
	dir_path = os.path.dirname(os.path.realpath(__file__))
	file_path = os.path.join(dir_path, 'src_files', file_name)
	# ReliableUDPSocket().receive_data(sock, address, False)
	file = open(file_path, 'r').readlines()
	data = ''
	for line in file:
		data += line
	ReliableUDPSocket().send_data(sock, data, address)
	# ReliableUDPSocket().receive_data(sock, address, False)


def get_files(sock, address, client_info):
	dir_path = os.path.dirname(os.path.realpath(__file__))
	files = os.path.join(dir_path, 'src_files')
	files_list = os.listdir(files)
	no_files = len(files_list)
	ReliableUDPSocket().send_data(sock, str(no_files), address)
	ReliableUDPSocket().receive_data(sock, address, False)
	for file in files_list:
		ReliableUDPSocket().send_data(sock, file, address)
	# ReliableUDPSocket().receive_data(sock, address, False)


def choose_and_add_thread(sock, address, text, client_info):
	# print('SELECT', text)
	if text == 'send':
		accept_client_file(sock, address, client_info)
	elif text == 'receive':
		send_file(sock, address, client_info)
	elif text == 'browse':
		get_files(sock, address, client_info)
	dict(client_info).pop(address)


class ServerThread(threading.Thread):
	def __init__(self, sock, address, text, client_info):
		threading.Thread.__init__(self)
		self.sock = sock
		self.address = address
		self.text = text
		self.client_info = client_info
	
	def run(self):
		print("Starting {}".format(self.address))
		self.sock.setblocking(True)
		choose_and_add_thread(self.sock, self.address, self.text, self.client_info)


def server(host, port):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((host, port))
	client_info = {}
	while True:
		# sock.setblocking(True)
		print('Server is Ready!!!')
		sock.setblocking(True)
		data, address = sock.recvfrom(BUFFER_SIZE)
		client_info[address] = sock
		text = data.decode('utf-8')
		ServerThread(sock, address, text, client_info).run()


# if __name__ == '__main__':
# 	parser = argparse.ArgumentParser(description='Send and Receive UDP locally')
# 	parser.add_argument('-p', metavar='PORT', type=int, default=1060, help='UDP port (default 53)')
# 	parser.add_argument('h', metavar='Host', type=str, default='localhost', help='Host Ip Address')
# 	args = parser.parse_args()
# 	server(args.h, args.p)

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Send and receive over TCP')
	parser.add_argument('host', help='interface the server listens at;host the client sends to')
	parser.add_argument('-p', metavar='PORT', type=int, default=1060, help='TCP port (default 1060)')
	args = parser.parse_args()
	server(args.host, args.p)
