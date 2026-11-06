import asyncio

from cryptography import x509
from cryptography.hazmat.backends import default_backend
import glob
import numpy as np
import os
import pyshark

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
            counter_a = 0
            counter_b = 0
            print("Loading {}...".format(path), end='\r')

        # Read pcap file
        #pcap = iter(pyshark.FileCapture(path))

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        pcap = iter(pyshark.FileCapture(path, eventloop=loop))

        # Initialise result
        result = list()

        # Loop over packets
        while True:
            try:
                packet = next(pcap)
            except:
                break
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
                continue

            # Find the IP layer by name instead of by position
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
                counter_a += 1
                counter_b += 1
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

            # Check whether TLS certificate is in packet
            # (newer Wireshark versions call this layer "TLS" instead of "SSL")
            tls_layer = None
            if "TLS" in packet:
                tls_layer = packet.tls
            elif "SSL" in packet:
                tls_layer = packet.ssl

            if tls_layer is not None and \
               tls_layer.get("handshake_certificate") is not None:
                # Get certificate
                cert = tls_layer.get('handshake_certificate')
                # Parse cert to bytes
                cert = bytes.fromhex(cert.replace(':', ''))
                # Parse x509 certificate as DER
                cert = x509.load_der_x509_certificate(cert,
                                                      default_backend())
                # Get serial number - TODO extend with other features?
                d[-1] = cert.serial_number

            # Append data item to result
            result.append(d)

        # Close capture
        pcap.close()

        if self.verbose:
            print()

        # Return result as numpy array
        return np.array(result)
