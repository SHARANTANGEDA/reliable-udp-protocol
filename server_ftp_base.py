import socket
import os
import sys
from ReliableUDP.ReliableUDPSocketAPI import ReliableUDPSocket
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


def accept_client_file(sock, sock_name, client_info):
	sock.sendto('send file name, size and expected_no_packets'.encode('ascii'), sock_name)
	data = secure_receive(sock_name, sock, BUFFER_SIZE)
	sock.sendto('send file now'.encode('ascii'), sock_name)
	file_name, size, expected_packets = data.split('@')
	dir_path = os.path.dirname(os.path.realpath(__file__))
	file_dir_path = os.path.join(dir_path, 'files', 'server_'+sock.getsockname()[0])
	try:
		os.makedirs(file_dir_path, exist_ok=True)
		print("Directory created successfully")
	except OSError as error:
		print("Directory can not be created")
	file_path = os.path.join(file_dir_path, file_name)
	file = open(file_path, 'w+')
	bytes_received = 0
	while bytes_received < size:
		data = secure_receive(sock_name, sock, FILE_BUFFER_SIZE)
		file.write(data)
		bytes_received += FILE_BUFFER_SIZE
	sock.sendto('File received'.encode('ascii'), sock_name)
	file.close()
	print('Received File:', file_name, 'from client:', sock_name)


def send_file(sock, address, client_info):
	get_files(sock, address, client_info)
	sock.sendto('enter file name of selected file'.encode('ascii'), address)
	file_name = secure_receive(address, sock, BUFFER_SIZE)
	dir_path = os.path.dirname(os.path.realpath(__file__))
	file_path = os.path.join(dir_path, 'src_files', file_name)
	file_size = sys.getsizeof(file_path)
	expected_packets = (file_size / FILE_BUFFER_SIZE) + 1
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


def get_files(sock, address, client_info):
	dir_path = os.path.dirname(os.path.realpath(__file__))
	files = os.path.join(dir_path, 'files')
	files_list = os.listdir(files)
	no_files = len(files_list)
	sock.sendto(str(no_files).encode('ascii'), address)
	data = secure_receive(address, sock, BUFFER_SIZE)
	if len(data) == 0:
		return
	for file in files_list:
		sock.sendto(file.encode('ascii'), address)
	data = secure_receive(address, sock, BUFFER_SIZE)
	if len(data) == 0:
		raise Exception('Error listing directory, client may not be available')
	

def server(host, port):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((host, port))
	client_info = {}
	while True:
		data, address = sock.recvfrom(BUFFER_SIZE)
		client_info[address] = [data]
		text = data.decode('ascii')
		if text == 'send':
			accept_client_file(sock, address, client_info)
		elif text == 'receive':
			send_file(sock, address, client_info)
		elif text == 'browse':
			get_files(sock, address, client_info)
