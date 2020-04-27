import socket
import numpy as np
from copy import copy
import math
import hashlib

# Sequence number
# Data
# Window size = 4, Buffer = 8 *2000
BUFFER_SIZE = 600
HEADERS_SIZE = 10
MAX_PACKET_PAYLOAD = 508


def add_sequence_nums(sequence_nums, avail, no_packets):
	high=0
	if len(sequence_nums) != 0:
		high = max(sequence_nums) + 1
	for i in range(no_packets):
		sequence_nums.append(high)
		avail.append(False)
		high += 1
	return sequence_nums, avail


def chunk_it(seq, num):
	avg, out, last = len(seq) / float(num), [], 0.0
	while last < len(seq):
		out.append(seq[int(last):int(last + avg)])
		last += avg
	return out


class DataPacket:
	def __init__(self, data, seq_nums, seq_nums_avail):
		self.seq_nums = seq_nums
		self.data = data
		self.seq_nums_avail = seq_nums_avail
		self.packet_chunks = []
	
	def _get_packetized_data(self):
		data_size = len(str(self.data).encode('utf-8'))
		no_packets = max(1, math.ceil(data_size / (BUFFER_SIZE - HEADERS_SIZE)))
		seq_nums, seq_nums_avail = add_sequence_nums(self.seq_nums, self.seq_nums_avail, no_packets)
		data_chunks = chunk_it(self.data, no_packets)
		return data_size, no_packets, data_chunks, seq_nums, seq_nums_avail
	
	def prep_data(self):
		curr_data = self.data.encode('utf-8')
		no_packets = 0
		while len(curr_data) != 0:
			curr_length = 0
			seq_nums, seq_nums_avail = add_sequence_nums(self.seq_nums, self.seq_nums_avail, 1)
			packet_data = str(len(str(seq_nums[len(seq_nums) - 1]))).encode('utf-8') + str(
				seq_nums[len(seq_nums) - 1]).encode('utf-8')
			curr_length += len(packet_data)
			if len(curr_data) > MAX_PACKET_PAYLOAD - curr_length - 133:
				pack_data, curr_data = curr_data[
									   0: MAX_PACKET_PAYLOAD - curr_length - 133], curr_data[
																				   MAX_PACKET_PAYLOAD - curr_length - 133:]
				curr_length += len(pack_data)
				packet_data += pack_data
				packet_data += hashlib.md5(packet_data).hexdigest().encode("utf-8")
				curr_length += 32
				no_packets += 1
				self.packet_chunks.append(packet_data)
			elif len(curr_data) < MAX_PACKET_PAYLOAD - curr_length - 133:
				curr_length += len(curr_data)
				packet_data += curr_data
				packet_data += hashlib.md5(packet_data).hexdigest().encode("utf-8")
				curr_length += 32
				curr_data = ''
				no_packets += 1
				self.packet_chunks.append(packet_data)
		no_packs_info = str(len(str(no_packets))).encode('utf-8') + str(no_packets).encode('utf-8')
		self.packet_chunks = [no_packs_info + pack for pack in self.packet_chunks]
		return no_packets, self.packet_chunks, self.seq_nums, self.seq_nums_avail


# def prep_packet(self):
#     return len(str(len(str(self.seq_nums))) + str(self.seq_nums)), str(len(str(self.seq_nums))) + str(
#         self.seq_nums) + str(self.data)
class InfoPacket:
	def __init__(self, packet_no):
		self.packet_no = packet_no
	
	def prep_packet(self):
		return "PACKET".encode('utf-8') + str(self.packet_no).encode('utf-8') + hashlib.md5(
			"PACKET".encode('utf-8') + str(self.packet_no).encode('utf-8')).hexdigest().encode('utf-8')


class AckPacket:
	def __init__(self, sequence_no):
		self.sequence_no = sequence_no
	
	def prep_packet(self):
		return "ACK".encode('utf-8') + str(len(str(self.sequence_no))).encode('utf-8') + str(
			self.sequence_no).encode('utf-8') + hashlib.md5(
			str(len(str(self.sequence_no))).encode('utf-8') + str(self.sequence_no).encode('utf-8')).hexdigest().encode(
			'utf-8')
