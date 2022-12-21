from abc import ABC, abstractmethod
from ElectionProfile import EPSILON

class Eta(ABC):

    @abstractmethod
    def __init__(self, u, initial_eta):
        """
        :param u: Upper bound of the assorter
        :param initial_eta: Initial value for the alternative hypothesis (the prior)
        """
        self.eta_0 = initial_eta
        self.value = min(initial_eta, u - EPSILON)
        self.u = u
        self.total_ballots = 0
        self.assorter_sum = 0

    @abstractmethod
    def calculate_eta(self, samples, assorter_value, mu):
        pass