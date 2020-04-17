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
        return len(str(len(str(self.seq_nums)))+str(self.seq_nums)), str(len(str(self.seq_nums)))+str(self.seq_nums) + str(self.data)
        

class InfoPacket:
    def __init__(self, packet_no):
        self.packet_no = packet_no
    
    def prep_packet(self):
        return "PACKET"+str(self.packet_no)


class AckPacket:
    def __init__(self, sequence_no):
        self.sequence_no = sequence_no
    
    def prep_packet(self):
        return str(len(str(self.sequence_no)))+str(self.sequence_no)
