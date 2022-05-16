from abc import ABC, abstractmethod


class Eta(ABC):

    @abstractmethod
    def __init__(self, u, initial_eta):
        """
        :param u: Upper bound of the assorter
        :param initial_eta: Initial value for the alternative hypothesis (the prior)
        """
        self.eta_0 = initial_eta
        self.value = initial_eta
        self.u = u
        self.total_ballots = 0

    @abstractmethod
    def calculate_eta(self, samples, assorter_value, mu):
        pass