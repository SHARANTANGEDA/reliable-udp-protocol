import socket
import math
from ReliableUDP.ReliableUDP import *
from collections import OrderedDict
from datetime import datetime, timedelta

BUFFER_SIZE = 600
HEADERS_SIZE = 10
ACK_SIZE = 10
RTT = 15


def chunk_it(seq, num):
	avg = len(seq) / float(num)
	out = []
	last = 0.0
	while last < len(seq):
		out.append(seq[int(last):int(last + avg)])
		last += avg
	
	return out


def _get_packetized_data(data, seq_nums, seq_nums_avail):
	data_size = len(str(data).encode('utf-8'))
	no_packets = max(1, math.ceil(data_size / (BUFFER_SIZE - HEADERS_SIZE)))
	seq_nums, seq_nums_avail = add_sequence_nums(seq_nums, seq_nums_avail, no_packets)
	# data_chunks = [data[i:i + no_packets] for i in range(0, len(data), no_packets)]
	data_chunks = chunk_it(data, no_packets)
	# print(len(data_chunks), ":::", no_packets)
	return data_size, no_packets, data_chunks, seq_nums, seq_nums_avail


def catch_sabotage(or_address, curr_address, sock):
	if not or_address == curr_address:
		sock.sendto('You have attempted to sabotage the server'.encode('ascii'), curr_address)
		print('Client', curr_address, 'has tried to sabotage')
		return True


def secure_receive(sock_name, sock, buffer_size):
	data, address = sock.recvfrom(buffer_size)
	# print(len(data), "DATA", sock_name)
	# if catch_sabotage(sock_name, address, sock):
	# 	raise Exception('attempted sabotage')
	return data.decode('utf-8')


def add_sequence_nums(sequence_nums, avail, no_packets):
	for i in range(no_packets):
		sequence_nums.append(i)
		avail.append(False)
	return sequence_nums, avail


class ReliableUDPSocket:
	def __init__(self):
		self.seq_nums = []
		self.seq_nums_avail = []
		self.window_size = 4
	
	def _receive_ack(self, sock, address, no_packets, ack_packet_list, packet_dict):
		# sock.settimeout(RTT)
		
		# time_out_after = timedelta(seconds=15)
		# start_time = datetime.now()
		# # while True:
		# if datetime.now() > start_time + time_out_after:
		# 	sock.close()
		# 	print('Connection closed data not received')
		# 	return False
		
		for idx, size in enumerate(ack_packet_list):
			try:
				# sock.setblocking(False)
				sock.settimeout(RTT)
				data = secure_receive(address, sock, BUFFER_SIZE)
				# print(size, 'receive_ack', data, len(ack_packet_list))
				# seq_num = int(data[1:])
				seq_num = int(data[1:])
				self.seq_nums_avail[self.seq_nums.index(seq_num)] = True
				del ack_packet_list[idx]
			except OSError or socket.error:
				pass
			except ValueError:
				sock.close()
				return True
				pass
		# print('Acknowledge Packet lost, prepping retransmission')
		if len(ack_packet_list) == 0:
			print('Success')
			self.seq_nums_avail.clear()
			self.seq_nums.clear()
			return True
		for idx, items in enumerate(self.seq_nums_avail):
			if not items:
				ack_packet_size, packet_data = DataPacket(self.seq_nums[idx],
														  packet_dict[self.seq_nums[idx]]).prep_packet()
				print("ACK_PAC", items, idx, )
				sock.sendto(packet_data.encode('utf-8'), address)
		return False
	
	def send_data(self, sock, data, address):
		# print("*************** Prep to Send Data *******************")
		data_size, no_packets, data_chunks, self.seq_nums, self.seq_nums_avail = _get_packetized_data(data,
																									  self.seq_nums,
																									  self.seq_nums_avail)
		# print("Data Size", data_size, no_packets, len(data_chunks))  # DEBUG CODE
		init, curr_packet_num = 0, 0
		ack_pack_list, packet_dict = [], {}
		# sock.setblocking(True)
		# print('TO SEND PACKET NOs', str(no_packets))
		pac_data = InfoPacket(no_packets).prep_packet()
		sock.sendto(pac_data.encode('utf-8'), address)
		# print('Packet Number Sent::', pac_data)
		if self.window_size > no_packets:
			for i in range(no_packets):
				packet_dict[self.seq_nums[i]] = data_chunks[i]
				ack_packet_size, packet_data = DataPacket(self.seq_nums[i], data_chunks[i]).prep_packet()
				# print("PACKET_BEING_SENT", len(packet_data), ack_packet_size, "CHUNK:DICT", len(packet_dict))
				sock.sendto(packet_data.encode('utf-8'), address)
				ack_pack_list.append(ack_packet_size)
			if self._receive_ack(sock, address, no_packets, ack_pack_list, packet_dict):
				return
			else:
				sock.close()
				print('Peer unavailable, connection closed')
		else:
			while curr_packet_num < no_packets:
				while (init + self.window_size > curr_packet_num) and (curr_packet_num < no_packets):
					# print('FINAL TEST', init, self.window_size, curr_packet_num)
					# print('FINAL TEST', self.seq_nums[curr_packet_num], data_chunks[curr_packet_num])
					packet_dict[self.seq_nums[curr_packet_num]] = data_chunks[curr_packet_num]
					ack_packet_size, packet_data = DataPacket(self.seq_nums[curr_packet_num],
															  data_chunks[curr_packet_num]).prep_packet()
					# print("PACKET_BEING_SENT", len(packet_data), ack_packet_size, "CHUNK:DICT", len(packet_data),
					# 	  curr_packet_num)
					sock.sendto(packet_data.encode('utf-8'), address)
					ack_pack_list.append(ack_packet_size)
					curr_packet_num += 1
				#
				# time_out_after = timedelta(seconds=15)
				# start_time = datetime.now()
				#
				# while True:
				# 	if datetime.now() > start_time + time_out_after:
				# 		print('Going to next Iteration')
				# 		break
				for idx, size in enumerate(ack_pack_list):
					try:
						sock.settimeout(RTT)
						# sock.setblocking(False)
						data = secure_receive(address, sock, BUFFER_SIZE)
						# print(size, 'receive_ack', data)
						seq_num = int(data[1:])
						self.seq_nums_avail[self.seq_nums.index(seq_num)] = True
						del ack_pack_list[idx]
					except OSError or socket.error:
						print('Packet lost, prepping retransmission')
				for idx, items in enumerate(self.seq_nums_avail):
					if idx == len(packet_dict):
						break
					if (not items) and idx < len(packet_dict):
						# print(idx, items, "PACKET DICT", len(packet_dict), len(self.seq_nums),
						# 	  len(self.seq_nums_avail))
						ack_packet_size, packet_data = DataPacket(self.seq_nums[idx],
																  packet_dict[self.seq_nums[idx]]).prep_packet()
						# print("RE_TRANS_PACKET_BEING_SENT", len(packet_data), ack_packet_size, "CHUNK:DICT",
						# 	  len(packet_dict), idx)
						# self.seq_nums_avail[idx] = True
						sock.sendto(packet_data.encode('utf-8'), address)
				for idx, seq in enumerate(self.seq_nums_avail):
					if not seq:
						break
					init += 1
	
	# if not self._receive_ack(sock, address, no_packets, ack_pack_list, packet_dict):
	# 	sock.close()
	# 	print('Peer unavailable, connection closed')
	
	def receive_data(self, sock, address, is_file, file_path=None):
		# print("*************** Prep to Receive Data *******************")
		data_buffer = OrderedDict()
		# sock.setblocking(True)
		no_packets = secure_receive(address, sock, BUFFER_SIZE)
		# trans_check = OrderedDict()
		# print('RECEIVED NO PACKETs:', no_packets)
		# if no_packets
		no_packets = int(no_packets[6:])
		time_out_after = timedelta(seconds=5)
		start_time = datetime.now()
		flag = False
		# sock.settimeout(RTT)
		while len(data_buffer) <= no_packets:
			if datetime.now() > start_time + time_out_after:
				sock.close()
				print('Connection closed data not received')
				flag = True
				break
			try:
				# sock.setblocking(False)
				sock.settimeout(RTT)
				data = secure_receive(address, sock, BUFFER_SIZE)
				# print('Data Received!!!', len(data))
				len_seq_num = int(data[0])
				seq_num = data[1: 1 + len_seq_num]
				ack_packet_data = AckPacket(seq_num).prep_packet()
				# print("SEQ_NUM_ACK_PACKET", ack_packet_data, '::::', len(data))
				sock.sendto(ack_packet_data.encode('utf-8'), address)
				data = data[1 + len_seq_num:]
				data_buffer[int(seq_num)] = data
			# trans_check[int(seq_num)] = False
			except OSError or socket.error:
				# print('Data Received')
				pass
			init_seq = -1
			re_trans_dict = []
			for key, data in data_buffer.items():
				if not key == init_seq + 1:
					print('CHECK', key, init_seq + 1)
					re_trans_dict.append(init_seq)
				init_seq += 1
			if len(data_buffer) >= no_packets and len(re_trans_dict) == 0:
				break
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
# def write_data_to_file(self, data_buffer: OrderedDict, file_path):
