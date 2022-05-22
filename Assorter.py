from Batch import Batch
from AdaptiveEta import AdaptiveEta
from abc import ABC, abstractmethod
from ElectionProfile import ElectionProfile, EPSILON

INVALID_BALLOT = "Invalid"
DEFAULT_MU = 0.5

class Assorter(ABC):

    @abstractmethod
    def __init__(self, risk_limit, election_profile: ElectionProfile, upper_bound, eta, vote_margin=None,
                 weighted_vote_margin=None, initial_statistic=1):
        """
        Constructs a new assertion
        :param risk_limit: Allowed probability of failure
        :param upper_bound: Upper bound of this assorter for a single ballot
        :param eta: Potentially adaptive alternative hypothesis. Should be inherited from the "Eta" class.
        :param initial_statistic: Initial value for this assorter's statistic (usually 1)
        """
        self.u = upper_bound
        self.alpha = risk_limit
        self.T = initial_statistic
        self.ballots_examined = 0
        self.assorter_total = 0
        self.mu = DEFAULT_MU
        self.eta = eta
        self.total_ballots = election_profile.tot_batch.total_votes
        self.vote_margin = vote_margin
        self.weighted_vote_margin = weighted_vote_margin


    @abstractmethod
    def audit_ballot(self, ballot):
        pass

    @abstractmethod
    def audit_batch(self, batch):
        pass

    def update_mu(self, ballot_count, assorter_sum):
        self.ballots_examined += ballot_count
        self.assorter_total += assorter_sum * ballot_count
        if self.total_ballots - self.ballots_examined == 0:
            self.mu = 0
        else:
            self.mu = (self.total_ballots*0.5 - self.assorter_total) / (self.total_ballots - self.ballots_examined)  # Make sure we should multiply by ballots_examined
            if self.mu > self.u:
                print(self, ' uh oh, stinky! I wanted ', self.mu, 'but ', self.u, '. Ballots: ', self.ballots_examined)
            self.mu = min(max(self.mu, 0), self.u - 2*EPSILON)
        if self.mu == 0:
            print(self)

    def get_margin(self):
        return self.vote_margin