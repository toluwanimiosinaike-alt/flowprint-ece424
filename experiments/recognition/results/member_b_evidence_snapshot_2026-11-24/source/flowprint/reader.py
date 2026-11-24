import asyncio

#asyncio is Python’s built-in library for asynchronous programming.
#Normal Python code runs in order
#asyncio changes that. Every time a task hits a wait, it hands control back,
#and Python goes off and does something useful in the meantime.

#asyncio is a package. A package is a folder of modules with an __init__.py file in it.
# When you run import asyncio, Python is really running that folder’s __init__.py,
# and that file pulls in the pieces from the other files.

#It is in /usr/local/lib/python3.13/asyncio/

from cryptography import x509

#Cryptography is a third-party package, and X.509 is a submodule inside it
#X.509 is the standard format for digital certificates, the files a server uses
# to prove who it is during a TLS/HTTPS connection.

#x.509 is a folder in the cryptography package

from cryptography.hazmat.backends import default_backend
#hazmat is another folder in cryptography just like X.509,
# which has another folder(subpackage) in it called backends

#default_backend is defined at line 10 of
# /usr/local/lib/python3.13/site-packages/cryptography/hazmat/backends/__init__.py.

#default_backend is a function that returns an object.
#A Backend Object
import glob
import numpy as np
import os
import pyshark

#pyshark is a third-party package, installed with pip install pyshark,
# that lets Python read network traffic. In reader.py it opens a .pcap file and
# hands you each packet as a Python object


#Inheritance
#The Reader class inherits from Python's base object class
#In python 3, this does nothing, since every object inherits
#from object automatically
class Reader(object):

    ########################################################################
    #                         Class initialisation                         #
    ########################################################################

    def __init__(self, verbose=False):
        """Reader object for extracting features from .pcap files.

            Parameters
            ----------
            verbose : boolean, default=False
                Boolean indicating whether to be verbose in reading.
            """
        # Set verbosity level
        self.verbose = verbose
        #verbose means “talkative.” It’s an on/off switch for whether the Reader prints progress messages while it works
        #Python lets you attach a new attribute to an object just by assigning to it.
        # You don’t have to declare it anywhere beforehand
        #, and no parent class has to provide it.

    ########################################################################
    #                             Read method                              #
    ########################################################################

    def read(self, path):
        """Read TCP and UDP packets from file given by path.

            Parameters
            ----------
            path : string
                Path to .pcap file to read.

            Returns
            -------
            result : np.array of shape=(n_packets, n_features)
                Where features consist of:
                [0]: Filename of capture
                [1]: Protocol TCP/UDP
                [2]: TCP/UDP stream identifier
                [3]: Timestamp of packet
                [4]: Length of packet
                [5]: IP packet source
                [6]: IP packet destination
                [7]: TCP/UDP packet source port
                [8]: TCP/UDP packet destination port
                [9]: SSL/TLS certificate if exists, else None
            """
        # If verbose, print which file is currently being read
        if self.verbose:
            #Creates two counters, both starting at zero, before the loop over packets begins:
            #counter_a counts the packets kept, meaning TCP or UDP ones.
            #counter_b counts every packet seen, kept or skipped.
            counter_a = 0
            counter_b = 0
            #format is a method of Python’s built-in string type, str
            #.format() fills the {} with the value of path
            #It is called on the "Loading {}..." string
            #path is a parameter for this function
            print("Loading {}...".format(path), end='\r')


        # Read pcap file
        #pcap = iter(pyshark.FileCapture(path))

        loop = asyncio.new_event_loop()
        #new_event_loop() is a function that returns an object.

        # An event loop object is a scheduler. It holds a list of jobs waiting to run
        # , runs each one until it has to wait on something, and keeps track of what
        # each paused job is waiting for so it can wake it up later.

        asyncio.set_event_loop(loop)
        #set_event_loop(loop) saves the scheduler called loop
        #so other code can look it up later with asyncio.get_event_loop().
        pcap = iter(pyshark.FileCapture(path, eventloop=loop))
        #FileCapture is a class inside pyshark, so calling it creates a
        #capture object. Which takes in path(the file to read) and
        #loop(What scheduler to use)
        #eventloop = loop is a keyword argument



        #FileCapture starks tshark, which is what actually reads the pcap file.
        #tshark goes through the file in order and writes each decoded packet out as text into a pipe.

        #FileCapture reads tshark’s output one packet at a time and
        # converts each one into a packet object for you.

        #iter() is a function that returns a generator object.
        #A generator object is an object that produces values one at a time,
        # only when asked,
        # and next() is how you ask for the next one.

        #pcap holds the generator object

        # Initialise result
        result = list()

        # Loop over packets to get all the packets out of the pcap file
        while True:
            try:
                packet = next(pcap)
                #one packet is returned
                #packet is now an instance of a class/module packet.py
                # in the pyshark third party package
            except:
                break
            #next() doesn’t return a special value like None when there’s nothing left.
            # It raises a StopIteration exception.
            # That’s Python’s built-in signal for “this iterator is finished.”
            # Without the try/except, that exception would crash the program right after the last packet
            """
            if not ("TCP" in packet or "UDP" in packet):
                counter_b += 1
                continue

            if self.verbose:
                counter_a += 1
                counter_b += 1
                print("Loading {}... {}/{} packets".format(path, counter_a, counter_b), end='\r')

            # Get required packet data
            d = [path,
                 packet.layers[2].layer_name, # Get
                 packet.layers[2].stream,     # Get stream ID
                 packet.sniff_timestamp,      # Get packet timestamp
                 packet.length,               # Get packet length
                 packet.layers[1].src,        # Get source IP or IPv6 (fixed)
                 packet.layers[1].dst,        # Get destination IP or IPv6 (fixed)
                 packet.layers[2].srcport,    # Get source port
                 packet.layers[2].dstport,    # Get destination port
                 None]

            # Check whether SSL/TLS certificate is in packet
            if "SSL" in packet and\
               packet.ssl.get("handshake_certificate") is not None:
                # Get certificate
                cert = packet.ssl.get('handshake_certificate')
                # Parse cert to bytes
                cert = bytes.fromhex(cert.replace(':', ''))
                # Parse x509 certificate as DER
                cert = x509.load_der_x509_certificate(cert,
                                                      default_backend())
                # Get serial number - TODO extend with other features?
                d[-1] = cert.serial_number
            """
            # Skip packets that are not plain TCP/UDP over IPv4/IPv6.
            # ICMP error packets contain a copy of a TCP/UDP header, so skip those too.
            if not ("TCP" in packet or "UDP" in packet) or \
               "ICMP" in packet or "ICMPV6" in packet:
                counter_b += 1
                continue #skip the rest of this loop iteration and go to the next packet


            # Find the IP layer by name instead of by position
            #Only finding the IP layer for packets that have TCP or UDP and Not ICMP
            if "IP" in packet:
                ip = packet.ip
            elif "IPV6" in packet:
                ip = packet.ipv6
            else:
                counter_b += 1
                continue

            # Find the transport layer by name instead of by position
            transport = packet.tcp if "TCP" in packet else packet.udp

            if self.verbose:
                counter_a += 1 #counting tcp/udp packets
                counter_b += 1 #counting all packets
                print("Loading {}... {}/{} packets".format(path, counter_a, counter_b), end='\r')

            # Get required packet data
            d = [path,
                 transport.layer_name,        # Get protocol (tcp/udp)
                 transport.stream,            # Get stream ID
                 packet.sniff_timestamp,      # Get packet timestamp
                 packet.length,               # Get packet length
                 ip.src,                      # Get source IP or IPv6
                 ip.dst,                      # Get destination IP or IPv6
                 transport.srcport,           # Get source port
                 transport.dstport,           # Get destination port
                 None]
            #attributes gotten ultimately from the third party package

            # Check whether TLS certificate is in packet
            # (newer Wireshark versions call this layer "TLS" instead of "SSL")
            tls_layer = None
            if "TLS" in packet:
                #packet.tls isn't an object attribute in the usual sense,
                #but still an attribute nonetheless.
                tls_layer = packet.tls
            elif "SSL" in packet:
                tls_layer = packet.ssl

            if tls_layer is not None and \
               tls_layer.get("handshake_certificate") is not None:
                # Get certificate
                cert = tls_layer.get('handshake_certificate')
                # Parse cert to bytes
                #The certificate started out as bytes. That’s what the server actually sent over the network.
                # Wireshark/tshark then wrote those bytes out as hex text so they could be passed to Python as a string.
                # This line undoes that step
                cert = bytes.fromhex(cert.replace(':', ''))
                # Parse x509 certificate as DER
                cert = x509.load_der_x509_certificate(cert,
                                                      default_backend())
                #load_der_x509_certificate() is a function reads the certificate’s bytes
                # according to the X.509 format rules and builds a Certificate object from them.
                #default_backend is ignored
                # Get serial number - TODO extend with other features?
                d[-1] = cert.serial_number
                #once you've created the certificate object, the serial
                #number is just a property on it.
                #it is then appended



            # Append data item to result
            result.append(d)


        # Close capture
        pcap.close()
        #pcap is not the FileCapture object. It’s the generator that iter() returned.
        # So pcap.close() calls the generator’s close() method, which is a built-in feature of every
        # Python generator.

        #A generator that’s paused at a yield is in the middle of running. Calling .close() on it:
        # Raises a special GeneratorExit exception inside it, at the spot where it’s paused.

        if self.verbose:
            print()
        #This tidies up the progress display.

        # Return result as numpy array
        return np.array(result)
        # result is a Python list of lists, one inner list (d) per packet:
        #np.array(result) turns that into a 2-D NumPy array, a table with one row per packet and 10 columns,
        # matching the docstring’s shape=(n_packets, n_features).
        # The function then hands it back to whoever called reader.read(path).
