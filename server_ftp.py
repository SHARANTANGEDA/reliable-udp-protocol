import socket
import os
from ReliableUDP.ReliableUDPSocketAPI import ReliableUDPSocket
import argparse
import threading
from datetime import datetime
BUFFER_SIZE = 1500
FILE_BUFFER_SIZE = 600


def accept_client_file(sock, sock_name, client_info):
	print('Receiving file from Client')
	# data = ReliableUDPSocket().receive_data(sock, sock_name, True, False)
	# file_name, size = data.split('@')
	file_name = str(datetime.now()) + '.txt'
	dir_path = os.path.dirname(os.path.realpath(__file__))
	file_dir_path = os.path.join(dir_path, 'files', 'from_client_' + sock_name[0])
	try:
		os.makedirs(file_dir_path, exist_ok=True)
		print("Directory created successfully")
	except OSError as error:
		print("Directory can not be created")
	file_path = os.path.join(file_dir_path, file_name)
	ReliableUDPSocket().receive_data(sock, sock_name, True, True, file_path)
	# ReliableUDPSocket().send_data(sock, 'File received', sock_name)
	# print('Received File:', file_name, 'from client:', sock_name)


def send_file(sock, address, client_info):
	get_files(sock, address, client_info)
	file_name = ReliableUDPSocket().receive_data(sock, address, True, False)
	dir_path = os.path.dirname(os.path.realpath(__file__))
	file_path = os.path.join(dir_path, 'src_files', file_name)
	file = open(file_path, 'r').readlines()
	data = ''
	for line in file:
		data += line
	ReliableUDPSocket().send_data(sock, data, address, True)


def get_files(sock, address, client_info):
	dir_path = os.path.dirname(os.path.realpath(__file__))
	files = os.path.join(dir_path, 'src_files')
	files_list = os.listdir(files)
	no_files = len(files_list)
	print(no_files, address, sock)
	ReliableUDPSocket().send_data(sock, str(no_files), address, True)
	ReliableUDPSocket().receive_data(sock, address, True, False)
	for file in files_list:
		ReliableUDPSocket().send_data(sock, file, address, True)


def choose_and_add_thread(sock, address, text, client_info):
	if text == 'send':
		sock.sendto(text.encode('utf-8'), address)
		accept_client_file(sock, address, client_info)
	# elif text == 'receive':
	# 	send_file(sock, address, client_info)
	elif text == 'browse':
		sock.sendto(text.encode('utf-8'), address)
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
		choose_and_add_thread(self.sock, self.address, self.text, self.client_info)


def server(host, port):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((host, port))
	client_info = {}
	while True:
		print('Server is Ready!!!')
		sock.setblocking(True)
		data, address = sock.recvfrom(BUFFER_SIZE)
		
		client_info[address] = sock
		text = data.decode('utf-8')
		print("Launching Thread")
		ServerThread(sock, address, text, client_info).run()


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Send and receive over TCP')
	parser.add_argument('host', help='interface the server listens at;host the client sends to')
	parser.add_argument('-p', metavar='PORT', type=int, default=1060, help='TCP port (default 1060)')
	args = parser.parse_args()
	server(args.host, args.p)
