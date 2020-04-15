import socket
import numpy as np

# Sequence number
# Data
# Window size = 4, Buffer = 8 *2000


class DataPacket:
    def __init__(self, seq_nums, data):
        self.seq_nums = seq_nums
        self.data = data
        
    def prep_packet(self):
        return str(len(str(self.seq_nums)))+str(self.seq_nums) + str(len(str(self.data))) + str(self.data)
        

class InfoPacket:
    def __init__(self,info_packet_seq_no, sequence_no, window_size):
        self.sequence_no = sequence_no
        self.window_size = window_size
        self.info_packet_seq_no = info_packet_seq_no
    
    def prep_packet(self):
        ack_packet_size = len(str(self.info_packet_seq_no).encode('utf-8'))+len(str(len(str(self.sequence_no))).encode('utf-8'))
        return ack_packet_size, str(self.info_packet_seq_no)+str(len(str(self.sequence_no)))+str(self.sequence_no)+str(len(str(self.window_size)))+str(self.window_size)


class AckPacket:
    def __init__(self, sequence_no):
        self.sequence_no = sequence_no
    
    def prep_packet(self):
        return str(len(str(self.sequence_no)))+str(self.sequence_no)
