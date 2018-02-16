import shutil
import tempfile
import unittest

import numpy as np
import scipy.stats
from pymc3 import summary
from sklearn.model_selection import train_test_split

from pymc3_models.exc import  PyMC3ModelsError
from pymc3_models import GaussianNaiveBayes



class GaussianNaiveBayesTestCase(unittest.TestCase):
    def setUp(self):
        """ Set up a test case with synthetic data.
        """

        self.num_cats = 3
        self.num_features = 10
        self.num_samples = 100000
        
        # Generate data
        ## Priors
        alpha = np.ones(self.num_cats)
        pi = np.random.dirichlet(alpha)
        mu = np.random.normal(0, 100, size=(self.num_cats, self.num_features))
        sigma = scipy.stats.halfnorm(loc=0, scale=100).rvs(size=(self.num_cats, self.num_features))
        ## Data
        Y = np.random.choice(range(self.num_cats), self.num_samples, p=pi)
        x_vectors = []
        for i in Y:
            x_vectors.append(np.random.normal(mu[i], sigma[i]))
        X = np.vstack(x_vectors)
        
        
        # Split into train/test sets
        split = train_test_split(X, Y, test_size=0.4)
        self.X_train = split[0] 
        self.X_test= split[1]
        self.Y_train = split[2]
        self.Y_test = split[3]

        self.test_GNB = GaussianNaiveBayes()
        self.test_dir = tempfile.mkdtemp()
        
        # Fit the model once and for all
        self.test_GNB.fit(self.X_train, self.Y_train, minibatch_size=2000)

    def tearDown(self):
        """ Tear down the testing environment.
        """
        shutil.rmtree(self.test_dir)


# Test fit
class GaussianNaiveBayesFitTestCase(GaussianNaiveBayesTestCase):
    def test_fit_returns_correct_model(self):
        """ Test the model initialization and fit

        Currently, only the sign of infered parameters is checked
        against the sign of the parameters used to generate the data.

        This is, however, not ideal. It is necessary to find better 
        strategies to test probabilistic code.
        """

        print('') # Berk
        
        # Check that the model correctly infers dimensions
        self.assertEqual(self.num_cats, self.test_GNB.num_classes)
        self.assertEqual(self.num_samples, self.test_GNB.num_samples)
        self.assertEqual(self.num_features, self.test_GNB.num_features)

        # TODO: How do you write tests for a stochastic mode?
        # TODO: Diagnose the sampling with a reasonable sampling size?
        np.testing.assert_equal(
            np.sign(self.pi),
            np.sign(self.test_GNB.trace['pi'].mean(axis=0))
            )

        np.testing.assert_equal(
            np.sign(self.sigma),
            np.sign(self.test_GNB.trace['sigma'].mean(axis=0))
            )


class GaussianNaiveBayesPredictProbaTest(GaussianNaiveBayesTestCase):
    """ Test the predict_proba() method.
    """
    def test_predict_proba_returns_probabilities_and_std(self):
        """ Test the shape of the predicted probabilities and std.
        """
        print('')
        probs, stds = self.test_GNB.predict_proba(self.X_test, return_std=True)
        self.assertEqual(probs.shape, self.Y_test.shape)
        self.assertEqual(stds.shape, self.Y_test.shape)


    def test_predict_proba_raises_error_if_not_fit(self):
        """ Test that an error is raised when you try to make predictions before fitting the model.
        """
        with self.assertRaises(PyMC3ModelsError) as no_fit_error:
            test_GNB = GaussianNaiveBayes()
            test_GNB.predict_proba(self.X_train, self.Y_train)

        expected = 'Run fit on the model before predict' # precarious, define a new Exception type
        self.assertEqual(str(no_fit_error.exception), expected)


class GaussianNaiveBayesPredictionTestCase(GaussianNaiveBayesTestCase):
    """ Test the predict() method.
    """
    def test_predict_returns_predictions(self):
        """ Test that the predict() function's  output has the correct shape.
        """
        print('')
        preds = self.test_GNB.predict(self.X_test)
        self.assertEqual(preds.shape, self.Y_test.shape)


class GaussianNaiveBayesScoreTestCase(GaussianNaiveBayesTestCase):
    """ Test the score() method.
    """
    def test_score_scores(self):
        print('')
        score = self.test_GNB.score(self.X_test, self.Y_test)
        # What to test for?

class GaussianNaiveBayesSaveAndLoadTestCase(GaussianNaiveBayesTestCase):
    """ Test the save() and load() method.
    """
    def test_save_and_load_work_correctly(self):
        print('')
        probs1 = self.test_GNB.predict_proba(self.X_test)
        self.test_GNB.save(self.test_dir)

        GNB2 = GaussianNaiveBayes()

        GNB2.load(self.test_dir)
