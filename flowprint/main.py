from cc_graph import CrossCorrelationGraph
from collections import Counter
from cluster import Cluster
#Cluster is a class in cluster.py that is imported for the purpose
#of making Cluster objects in the main.py file.
from fingerprints import Fingerprints
from loader import Loader
from preprocessor import Preprocessor
from statistics import Statistics
#the same is true for everything above
from sklearn.metrics import accuracy_score, classification_report
from sklearn.metrics import completeness_score, homogeneity_score
from sklearn.metrics import v_measure_score
#the above e.g sklearn is package that doesn't come with flowprint,
#but one that was installed and placed in python installation
#we are different function from its metrics module.
#/usr/local/lib/python3.13/site-packages/sklearn/...
from sklearn.preprocessing import LabelEncoder
from split import Splitter
#Splitter is a class in split.py that is imported for the purpose
#of making Cluster objects in the main.py file.
import argparse
#It’s part of Python’s standard library, the modules that come with every Python installation.
# It’s a single file, argparse.py, that was installed along with Python.
#/usr/local/lib/python3.13/argparse.py
#Compare that with sklearn from earlier, Both are in Python’s lib folder,
# but argparse.py sits directly in it, next to os.py and pickle.py.
# That’s the standard library. sklearn sits one level deeper, inside site-packages/,
# because pip added it later.
import numpy as np
#numpy is not part of the standard library.
# It’s a third-party package you install with pip
#/usr/local/lib/python3.13/site-packages/numpy/__init__.py
#as gives the imported thing a different name in your file. np
import os
import pickle


def extract_labels(files):
    #files is a parameter which expects a list of pcap file paths
    # Initialise result
    result = list()#using the built-in python constructor to make a list

    for file in files:
        # Extract directory name
        result.append(os.path.split(os.path.dirname(file))[-1])
        #os is a module
        #os.path is a submodule: os.path is a clever trick where the os file imports
        #a completely separate file and attaches it to itself as an attribute.
        #It’s the part of os that works specifically with file paths
        #split is a function inside os.path. It splits a path into two pieces,
        # everything before the last / and the last part,
        # and returns them as a pair (a tuple)
        #dirname is short for directory name
        #It’s a function call that takes one file path and gives back the folder part.
    # Return result
    #collect ed all the folders of each pcap file and returned that list
    return result

if __name__ == "__main__":
    #So if this file is run directly, its name will be  "__main__",
    # but if it was imported, its name will be "main"
    #So the block of code starts with "if the main.py file is run directly"
    #then do the following
    ########################################################################
    #                           Parse arguments                            #
    ########################################################################

    # Create argument parser
    parser = argparse.ArgumentParser(description='Flowprint.')
    #ArgumentParser is a class int the argparse built-in module
    #and ArgumentParser object called parser is created, now we have freedom to use the methods in the class.
    parser.add_argument('-f', '--files', nargs='+', help='pcap files to run '
                                                   'through FlowPrint. We use '
                                                   'the  directory of each '
                                                   'file as label.')
    #add_argument sets up the rules for what input is allowed.
    #every value that comes after -f or --files in the command line, is stored in args.files
    #nargs = '+' means one or more. Everything after -f up to the next option is collected into a list
    #There’s no type=..., so each value stays a string, which suits file paths.
    #help prints text for user assistance
    parser.add_argument('-s', '--save', help='Save preprocessed data to given '
                                       'file.')
    #All the pcap files you give with -f are processed together into one set of data
    #Whatever you type after -s becomes the name of the file the data is saved to.
    #the variable holding the name is stored in args.save
    #the processed file saved in the folder your terminal is currently in
    parser.add_argument('-l', '--load', nargs='+', help='load preprocessed data'
                                                        'from given file.')
    #This is the partner of --save. It loads data you processed and saved earlier, so the program can skip reading the pcaps.
    #-l or --load, stored as args.load.
    #nargs='+', so one or more file names, collected into a list
    #there is not type, so each value is saved as a string
    #--load expects the kind of file --save creates.
    parser.add_argument('-r', '--random', type=int, help='Random state to use '
                                                 'for splitting data. '
                                                 '(default=42)')
    #accepts an integer(random seed) which is stored as args.random, which is used to decide which of the data
    #goes into the training group, and which data goes into the test group.
    #comeback to this later
    parser.add_argument('-t', '--test', type=float, help='Portion of data to be'
                                                   ' used for testing. All '
                                                   'other data is used for '
                                                   'training. (default=0.33)')
    #takes in a float(decimal number), decides how much data goes into the test group.
    #e.g 80/20, 60/40

    parser.add_argument('-p', '--stats', action='store_true', help='If flag is '
                                                 'set, output data statistics.')
    #it’s an on/off flag. Including -p asks the program to print statistics about the dataset instead of running the full experiment.
    #-p or --stats, stored as args.stats.
    #(The short letter doesn’t have to match the long name. -s was already taken by --save, so they used -p, probably for “print.”)
    # action='store_true': this is what makes it a flag. It takes no value after it:
    # -p included → args.stats is True
    # -p left out → args.stats is False



    # Parse given arguments
    args = parser.parse_args()
    #It’s the moment the parser reads what you typed and turns it into values the program can use.
    #All the add_argument lines before it only set up the rules. This line applies them.
    # When parser.parse_args() runs, it:
    #
    # Takes the words after main.py: ['--load', 'processed.p', '--random', '7']
    # Matches them to the rules: --load collects one or more values, --random takes one value as an int.
    # Converts types: '7' (text) becomes 7 (a number).
    # Fills in everything you didn’t type: None for options, False for the -p flag.
    # Checks for mistakes: a misspelled option or -r abc stops the program with an error message.

    # Returns a Namespace object holding all the results(args.files, args.save, args.load,e.tc).

    #Yes, exactly. args is a Namespace object holding one value per option.

    ########################################################################
    #                          Preprocessing step                          #
    ########################################################################

    # Initialise preprocessor
    preprocessor = Preprocessor(verbose=True)

    #main.py imported the Preprocessor class at the top, and this line creates an object from it:

    #In programming, a verbose setting is an on/off switch
    # for whether the program prints progress messages while it works.
    # It doesn’t change the results, only how much it tells you along the way.

    # Parse files if required
    #meaning if any files were given with -f, do the indented code below.
    if args.files:
        # Extract files and labels
        files  = args.files
        #gives the list a different name
        labels = extract_labels(args.files)
        #gets the folder each file is in and makes that the label.

        # Load data
        X, y = preprocessor.process(files, labels)
        #It’s the step that turns your pcap files into the data FlowPrint uses.
        #X is one long list of every flow from every pcap, all joined together.
        #It isn’t grouped by file.
        #a flow is one connection: source and destination IPs, ports, timestamps, packet sizes, TLS certificate
        #y is one label per flow, in the same order as X.

        # Save preprocessed data if necessary

        #if there was a name typed in after -s.
        if args.save:
            preprocessor.save(args.save, X, y)
            #take the data from the lists X and y and save a file with the name found in args.save
            #All the pcaps you pass with -f are processed together into one X and one y, and save writes
            # that pair into a single file, whatever name you gave after -s.
            exit()
            #Because the author designed --save as a “prepare the data only” mode.
            # Once the data is saved, the job you asked for is done, so the program stops
            # instead of running the rest.

    # Load data if necessary
    #if the user types in any preprocessed files that need to be loaded,
    if args.load:
        #Does any of the file names given to --load contain the word ‘andrubis’?”
        # If yes, the code uses the special Andrubis loader.
        if any('andrubis' in x.lower() for x in args.load):
            loader = Loader('../data/Andrubis/appdict.p')
        else:
            loader = Loader()
            #loader object is created from the Loader class.

        X, y = loader.load_files(args.load)
        #Once the Loader object is created, its load_files method reads the preprocessed file
        #and unpacks it back into X (the flows) and y (their labels)

        #X and y are NumPy arrays, not plain Python lists. They behave much like lists

    ########################################################################
    #                   Get data statistics if required                    #
    ########################################################################
    # Check if stats flag has been set
    if args.stats:

        # Check fingerprint stats
        # A fingerprint is what FlowPrint produces from flows later in the pipeline
        with open('fingerprints.p', 'rb') as infile:
            fps, y = pickle.load(infile)

        # Create mapping
        mapping = dict()
        for fingerprint, label in zip(fps, y):
            mapping[fingerprint] = mapping.get(fingerprint, set()) | set([label])

        # Check uniqueness of fingerprints
        from itertools import combinations

        for fp1, fp2 in combinations(mapping.keys(), 2):
            score = fp1.compare(fp2)
            if score > 0.8:
                print(score)
                fp1.show()
                fp2.show()
                print('\n\n')

        with open('fingerprints_processed.p', 'wb') as outfile:
            pickle.dump((mapping, table), outfile)

        exit()


        # Create statistics object
        statistics = Statistics(X, y)
        statistics.app_detection_time(plot=True)
        print(statistics.plot_application_detection_time(500))
        print(statistics.report())

        # Output all statistics
        exit()

    ########################################################################
    #                  Remove low occurence applications                   #
    ########################################################################
    # from collections import Counter
    # occurences = Counter(y)
    #
    # indices = []
    # for app, count in occurences.items():
    #     if count >= 100:
    #         indices.extend(np.argwhere(y == app).flatten().tolist())
    #
    # X = X[indices]
    # y = y[indices]

    ########################################################################
    #                           Clustering step                            #
    ########################################################################

    # Create clustering object
    cluster = Cluster()
    #In FlowPrint, a cluster is a group of flows that all go to the same destination,
    #meaning the same server or online service.

    ########################################################################
    #                         Fingerprinting step                          #
    ########################################################################

    # Create Fingerprinter
    fingerprints = Fingerprints(cluster)
    #It creates one Fingerprints object, which is the fingerprint generator:
    #the tool that will make fingerprints.
    #fingerprints are built out of clusters

    #A fingerprint is FlowPrint’s way of identifying an app from its network traffic:
    #the set of destinations an app talks to together.

    # Train and predict with fingerprinter
    y_pred_fingerprints = fingerprints.fit_predict_fingerprints(X, y)
    #This one line runs the whole FlowPrint algorithm. It takes all your flows (X) and their labels (y), builds fingerprints,
    #and returns one fingerprint per flow, stored in y_pred_fingerprints
    y_pred_labels       = np.array([fp.label for fp in y_pred_fingerprints])
    #for fp in y_pred_fingerprints goes through the fingerprints one at a time (one per flow).
    #Each one is called fp in turn.
    #fp.label asks that fingerprint which app it belongs to. As you saw in fingerprint.py,
    # the clusters inside it “vote,” and the most common app wins

    #np.array(...) turns something like a list into a NumPy array,
    #a special list-like container from the numpy package.

    y_pred_fingerprints = np.array([hash(y_) for y_ in y_pred_fingerprints])
    #It turns each fingerprint into a plain number (an ID),
    #so the fingerprints can be scored with sklearn.

    ########################################################################
    #                               Evaluate                               #
    ########################################################################

    #This section scores how well FlowPrint did in Experiment 1,
    # by comparing its predictions with the true labels y

    # Compute metrics
    accuracy     = accuracy_score     (y, y_pred_labels)
    homogeneity  = homogeneity_score  (y, y_pred_fingerprints)
    completeness = completeness_score (y, y_pred_fingerprints)
    v_measure    = v_measure_score    (y, y_pred_fingerprints)

    # Print metrics
    print(classification_report(y, y_pred_labels, digits=4))
    print("Accuracy    : {:.4f}".format(accuracy))
    print("Homogeneity : {:.4f}".format(homogeneity))
    print("Completeness: {:.4f}".format(completeness))
    print("V-Measure   : {:.4f}".format(v_measure))

    ########################################################################
    #                            Anomaly setup                             #
    ########################################################################

    #It tests a different, harder question than the evaluate section:
    #can FlowPrint tell when traffic comes from an app it has never seen before?

    # Create splitter instance
    splitter = Splitter(args.random or 42) # Default = 42 otherwise use random

    # Split in train, test_known, test_unknown sets
    X_train, y_train,\
    X_test_known, y_test_known,\
    X_test_unknown, y_test_unknown = splitter.split_normal(X, y, size_train=4/5)

    # Create Fingerprinter
    fingerprints = Fingerprints(cluster)

    # Train fingerprinter
    fp_train = fingerprints.fit_predict_fingerprints(X_train, y_train)

    # Create mappings of fingerprints for fast search
    # TODO: document
    fp_train_dest = dict()
    fp_train_cert = dict()
    for fp in fp_train:
        for destination in fp.destinations:
            dsts = fp_train_dest.get(destination, set())
            dsts.add(fp)
            fp_train_dest[destination] = dsts
        for certificate in fp.certificates:
            certs = fp_train_cert.get(certificate, set())
            certs.add(fp)
            fp_train_cert[certificate] = certs

    # Predict fingerprinter
    fp_test_known   = fingerprints.fit_predict_fingerprints(X_test_known)
    fp_test_unknown = fingerprints.fit_predict_fingerprints(X_test_unknown)

    true_positives = 0
    true_negatives = 0
    false_positives = 0
    false_negatives = 0

    threshold = 0.5

    count = 0
    length = len(set(fp_test_known))
    for test in set(fp_test_known):
        count += 1
        print("{}/{}".format(count, length), end='\r')

        possible = set()
        for destination in test.destinations:
            possible |= fp_train_dest.get(destination, set())
        for certificate in test.certificates:
            possible |= fp_train_cert.get(certificate, set())

        for train in possible:
            if test.compare(train) >= threshold:
                true_positives += np.sum(fp_test_known == test)
                break
        else:
            false_negatives += np.sum(fp_test_known == test)


    count = 0
    length = len(set(fp_test_unknown))
    for test in set(fp_test_unknown):
        count += 1
        print("{}/{}".format(count, length), end='\r')

        possible = set()
        for destination in test.destinations:
            possible |= fp_train_dest.get(destination, set())
        for certificate in test.certificates:
            possible |= fp_train_cert.get(certificate, set())

        for train in possible:
            if test.compare(train) >= threshold:
                false_positives += np.sum(fp_test_unknown == test)
                break
        else:
            true_negatives += np.sum(fp_test_unknown == test)

    print("TP: {}".format(true_positives))
    print("TN: {}".format(true_negatives))
    print("FP: {}".format(false_positives))
    print("FN: {}".format(false_negatives))

    # RESULTS RECON
    # TP : 3623
    # TN : 19818
    # FP : 0
    # FN : 2384
    # ACC: 0.9076863504356244

    # RESULTS ANDRUBIS 20*.p
    # TP : 80436
    # TN : 30676
    # FP : 28307
    # FN : 8209
    # ACC: 0.7526485490557346

    # RESULTS ANDRUBIS 20{1,2,3,4,5}.p
    # TP : 21289
    # TN : 13086
    # FP : 6486
    # FN : 2774
    # ACC: 0.7526485490557346
