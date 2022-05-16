from math import sqrt
from Eta import Eta
from ElectionProfile import EPSILON

ADAPTIVE_ETA = "Adaptive"

class AdaptiveEta(Eta):
    def __init__(self, u, initial_eta, d, mu=0.5, c=None):
        """
        Adaptive alternative hypothesis for an ALPHA assertion
        :param u: Upper bound of the assorter
        :param initial_eta: Initial value for the alternative hypothesis (the prior)
        :param d: Effects the balance between the prior and the mean assorter value seen thus far. A larger value
        improves efficiency when the reported tally isn't accurate, and vice-versa.
        :param mu: Null hypothesis for the assorter mean.
        :param c: Effects the minimal distance that the alternative hypothesis (eta) must have from the null. As the
        number of samples grow, that minimal distance may shrink.
        """
        super().__init__(u, initial_eta)
        self.d = d
        self.mu = mu
        if c is None:
            self.c = (initial_eta - mu) / 2
        else:
            self.c = c
        self.assorter_sum = 0


    def calculate_eta(self, samples, assorter_value, mu):
        """
        Updates eta based on an additional number of samples.
        :param samples: Number of samples to update.
        :param assorter_value: The assorter mean over these samples.
        :param mu: null hypothesis regarding the assorter mean
        :return: Eta.
        """
        self.assorter_sum += assorter_value
        self.total_ballots += samples
        self.value = min(max((self.d*self.eta_0 + self.assorter_sum) / (self.d + self.total_ballots - 1), mu + EPSILON), self.u - EPSILON)
        return self.value