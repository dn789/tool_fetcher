import os

import pandas as pd
from sklearn import metrics
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import SelectFromModel

from get_posts.utils import get_web_page_features, get_post_set_features


def make_training_test_data(csv_path, test_prop=.1, type_='post_set'):
    """Splits data into training and test sets with labels.

    Parameters
    ----------
    csv_path : str
        Path to csv file with training data.
    test_prop : float, optional
        proportion of test data, by default .1
    return_features : bool, optional
        _description_, by default False

    Returns
    -------
    dictionary
        {
            'features' : list of features used in training,
            'train_data': X_train, y_train
            'test_data': X_test, y_test (or None if not test_prop)
        }
    """
    return_dict = {}
    df = pd.read_csv(csv_path)
    return_dict['features'] = list(df.columns)[1:]
    y_label = 'valid_post_set' if type_ == 'post_set' else 'page_with_posts'
    if test_prop:
        train, test = train_test_split(df, test_size=test_prop)
        y_train = train.pop(y_label).values
        y_test = test.pop(y_label).values
        return_dict['train_data'] = train, y_train
        return_dict['test_data'] = test, y_test
    else:
        y_train = df.pop(y_label).values
        return_dict['train_data'] = df, y_train
        return_dict['test_data'] = None
    return return_dict


def train_model(X_train, y_train):
    """
    Parameters
    ----------
    X_train : pandas.core.frame.DataFrame
        training input samples (from make_training_data)
    y_train : numpy.ndarray
        target values (from make_training_data)

    Returns
    -------
    sklearn RandomForestClassifier
    """
    clf = RandomForestClassifier(n_estimators=100)
    clf.fit(X_train, y_train)
    return clf


class Classifier():
    """Random forest ensemble model created from data in csv_path.

    Parameters
    ----------
    csv_path : str
        Path to csv file with training data.
    type_ : str
        'web_page' or 'post_set'
    test_data_prop: float
        Reserves this proportion of samples as test data, tests model and saves accuracy
        score in self.accuracy

    Attributes
    ----------
    Model.name : the name of the csv file.
    Model.features : a list of the features used to train the model. Automatically
        used to extract features from post sets in Model.predict
    """

    def __init__(self, csv_path, type_, test_data_prop=0):
        self.type_ = type_
        self.name = os.path.basename(csv_path)[:-4]
        self.test_data_prop = test_data_prop
        train_dict = make_training_test_data(
            csv_path, test_prop=self.test_data_prop, type_=self.type_)
        self.features = train_dict['features']
        X_train, y_train = train_dict['train_data']
        self.model = train_model(X_train.values, y_train)

        if test_data_prop:
            X_test, y_test = train_dict['test_data']
            y_pred = self.model.predict(X_test.values)
            self.accuracy = metrics.accuracy_score(y_test, y_pred)

    def predict(self, url, full_html, full_text, posts=None):
        """Runs model on post set and associated html and text files.

        Parameters
        ----------
        full_text : str
            extracted full text of the associated web page. 
        full_html : str
            HTML of the associated web page
        posts : list of str
            extracted posts

        Returns
        -------
        1 or 0
            1 is a valid post set, 0 isn't. 
        """
        if self.type_ == 'web_page':
            feature_dict = get_web_page_features(
                url, full_text, full_html, feature_dict={}, features=self.features)
        elif self.type_ == 'post_set':
            feature_dict = get_post_set_features(
                full_text, full_html, posts, feature_dict={}, features=self.features)
        feature_list = list(feature_dict.values())
        pred, = self.model.predict([feature_list])
        return pred


def find_best_features(X_train, y_train, threshold='mean'):
    """Prints best features found in training model. 

    Parameters
    ---------- feature_dict['mean_descendant_count'] 
    X_train : pandas.core.frame.DataFrame
        training input samples (from make_training_data)
    y_train : numpy.ndarray
        target values (from make_training_data)
    threshold : str, optional
        threshold for inclusion as a best feature ('mean' or 'median') , by default 
        'mean'
    """
    sel = SelectFromModel(RandomForestClassifier(
        n_estimators=100), threshold=threshold)
    sel.fit(X_train, y_train)
    sel.get_support()
    selected_feat = X_train.columns[(sel.get_support())]
    print(selected_feat)


def get_model_accuracy(model, X_test, y_test):
    """
    Parameters
    ----------
    model : sklearn RandomForestClassifier
    X_test : pandas.core.frame.DataFrame
        training input samples (from make_training_data)
    y_test : numpy.ndarray
        target values (from make_training_data)
    """
    y_pred = model.predict(X_test.values)
    print("Accuracy:", metrics.accuracy_score(y_test, y_pred))
