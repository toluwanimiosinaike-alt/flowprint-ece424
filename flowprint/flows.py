from datetime import datetime
#pulls in the datetime class from Python’s
# built-in datetime module
#/usr/local/lib/python3.13/datetime.py
import ipaddress
#loads Python’s built-in ipaddress module
#The module turns IP address strings like "192.168.1.5"
# into objects that know facts about themselves.

########################################################################
#                          Single Flow object                          #
########################################################################

class Flow(object):

    def __init__(self):
        """Representation of a Flow."""
        #A flow is a connection of packets, and each packet has
        #an ip addresses, certificates, lengths, and timestamps
        self.ips = set()
        #gives the Flow object an attribute called ips
        #and starts it off as an empty set.
        #set() is Python’s built-in way to make a set,
        # a collection that holds each value only once
        # and keeps no particular order.
        self.certificates = set()
        #same is done

        self.lengths    = list()
        self.timestamps = list()

    def add(self, packet):
        """Add a new packet to the flow.

            Parameters
            ----------
            packet : np.array of shape=(n_features,)
                Packet from Reader.
            """
        # Add flow identifiers
        self.ips.add((packet[5], packet[7]))
        #.add calls are set's built-in add method
        #We're putting this tuple in the set
        self.ips.add((packet[6], packet[8]))
        # Add certificate if any
        if packet[9] is not None:
            self.certificates.add(packet[9])
            #Most packets in a flow carry no certificate at all.
            #During a TLS connection the server sends its certificate once,
            # in the handshake at the start. All the packets after that
            # carry encrypted application data and have no certificate

        # Perform equivalence checks
        if len(self.ips) > 2:
        #The key is that every packet in one flow has the same two endpoints,
        # just swapped depending on direction, and a set throws away repeats.
        # So it never grows past 2 unless something is wrong.
            raise ValueError("More than 2 IPs found: {}".format(self.ips))
            #.format places self.ips in the {}
            #which puts the entire set as it stands at that moment into the message
        if len(self.certificates) > 1:
            raise ValueError("More than 1 certificate found: {}"
                             .format(self.certificates))

        # Set timestamps and lengths
        self.timestamps.append(float(packet[3]))
        #timestamp is converted into a float and added to the
        #timestamp list
        self.lengths   .append( int(packet[4]) if packet[5] == self.src() else
                               -int(packet[4]))
        #if statement meaning append the packet length as positive if this packet’s
        # source IP is the flow’s source, and otherwise append it as negative.

        #A flow is a two-way conversation, so its packets go in both directions.
        # Each packet has its own source, namely whoever sent that packet,
        # and that changes from packet to packet.
        # The flow as a whole has no built-in source,
        # so the code picks one endpoint and calls it the source.
        # That’s what self.src() returns.

        #The packet’s source flips back and forth. The flow’s source stays the same,
        # because it’s a fixed label for one side of the conversation.

        #self.lengths is a per-packet log of size and direction in order.
        # Each entry answers to questions:
        # Which side sent it? The sign: + means client → server, − means server → client.
        # How big was it? The number.

        # Return self
        return self
        #hands back the same Flow object, not a copy.

    ########################################################################
    #                      Source/Destinatino methods                      #
    ########################################################################

    def get_ips(self):
        """Return set of IP addresses"""
        return sorted([(str(ip), int(port)) for ip, port in self.ips])
        #It takes the ips set and turns it into a sorted list of (IP, port) pairs with clean types.
        # It does three things in one line

    def src(self):
        """Return source IP of flow."""
        (x_ip, x_port), (y_ip, y_port) = self.get_ips()
        #That’s unpacking, also called destructuring. It takes the list returned by get_ips()
        # and assigns its parts to four variables in one step.


        # If both IP addresses are private
        if ipaddress.ip_address(x_ip).is_private and\
           ipaddress.ip_address(y_ip).is_private:
        #ip_address is a function, you give it a string and it returns an object.
        #The object is an instance of one two classes from the
        #ipaddress module chosen by the string you pass. That object stores the address internally
        #as a number and has lots of built-in properties e.g is_private
        #is_private is a property,

        #how does is_private work:
        #The library turns the string into a number and
        #then checks that number against a list of reserved ranges.

            # Return address with highest port
            return x_ip if x_port > y_port else y_ip
            # Ports first. An IP address identifies a device.
            # A port is a number from 0 to 65535 that identifies a specific program or
            # connection on that device.

            #We don't know whether x is the client or y is, checking which port is bigger helps us find out.
            #The server waits on a fixed, usually low port (443, 80, 53) so clients know where to connect.
            # The client gets a random high port from its operating system for each new connection (e.g. 51234).

        # Return non-private address
        return x_ip if ipaddress.ip_address(x_ip).is_private else y_ip
        #In flows.py, public IPs don’t get any handling of their own.
        # They’re simply whatever is left over after the private checks.

    def dst(self):
        """Return destination IP of flow."""
        (x_ip, x_port), (y_ip, y_port) = self.get_ips()

        # If both IP addresses are private
        if ipaddress.ip_address(x_ip).is_private and\
           ipaddress.ip_address(y_ip).is_private:
            # Return address with lowest port
            return y_ip if x_port > y_port else x_ip

        # Return non-private address
        return y_ip if ipaddress.ip_address(x_ip).is_private else x_ip

    def sport(self):
        """Return source port of flow."""
        (x_ip, x_port), (y_ip, y_port) = self.get_ips()

        # If both IP addresses are private
        if ipaddress.ip_address(x_ip).is_private and\
           ipaddress.ip_address(y_ip).is_private:
            # Return highest port
            return max(x_port, y_port)

        return x_port if ipaddress.ip_address(x_ip).is_private else y_port

    def dport(self):
        """Return destination port of flow."""
        (x_ip, x_port), (y_ip, y_port) = self.get_ips()

        # If both IP addresses are private
        if ipaddress.ip_address(x_ip).is_private and\
           ipaddress.ip_address(y_ip).is_private:
            # Return lowest port
            return min(x_port, y_port)

        return y_port if ipaddress.ip_address(x_ip).is_private else x_port

    def source(self):
        """Returns source of Flow."""
        return (self.src(), self.sport())

    def destination(self):
        """Returns destination of Flow."""
        return (self.dst(), self.dport())

    def certificate(self):
        """Returns certificate of Flow."""
        return list(self.certificates)[0] if self.certificates else None

    def time_start(self):
        """Returns start time of Flow."""
        return min(self.timestamps)

    def time_end(self):
        """Returns end time of Flow."""
        return max(self.timestamps)

    ########################################################################
    #                           Class overrides                            #
    ########################################################################

    def __len__(self):
        """Return length of Flow in packets."""
        return len(self.lengths)
        #counts the items in self.lengths and returns an integer

    def __str__(self):
        """Return string representation of flow."""
        return "[Time {} to {}] {:>15}:{:<5} <-> {:>15}:{:<5} [Length {}]".format(
            datetime.fromtimestamp(min(self.timestamps)).strftime("%H:%M:%S.%f"),
            datetime.fromtimestamp(max(self.timestamps)).strftime("%H:%M:%S.%f"),
            self.src(), self.sport(), self.dst(), self.dport(),
            len(self))

    #other is the parameter name for another flow object
    def __gt__(self, other):
        """Greater than object override"""
        return min(self.timestamps) >  min(other.timestamps)
        #So when greater than is called, it compares the timestamps of two Flows

    def __ge__(self, other):
        """Greater equals object override"""
        return min(self.timestamps) >= min(other.timestamps)

    def __lt__(self, other):
        """Less than object override"""
        return min(self.timestamps) <  min(other.timestamps)

    def __le__(self, other):
        """Less equals object override"""
        return min(self.timestamps) <= min(other.timestamps)

########################################################################
#                         Flow combiner object                         #
########################################################################

#another class in the Flows.py module.
class Flows(object):

    def combine(self, packets):

    #takes in two parameters, a list of individual packets, and a flow object
        """Combine individual packets into a flow representation.

            Parameters
            ----------
            packets : np.array of shape=(n_samples_packets, n_features_packets)
                Output from Reader.read

            Returns
            -------
            flows : np.array of shape=(n_samples_flows, n_features_flows)
                Numpy array grouped together as flows.
            """
        # Initialise result
        result = dict()
        #It creates an empty dictionary called result,
        #which will collect the flows.

        #a dict stores key → value pairs.
        #You look things up by key instead of by position:

        # For each packet, add it to a flow
        for packet in packets:
            #Keys have to be unique: assigning to an existing key replaces its value.
            # Like set items, keys must be hashable (strings, numbers, tuples).
            key = (packet[0], packet[1], packet[2])
            #Reader.read() returns a 2D array, Each row is a packet,
            #and each packet has 10 columns. The columns serve as attributes
            #for the packets.



            #Key: the tuple (filename, protocol, stream ID),
            # which identifies one conversation(flow).

            # Many packets share the same key.
            # Every packet in TCP stream 3 of 1.pcap produces the same tuple ("…/1.pcap", "tcp", "3").
            # So the dictionary ends up with one entry per flow

            # Value: the Flow object for that conversation.

            # Add packet to flow
            result[key] = result.get(key, Flow()).add(packet)
            #.get() is a dictionary method that looks up a key, and a returns a value
            #with a fallback

            #So if there is a value(an existing flow) at result[key], a packet is added to that flow
            #If not a new flow created and then the packet gets added
        # Return result
        return result
