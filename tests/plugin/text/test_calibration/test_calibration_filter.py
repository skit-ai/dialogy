import numpy as np
import pytest
from scipy import sparse

from dialogy import constants as const
from dialogy.plugins.text.calibration.xgb import CalibrationModel
from dialogy.workflow.workflow import Workflow
from tests import EXCEPTIONS, load_tests


class MyVectorizer(object):
    def __init__(self):
        pass

    def transform(self, text):
        assert isinstance(text, list)
        return sparse.csr_matrix(np.array([1]))


class MyClassifier(object):
    def __init__(self):
        pass

    def predict(self, X):
        return np.array([1])


vectorizer = MyVectorizer()
classifier = MyClassifier()
