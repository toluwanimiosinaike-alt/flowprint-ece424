from sklearn.model_selection import train_test_split, KFold
#That line imports two tools from scikit-learn,
# the standard Python machine-learning library.
# Its model_selection module holds utilities for dividing data so you can evaluate a model fairly.
#train_test_split randomly splits your data into a training set and
# a test set in one call.
#KFold sets up k-fold cross-validation.
# It cuts the data into k equal chunks ("folds").
# Each fold takes one turn as the test set while
# the other k−1 folds are used for training.
from sklearn.utils import check_random_state
# check_random_state takes whatever you pass as a "random state"
# and gives back a proper NumPy random number generator object (np.random.RandomState).
# That lets the rest of the code use randomness the same way
# no matter what form the seed came in.
import numpy as np




class Splitter(object):

    def __init__(self, random_state=42):
        """Splitter object for splitting flows.

            Parameters
            ----------
            random_state : int, default=42
                Random state for reproducable splitting.
            """
        #the random_state you pass in (42 by default) goes to check_random_state.
        # That returns a RandomState generator,
        # which is stored on the object as self.rs
        self.rs = check_random_state(random_state)

    def split_labels(self, X, y, size_known=1/2):
        """Split labels into known and unknown.
            You need both test sets.
            Good results on the known test alone only prove FlowPrint works in a "closed world."
            The unknown test checks whether it can tell when something new appears.

            Parameters
            ----------
            X : np.array of shape=(n_samples, n_features)
                Samples on which to split.

            y : np.array of shape=(n_samples,)
                Labels on which to split.

            size_known : float, default=1/2
                Proportion of samples to return as known_test indices.

            Return
            ------
            X_known : np.array of shape=(n_samples, n_features)
                Known data

            y_known : np.array of shape=(n_samples,)
                Known labels

            X_unknown: np.array of shape=(n_samples, n_features)
                Known undata

            y_unknown: np.array of shape=(n_samples,)
                Unknown labels
            """
        # Get data as numpy array
        y = np.asarray(y)
        #It converts y into a NumPy array, whatever form it arrived in.
        X = np.asarray(X)

        # Randomly select known and unknown labels
        """
        unknown, known = train_test_split(np.unique(labels),
                                          test_size=size_known,
                                          random_state=self.rs)
        """
        unknown, known = train_test_split(np.unique(y),
                                          test_size=size_known,
                                          random_state=self.rs)
        #np.unique(labels) builds the list of apps.
        # Your labels have one entry per flow,
        # so app names repeat many times. np.unique reduces that to each app once (sorted)

        #test_size sets how much of the list goes into the second array that train_test_split returns.
        # The first array gets everything else.

        #train_test_split doesn't just cut the list in place.
        # It shuffles the list first, then takes the cut.

        #random_state controls the shuffle,
        # which decides which apps those are

        # Return known and unknown labels
        return X[np.isin(y,   known)], y[np.isin(y,   known)],\
               X[np.isin(y, unknown)], y[np.isin(y, unknown)]
        #np.isin(y, known) checks each label in y against the known array
        # and returns a boolean NumPy array of the same length as y.
        # Each element is True if that label appears in known
        # and False if it doesn't.
        # X[mask] walks through the positions and keeps X[i] wherever mask[i] is True.
        # Reducing the list of flow objects

        #The function returns one tuple that holds the four arrays.
        #Python packs comma-separated return values into a tuple,

    def k_fold_label(self, X, y, k, rs=42, max_labels=None):
        """Generator: splits the data into different k-folds according to label.

            Parameters
            ----------
            X : np.array of shape=(n_samples, n_features)
                Samples on which to split.

            y : np.array of shape=(n_samples,)
                Labels on which to split.

            k : int
                Number of splits to make.

            rs : int, default=42
                Random state

            max_labels : int, optional
                If given, return a maximum number of labels per k-fold.

            Yields
            ------
            X : np.array of shape=(n_samples,)
                Samples in given k-fold.

            y : np.array of shape=(n_samples,)
                Labels in given k-fold.
            """
        # Get random state
        rs = check_random_state(rs)
        #rs is now the generator.

        # Get unique labels
        labels = np.unique(y)
        # Split into k-folds
        #the randomState generator object is passed as a random_state
        #So kfold_safe just relays KFold's folds one at a time.
        #it only ever produces (train_indices, test_indices) pairs.
        for train, test in self.kfold_safe(k, labels, random_state=rs):
            # get labels for k-fold
            # pull up the actual app names out of labels. The
            # result is the list of apps included in this fold.

            labels_kfold = labels[train]
            # In case of max_labels, randomly select maximum number of labels.
            if max_labels is not None and max_labels <= labels_kfold.shape[0]:
                # Randomly select max_labels of labels
                labels_kfold = rs.choice(labels_kfold, size=max_labels, replace=False)
                """
                 - rs.choice(...) is the generator's "pick at random" method. 
                 Because it's called on rs, the picks come from the seeded generator, 
                 so the same seed gives the same max_labels apps on every fresh run.
                 - labels_kfold (first argument) is the pool to pick from.
                 - size=max_labels is how many to pick.
                 - replace=False means without replacement: once an app is picked, 
                 it can't be picked again. 
                 With replace=True you could get ['h','h','c','j','h'], 
                 and duplicate apps would make no sense here.
                 - labels_kfold = ... overwrites the old 8-app array with the new max_labels-app one. 
                 The next line, np.isin(y, labels_kfold), 
                 therefore only keeps flows from those max_labels apps.
                """

            # Get mask for given k-fold
            mask = np.isin(y, labels_kfold)
            #builds a boolean mask over the labels in y
            # Yield data
            yield X[mask], y[mask]
            #returns the flow objects and labels chosen by the boolean mask


    def kfold_safe(self, k, data, random_state):
        """A safe method for requesting K-folds, also covers k=1.

            Parameters
            ----------
            k : int
                Number of folds. Meaning how many times the experiment
                is repeated on different groups of apps.

                For example: If we have 10 apps and k = 5

                Apps: A B C D E F G H I J
                Chunks: [A B] [C D] [E F] [G H] [I J]

                Fold 1: test = A B    train = C D E F G H I J
                Fold 2: test = C D    train = A B E F G H I J
                Fold 3: test = E F    train = A B C D G H I J
                Fold 4: test = G H    train = A B C D E F I J
                Fold 5: test = I J    train = A B C D E F G H

            data : np.array of shape=(n_samples, n_features)
                Data on which to perform kfold split.

            random_state : int, default=42
                Random state.

            Yields
            ------
            train : np.array of shape=(n_samples, n_features)
                Data """
        if k < 2:
            #produces one (train, test) pair where every app is in train
            # and nothing is in test

            #np.arange generates a one-dimensional NumPy array containing evenly spaced values
            # For example
            # np.arange(5)
            # Output: array([0, 1, 2, 3, 4])
            #these are the train indices

            #np.zeros(0) makes an array of zeros with length 0, which is an empty array
            #This is the test side

            #yield hands a value back to whoever is looping over the function,
            # then pauses the function where it is.

            #In Python, the comma is what makes a tuple

            yield np.arange(data.shape[0]), np.zeros(0)
        else:
            #KFold(k, random_state=random_state) creates a KFold object.
            #It's like a configured splitter that knows "make k folds, using this generator for randomness."
            # No splitting has happened yet.

            #split(data) produces the folds. It's a generator that yields one (train, test) pair per fold.
            # Each pair is two arrays of index positions into data

            #Going back to the example of 10 apps and k = 5.
            #KFold(k, random_state=random_state).split(data) is still an object
            # When you loop over it or wrap it in list(), it gives you 5 tuples. Each tuple holds two NumPy
            #arrays of integer index positions: 8 train indices and 2 test indices.
            for train, test in KFold(k, random_state=random_state).split(data):
                # yield hands a value back to whoever is looping over the function,
                # then pauses the function where it is.
                yield train, test



    def split(self, X, y, size_known=1/2, size_train=1/2):
        """ Get indices of train, known_test and unknown_test data.
            I.e. labels in known_test may appear in train data, whereas
            labels in unknown_test will not appear in train data. This
            implementation splits the data on a temporal level, i.e. all
            training instances occur before testing instances.

            Note that ratios are approximate as the numer of labels has
            influence on the final result.

            Parameters
            ----------
            X : np.array of shape=(n_samples, n_features)
                Samples on which to split.

            y : np.array of shape=(n_samples,)
                Labels on which to split.

            size_known : float, default=1/2
                Proportion of samples to return as known_test indices.

            size_unknown : float, default=1/4
                Proportion of samples to return as unknown_test indices.

            Returns
            -------
            indices_train : np.array
                Indices of samples and labels in training set.

            indices_known : np.array
                Indices of samples and labels in known testing set.

            indices_unknown : np.array
                Indices of samples and labels in unknown testing set.
            """
        # Get data as numpy array
        y = np.asarray(y)
        X = np.asarray(X)

        # Initialise results
        X_train     , y_train      = list(), list()
        X_test_known, y_test_known = list(), list()

        # Get unique labels
        labels = np.unique(y)
        # Split labels in known and unknown
        labels_unknown, labels_known = train_test_split(labels,
                                            test_size=size_known,
                                            random_state=self.rs)

        ####################################################################
        #                       Set unknown dataset                        #
        ####################################################################
        # Compute mask for unknown data
        mask_test_unknown = np.isin(y, labels_unknown)
        # Set unknown sets
        X_test_unknown = X[mask_test_unknown]
        y_test_unknown = y[mask_test_unknown]

        ####################################################################
        #                        Set known dataset                         #
        ####################################################################
        # Compute masks for known & unknown data
        #line of code isn't needed
        mask_known   = np.isin(y, labels_known)

        # Split known data in train and test sets
        #It builds an array with one start time per flow: the timestamp of each flow's first packet.
        # That array is what split() uses to put earlier flows in train and later flows in test.

        #x is a single flow.
        # X is an array of Flow objects,
        # and the for x in X part visits them one at a time.

        #x.timestamps is that flow's list of packet times.
        # A flow is a conversation between the phone and one server,
        # made up of many packets,
        # and each packet was captured at a particular moment:

        #min(x.timestamps) is the earliest of those times, which is when the flow started.

        timestamps = np.array([min(x.timestamps) for x in X])
        # For each application in known, split data in train and test
        for application in labels_known:

            # Create mask for application
            #in each iteration, application holds one of item in labels_known
            #and that item is checked against the whole y list.
            #mask_app is a boolean list(true for the application found in y, false otherwise)
            mask_app = y == application
            # Get timestamp on which to split
            #form a number split based on the 50th percentile of timestamps
            split = np.percentile(timestamps[mask_app], 100*size_train)
            # Set train and test data for given application
            #First a set of timestamps are chosen based on the mask_app mask.
            #Picking only the timestamps that correspond to the flows which characterize the label.
            #that has been picked for this iteration
            #Then another mask(a boolean list of trues and falses), is created using the split
            #condition. the ones less than split are labeled true, and the ones greater are false
            train = timestamps[mask_app] <= split
            test  = ~train

            # Add train data and labels
            #two masks are applied to truncate the flows and the labels of this iteration
            X_train.append(X[mask_app][train])
            y_train.append(y[mask_app][train])

            # Add test data and labels
            X_test_known.append(X[mask_app][test])
            y_test_known.append(y[mask_app][test])
            # and with each iteration, you the lists grow bigger.

        # Combine train and test data
        X_train      = np.concatenate(X_train)
        y_train      = np.concatenate(y_train)
        X_test_known = np.concatenate(X_test_known)
        y_test_known = np.concatenate(y_test_known)

        # Return result
        return X_train       , y_train,\
               X_test_known  , y_test_known,\
               X_test_unknown, y_test_unknown

    def split_normal(self, X, y, size_known=1/2, size_train=1/2):
        # Get data as numpy array
        y = np.asarray(y)
        X = np.asarray(X)

        # Initialise results
        X_train     , y_train      = list(), list()
        X_test_known, y_test_known = list(), list()

        # Get unique labels
        labels = np.unique(y)
        # Split labels in known and unknown
        labels_unknown, labels_known = train_test_split(labels,
                                            test_size=size_known,
                                            random_state=self.rs)

        # Get mask unknown
        mask_unknown = np.isin(y, labels_unknown)
        X_test_unknown = X[mask_unknown]
        y_test_unknown = y[mask_unknown]

        # Get mask known
        mask_known = ~mask_unknown
        # Split train test of known
        X_train, X_test_known, y_train, y_test_known = \
            train_test_split(X[mask_known], y[mask_known],
                             test_size=1-size_train, random_state=self.rs)

        # Return result
        return X_train       , y_train,\
               X_test_known  , y_test_known,\
               X_test_unknown, y_test_unknown
