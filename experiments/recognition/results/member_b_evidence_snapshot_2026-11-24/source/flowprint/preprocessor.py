from flows import Flows
from reader import Reader
import numpy as np
import pickle
#pickle saves Python objects to a file and loads them back later.
# This is called serialization. Saving a plain list or dict to a file normally means
# converting it to text yourself. Pickle instead writes the object as bytes and
# rebuilds it exactly when you load it.
#/usr/local/lib/python3.13/pickle.py
import sys
#sys lets your code interact with the Python
# interpreter and the system it’s running on.
#both pickle and sys are two modules
# from Python's standard library.
class Preprocessor(object):

    ########################################################################
    #                         Class initialisation                         #
    ########################################################################

    def __init__(self, verbose=False):
        """Preprocessor object for preprocessing flows from pcap files."""
        #these objects are initialized in the constructor,
        #so that every other method in Preprocessor can use them
        # Initialise Reader object
        self.reader = Reader(verbose)
        # Initialise Flow object
        self.flows  = Flows()

    ########################################################################
    #                       Process files and labels                       #
    ########################################################################

    def process(self, files, labels):
        """Extract data from files and attach given labels.

            Parameters
            ----------
            files : iterable of string
                Paths from which to extract data.

            labels : iterable of int
                Label corresponding to each path.

            Returns
            -------
            X : np.array of shape=(n_samples, n_features)
                Features extracted from files.

            y : np.array of shape=(n_samples,)
                Labels for each flow extracted from files.
            """
        # Initialise X and y
        X, y = list(), list()

        # Loop over all given files
        #This line loops over two lists at the sametime, taking one item
        #from each on every pass.
        for file, label in zip(files, labels):
        #So zip gives back a sequence of pairs: the first file with the first label,
        # the second with the second, and so on.
            # On exit, exit for loop
            try:
                data = np.array(list(self.extract(file).values()))
                #self.extract(file). returns a dictionary of flow_key → flow.
                # The key identifies the conversation (its IPs, ports, and so on),
                # and the value is the Flow object holding its packets.

                #.values() is a built-in dictionary method. It gives you the values from a dictionary
                #and leaves out the keys.
                #It returns a special “view” object (dict_values),
                # not a real list.

                #wrapping all that with list(), turns what we got previously
                #into a list of flow objects

                #np.array(...) takes the plain list of Flow objects and
                # turns it into a NumPy array
            except KeyboardInterrupt:
                #This catches you pressing Ctrl+C.
                # Normally Ctrl+C kills the program.
                # Here it just stops the loop early,
                # and the code moves on to combine and
                # return whatever was processed before you pressed it.
                break
            #One bad pcap file shouldn't ruin the whole run. Flowprint datasets
            #can have thousands of pcaps, and preprocessing can take hours. Without the
            #try an error in any single file would crash the program and throw away everything processed so far.
            except Exception:
            #print a message then continue.
            #The code prints which file failed
            #and continue skips to the next file.
                print("Reading {} failed".format(file), file=sys.stderr)
                #file = sys.stderr tells print where to send its text.
                #sys.stdout, the normal output stream. file=sys.stderr sends
                # the text to the error stream instead.
                import traceback
                #traceback is another module from Python’s standard library.
                #It lets you print or save the full error report for an exception
                traceback.print_exc()
                continue
            # Append data to X
            X.append(data)
            # Append label to y
            y.append(np.array([label] * data.shape[0]))
            #data.shape[0] is the number of flows.
            #data is the NumPy array of Flows from this pcap
            #.shape gives its dimensions, and [0] is the first dimension
            #, the number of items.

            #multiplying a list by n, repeats the list n times.
            #The square brackets matter.
            # "appA" * 4 would repeat the string and give "appAappAappAappA".
            # Wrapping it in [...] makes it a one-item list,
            # so the whole item gets repeated.

            #A pcap files which eventually gets processed into a list of flows,
            #has one label(the folder the file is found in)

            #X and y must line up position by position:
            # y[i] has to be the label for flow X[i].
            # All flows in one pcap come from the same app,
            # so each one gets that file’s label

            #X and y will receive a new set of lists everytime the loop
            #goes through an iteration



        # Filter empty entries from array
        X = list(filter(lambda x: x.shape[0] != 0, X))
        #This lines removes empty arrays from X, meaning pcap files that produced zero flows
        #At this point, X is a list  with one array per pcap file

        #lambda is just a shortcut for writing a one-line function in place.
        #lambda x: x.shape[0] != 0 is the same as
        # -->
        #def keep(x):
        #   return x.shape[0] != 0   # True if the array has at least one item
        # -->
        #X (capital) is the whole list, one array per pcap file:
        #x (lowercase) is the function’s parameter:
        #one single item from that list, which means one file’s array of flows.
        y = list(filter(lambda x: x.shape[0] != 0, y))

        # Append both X and y
        try:
            #These two lines merge the separate per-file
            # arrays into one long array each.
            X = np.concatenate(X)
            y = np.concatenate(y)

        except Exception:
            #Those two lines create empty NumPy arrays.
            # They’re the fallback in the except branch,
            # used when np.concatenate fails.
            X = np.array([], dtype=object)
            y = np.array([], dtype=object)
            #np.array([]) is an array with zero items, so X.shape[0] is 0.
            #dtype=object tells NumPy the array holds Python objects.
            # That matches what X and y normally hold: Flow objects and string labels.
            # Without it, NumPy would default to a float array, which is the wrong type.


        # Return result
        return X, y

    ########################################################################
    #                         Process single file                          #
    ########################################################################

    def extract(self, infile):
        """Extract flows from given pcap file.
        #infile in this method is a file in the process method.
        #Which is just one pcap file.
            Parameters
            ----------
            infile : string
                Path to input file.

            Returns
            -------
            result : dict
                Dictionary of flow_key -> flow.
            """
        # Read packets
        #A pcap file is passed into read() and it returns
        # a list of packets
        result = self.reader.read(infile)
        # Combine packets into flows
        #The list of packets is passed into combine
        #which returns a dicitonary of flows
        result = self.flows.combine(result)
        # Return result
        return result

    ########################################################################
    #                             I/O methods                              #
    ########################################################################

    def save(self, outfile, X, y):
        """Save data to given outfile.

            Parameters
            ----------
            outfile is the path to the file itself, not just the folder.
            It ends in the file name
            e.g "results/flows.p"
            outfile : string
                Path of file to save data to.

            X : np.array of shape=(n_samples, n_features)
                Features extracted from files.

            y : np.array of shape=(n_samples,)
                Labels for each flow extracted from files.
            """
        #open(outfile, 'wb') opens (or creates)
        # the file at the path in outfile, such as "flows.p"
        #w: write. It creates the file, or overwrites it if it already exists.
        #b: binary. Pickle writes raw bytes, not text, so the file must be opened in binary mode.
        with open(outfile, 'wb') as outfile:
        #as outfile gives a name to the opened file so the next line can write to it:
        #When the indented block ends, with closes the file automatically,
        #whether or not an error happened.
            pickle.dump((X, y), outfile)
            #pickle.dump((X, y), outfile) converts the data into bytes and writes them to the file.
            #(X, y) is a tuple, so both arrays get saved together as one object.
    def load(self, infile):
        """Load data from given infile.

            Parameters
            ----------
            infile : string
                Path of file from which to load data.

            Returns
            -------
            X : np.array of shape=(n_samples, n_features)
                Features extracted from files.

            y : np.array of shape=(n_samples,)
                Labels for each flow extracted from files.
            """
        #open(infile, 'rb') opens the existing file at the path in infile,
        #such as "results/flows.p".
        #The 'rb' mode means:
        # r: read. The file must already exist, or you get a FileNotFoundError.
        # b: binary, because pickle files are raw bytes,
        # the same as when they were written with 'wb'.
        with open(infile, 'rb') as infile:
            #pickle.load(infile) reads the bytes and
            # rebuilds the exact Python objects that were saved
            # .save stored the tuple (X, y), so load gives that same tuple back,
            # including the arrays and the Flow objects inside them.
            return pickle.load(infile)

if __name__ == "__main__":
    preprocessor = Preprocessor(verbose=True)
    X, y = preprocessor.process('../data/ReCon/pcaps/at.ner.lepsWorld2/372.pcap')
    print(len(flows))
"""
    Python gives every file a built-in variable called __name__:
    If you run the file directly (python preprocessor.py), __name__ is set to "__main__", so the block runs.
    If another file imports it (from preprocessor import Preprocessor, as main.py does), __name__ is "preprocessor", so the block is skipped.
"""
