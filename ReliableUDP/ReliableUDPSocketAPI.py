import socket
import math
from ReliableUDP.ReliableUDP import *
from time import sleep

BUFFER_SIZE = 600
HEADERS_SIZE = 30
ACK_SIZE = 30
RTT = 0.01


def _get_packetized_data(data, seq_nums, seq_nums_avail):
	data_size = len(str(data).encode('utf-8'))
	no_packets = max(1, math.ceil(data_size / (BUFFER_SIZE - HEADERS_SIZE)))
	seq_nums, seq_nums_avail = add_sequence_nums(seq_nums, seq_nums_avail, no_packets)
	data_chunks = [data[i:i + no_packets] for i in range(0, len(data), no_packets)]
	return data_size, no_packets, data_chunks


def catch_sabotage(or_address, curr_address, sock):
	if not or_address == curr_address:
		sock.sendto('You have attempted to sabotage the server'.encode('ascii'), curr_address)
		print('Client', curr_address, 'has tried to sabotage')
		return True


def secure_receive(sock_name, sock, buffer_size):
	data, address = sock.recvfrom(buffer_size)
	if catch_sabotage(sock_name, address, sock):
		raise Exception('attempted sabotage')
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
		sleep(RTT)
		sock.settimeout(RTT)
		# sock.setblocking(False)
		temp = 0
		while temp < 4:
			if len(ack_packet_list) == 0:
				print('Success')
				return True
			for size in ack_packet_list:
				try:
					data = secure_receive(address, sock, size)
					seq_num = int(data[1:])
					self.seq_nums_avail[self.seq_nums.index(seq_num)] = True
					ack_packet_list.remove(size)
				except OSError:
					print('Packet lost, prepping retransmission')
			for idx, items in enumerate(self.seq_nums_avail):
				if not items:
					ack_packet_size, packet_data = DataPacket(self.seq_nums[idx],
															  packet_dict[self.seq_nums[idx]]).prep_packet()
					sock.sendto(packet_data.encode('utf-8'), address)
			temp += 1
		return False
	
	def send_data(self, sock, data, address):
		data_size, no_packets, data_chunks = _get_packetized_data(data, self.seq_nums, self.seq_nums_avail)
		print(data_size, no_packets, len(data_chunks))  # DEBUG CODE
		init, curr_packet_num = 0, 0
		ack_pack_list, packet_dict = [], {}
		if self.window_size > no_packets:
			for i in range(no_packets):
				packet_dict[self.seq_nums] = data_chunks[i]
				ack_packet_size, packet_data = DataPacket(self.seq_nums[i], data_chunks[i]).prep_packet()
				sock.sendto(packet_data.encode('utf-8'), address)
				ack_pack_list.append(ack_packet_size)
			if self._receive_ack(sock, address, no_packets, ack_pack_list, packet_dict):
				return
			else:
				sock.close()
				print('Peer unavailable, connection closed')
		else:
			while curr_packet_num < no_packets:
				while init + self.window_size > curr_packet_num:
					packet_dict[self.seq_nums] = data_chunks[curr_packet_num]
					ack_packet_size, packet_data = DataPacket(self.seq_nums[curr_packet_num],
															  data_chunks[curr_packet_num]).prep_packet()
					sock.sendto(packet_data.encode('utf-8'), address)
					ack_pack_list.append(ack_packet_size)
					curr_packet_num += 1
				temp = 0
				while temp < 4:
					for size in ack_pack_list:
						try:
							data = secure_receive(address, sock, size)
							seq_num = int(data[1:])
							self.seq_nums_avail[self.seq_nums.index(seq_num)] = True
							ack_pack_list.remove(size)
						except OSError:
							print('Packet lost, prepping retransmission')
					for idx, items in enumerate(self.seq_nums_avail):
						if not items:
							ack_pack_list, packet_data = DataPacket(self.seq_nums[idx],
																	packet_dict[self.seq_nums[idx]]).prep_packet()
							sock.sendto(packet_data.encode('utf-8'), address)
					for idx, seq in enumerate(self.seq_nums_avail):
						if not seq:
							break
						init += 1
					temp += 1
			if not self._receive_ack(sock, address, no_packets, ack_pack_list, packet_dict):
				sock.close()
				print('Peer unavailable, connection closed')
