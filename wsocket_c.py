#!/usr/bin/python3.6
# -*- coding: utf-8 -*-
# "sentdex"'s video - client.py
# az odoo.sh-ban működik; Colab-ban nem!
import os
import sys
import subprocess
import socket
import time
import errno

IP = "127.0.0.1"
PORT = 50416#1234

linux = sys.platform.startswith("linux")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        request = bytes(sys.argv[1].strip(), "utf-8")
    else:
        print('You must give one argument.')
        print(
"""USAGE: python3.6 socket_c.py [argument]
 Arguments:
  l                login, start server
  <artikel number> stock request
  q                quit server
 Result output:    stdout """)
        
        exit()
    
    """ ha NEM 'l' parancs az első, akkor '[Errno 111] Connection refused' hibával leáll,
        mert még nincs szerver! 
        errno.ECONNREFUSED, (errno.ECONNRESET, {}) 
        Ugyanez a hibaüzenet van, ha a szerverben "[Errno 98] Address already in use" a hiba!
    """
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((IP, PORT))

    except IOError as e:
        if e.errno == errno.ECONNREFUSED:
            if request == b'l':
                subprocess.Popen(['python', os.path.realpath('wsocket_s.py')], close_fds=True)
                time.sleep(1)
            else:
                client_socket.close()
                sys.exit('False request - Server is not running yet.')

            client_socket.connect((IP, PORT))

    client_socket.send(request)  # b'' "érkezik" a szerverre, ha ezt nem tudja végrehajtani
        
    response = client_socket.recv(1024)
    if linux:
      print('c:Response:', file=sys.stderr)
    else:
      print('c:Response:')#, file=sys.stderr)
    print(response.decode("utf-8"))

    client_socket.close()
    