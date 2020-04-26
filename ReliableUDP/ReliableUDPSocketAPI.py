import socket
import math
from ReliableUDP.ReliableUDP import *
from collections import OrderedDict
from datetime import datetime, timedelta

BUFFER_SIZE = 508
HEADERS_SIZE = 10
ACK_SIZE = 10
RTT = 15
Wait_Time_For_Timeout = 20
TOL_LIMIT = 5


def check_integrity_packet(data):
	try:
		no_packets = data[1:int(data[0]) + 1]
		seq_digits = int(data[int(data[0]) + 1])
		seq_num = data[int(data[0]) + 2: int(data[0]) + 2 + seq_digits]
		data_string = data[int(data[0]) + 2 + seq_digits: len(data) - 32]
		checksum = data[len(data) - 32:]
		if hashlib.md5(data[int(data[0]) + 1: len(data) - 32].encode('utf-8')).hexdigest() == checksum:
			return True, no_packets, seq_num, data_string
		else:
			return False, None, None, None
	except ValueError:
		return False, None, None, None


def catch_sabotage(or_address, curr_address, sock):
	if or_address[0] == 'localhost':
		or_address = ('127.0.0.1', or_address[1])
	if curr_address[0] == 'localhost':
		curr_address = ('127.0.0.1', curr_address[1])
	if not or_address == curr_address:
		print('Client', curr_address, 'has tried to sabotage', or_address)
		return True
	return False


def secure_receive(sock_name, sock, buffer_size):
	data, address = sock.recvfrom(buffer_size)
	if catch_sabotage(sock_name, address, sock):
		raise Exception('attempted sabotage, Shutting server down for manual Check!!')
	return data.decode('utf-8')


class ReliableUDPSocket:
	def __init__(self):
		self.seq_nums = []
		self.seq_nums_avail = []
		self.window_size = 4
		
	def send_data(self, sock, data, address, is_server):
		# print("*************** Prep to Send Data Wait 15 seconds for re-transmission*******************")
		no_packets, data_chunks, self.seq_nums, self.seq_nums_avail = DataPacket(
			data, self.seq_nums, self.seq_nums_avail).prep_data()
		init, curr_packet_num, ack_sent = 0, 0, 0
		ack_pack_list, packet_dict = [], {}
		STATE = 0
		while curr_packet_num < no_packets and STATE < TOL_LIMIT:
			while (init + self.window_size > curr_packet_num) and (curr_packet_num < no_packets):  # Sending Data
				packet_dict[self.seq_nums[curr_packet_num]] = data_chunks[curr_packet_num]
				sock.sendto(data_chunks[curr_packet_num], address)
				ack_pack_list.append(1)
				curr_packet_num += 1
			time_out_after = timedelta(seconds=Wait_Time_For_Timeout)
			start_time = datetime.now()
			sock.setblocking(False)
			while True:  # Waiting to receive Acknowledgement
				if datetime.now() > start_time + time_out_after:
					break
				if ack_sent >= len(ack_pack_list):
					break
				try:
					data = secure_receive(address, sock, BUFFER_SIZE)
					if len(data) != 0:
						start_time = datetime.now()
						seq_num = int(data[1:int(data[0]) + 1])
						self.seq_nums_avail[self.seq_nums.index(seq_num)] = True
						ack_sent += 1
				except BlockingIOError:
					pass
				except OSError or socket.error:
					print('Packet lost, prepping retransmission')
				except ValueError:
					print(
						"Re-Ordering or Corruption Tolerance limit is reached\nPlease try with a more reliable connection!!")
					exit(1)
			for idx, items in enumerate(self.seq_nums_avail):  # Re-transmission of Packets
				if idx == len(packet_dict):
					break
				if (not items) and idx < len(packet_dict):
					sock.sendto(packet_dict[self.seq_nums[idx]], address)
			prev_init = copy(init)
			for idx, seq in enumerate(self.seq_nums_avail):  # Checking remaining Packets to move window
				if not seq:
					break
				init += 1
			if prev_init == init:
				STATE += 1
			else:
				STATE = 0
	
	def receive_data(self, sock, address, is_server, is_file, file_path=None):
		# print("*************** Prep to Receive Data *******************")
		data_buffer = OrderedDict()
		# no_packets = secure_receive(address, sock, BUFFER_SIZE)
		no_packets, curr_pack_no = 0, 0
		# time_out_after = timedelta(seconds=Wait_Time_For_Timeout)
		# start_time = datetime.now()
		flag = False
		sock.setblocking(True)
		ack_pack_list = 0
		while True:
			if no_packets != 0 and curr_pack_no >= no_packets:
				break
			# if datetime.now() > start_time + time_out_after:
			# 	if not is_server:
			# 		sock.close()
			# 		print('Server is un-reachable at the moment')
			# 		flag = True
			# 		break
			try:
				data = secure_receive(address, sock, BUFFER_SIZE)
				integrity, no_packets, seq_num, data_string = check_integrity_packet(data)
				if integrity:
					seq_num = seq_num
					ack_packet_data = AckPacket(seq_num).prep_packet()
					sock.sendto(ack_packet_data, address)
					no_packets = int(no_packets)
					data_buffer[int(seq_num)] = data_string
					curr_pack_no += 1
				else:
					print('Packet is corrupted, requesting re-transmission')
			except OSError or socket.error:
				print('Problem connecting')
				exit(1)
			except ValueError:
				print(
					"Re-Ordering or Corruption Tolerance limit is reached\nPlease try with a more reliable connection!!")
				exit(1)
			init_seq = -1
			for key, data in data_buffer.items():
				if not key == init_seq + 1:
					print('CHECK', key, init_seq + 1)
					ack_pack_list += 1
				init_seq += 1
		# if len(data_buffer) >= no_packets and len(ack_pack_list) == 0:
		# 	break
		if not flag:
			if is_file:
				file = open(file_path, 'w+')
				for key, data in data_buffer.items():
					file.write(data)
				data_buffer.clear()
				file.close()
			else:
				total_data = ''
				for key, data in data_buffer.items():
					total_data += data
				data_buffer.clear()
				return total_data
		return
