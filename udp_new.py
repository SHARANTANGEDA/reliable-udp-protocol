import argparse, socket
from datetime import datetime
from ReliableUDP import *
import threading
from datetime import datetime

MAX_BYTES = 65555
window_size = 4
max_chars_per_packet = 16
wait_until_window_finishes = 3
# current_sequence_no = -1
# start_sequence_no = 0
info_packet_seq_no = -1


def split_data(data):
    split_list = []
    temp, idx = '', 0
    for i in range(len(data)):
        if idx == 16:
            idx = 0
            split_list.append(temp)
            temp = ''
        temp = temp + data[i]
        idx += 1
    return split_list


def get_sequence_no(current_seq_no, start_sequence_no):
    if start_sequence_no <= current_seq_no < start_sequence_no + window_size:
        print(current_seq_no, (current_seq_no + 1) % 10)
        return current_seq_no, (current_seq_no + 1) % 10
    else:
        print('Window size limit reached')


def server(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', port))
    print('Listening at {}'.format(sock.getsockname()))
    client_info = {}
    
    while True:
        data, address = sock.recvfrom(MAX_BYTES)
        sock.settimeout(1)
        text = data.decode('ascii')
        if text[0] == '-':
            client_info[address] = []
            start_time = datetime.now()
            # client_info[address].append(text[3:3 + int(text[2])])
        else:
            try:
                client_info[address].append(text[1:1 + int(text[0])])
            except:
                ## resend the info packet
                pass
        print(client_info[address])
        print("The client at {} says {!r}".format(address, text))
        text = 'Your data was {} bytes long'.format(len(data))
        data = text.encode('ascii')
        sock.sendto(data, address)


def client(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # text = 'The time is {}'.format(datetime.now())
    while True:
        current_sequence_no = 0
        start_sequence_no = 0
        data = input('Enter the data:\n')
        data = split_data(data)
        if len(data) != 0:
            sequence_no, current_sequence_no = get_sequence_no(current_sequence_no, start_sequence_no)
        else:
            print('Enter some valid data')
            return
        info_packet = InfoUDP(info_packet_seq_no, sequence_no, window_size).prep_packet()
        sock.sendto(info_packet.encode('ascii'), ('127.0.0.1', port))
        start_time = datetime.now()
        packet_pair, least_seq_no = {}, sequence_no
        for chunk in data:
            packet_pair[sequence_no] = chunk
            packet_data = ReliableDataUDP(chunk, sequence_no).prep_packet()
            data = packet_data.encode('ascii')
            sock.sendto(data, ('127.0.0.1', port))
            sequence_no, current_sequence_no = get_sequence_no(current_sequence_no, start_sequence_no)
        if datetime.now() - start_time <= 100:  # TODO
            for i in range(len(data)):
                data, address = sock.recvfrom(MAX_BYTES)
                text = data.decode('ascii')
                recvd_seq_no = int(text[1:1 + int(text[0])])
                if recvd_seq_no == least_seq_no:
                    start_sequence_no = (start_sequence_no + 1) % 10
                    least_seq_no = (least_seq_no + 1) % 10
                del packet_pair[recvd_seq_no]
        for seq_no, value in packet_pair.items():
            packet_data = ReliableDataUDP(value, seq_no).prep_packet()
            data = packet_data.encode('ascii')
            sock.sendto(data, ('127.0.0.1', port))
        
        print('The OS assigned me the address {}'.format(sock.getsockname()))
        data, address = sock.recvfrom(MAX_BYTES)
        text = data.decode('ascii')
        # if address[0] is not '127.0.0.1':
        #     print('The server {} is malicious'.format(address, text))
        # else:
        #     print('The server {} replied {!r}'.format(address, text))


if __name__ == '__main__':
    choices = {'client': client, 'server': server}
    parser = argparse.ArgumentParser(description='Send and Receive UDP locally')
    parser.add_argument('role', choices=choices, help='which role to play')
    parser.add_argument('-p', metavar='PORT', type=int, default=1060, help='UDP port (default 53)')
    args = parser.parse_args()
    function = choices[args.role]
    function(args.p)
