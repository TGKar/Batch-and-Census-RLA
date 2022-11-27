from Batch import Batch
import numpy as np
from AdaptiveEta import AdaptiveEta
from abc import ABC, abstractmethod
from ElectionProfile import ElectionProfile, EPSILON, INVALID_BALLOT

DEFAULT_MU = 0.5
MAX_ERR = 10**(-10)  # 0.000001
MAX_DISC_SHARE = 1.0  # Assumed maximal discrepency between reported and true results, as a share of the maximal possible assorter value

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
        self.ballots_counter = 0
        self.batch_counter = 0
        self.assorter_total = 0
        self.mu = DEFAULT_MU
        self.eta = eta
        self.total_ballots = election_profile.tot_batch.total_votes
        self.total_batches = len(election_profile.batches)
        self.vote_margin = vote_margin
        self.weighted_vote_margin = weighted_vote_margin

        # Next couple of lines predict the # of batches required for the audit
        self.batch_num = len(election_profile.batches)
        #self.batch_pred = -np.log(self.alpha) / \
        #                  np.log(self.inner_u / (self.inner_u - self.reported_inner_assorter_margin))


    @abstractmethod
    def audit_ballot(self, ballot):
        pass

    def audit_batch(self, batch):
        self.batch_counter += 1
        assorter_value = self.get_assorter_value(batch)
        self.T *= (assorter_value/self.mu) * (self.eta.value-self.mu) / (self.u-self.mu) + (self.u - self.eta.value) / \
                  (self.u - self.mu)
        #self.T *= assorter_value/self.mu
        self.update_mu_and_u(batch.total_votes, assorter_value)
        self.eta.calculate_eta(batch.total_votes, assorter_value * batch.total_votes, self.mu)  # Prepare eta for next batch
        #print("Assorter value: ", assorter_value, ".  T: ", str(self.T), '.  Eta: ' + str(self.eta.value))

        # Delete next 2 lines
        #self.u = self.eta.value + EPSILON
        #self.eta.u = self.u

        if self.mu < 0:
            self.T = float('inf')
        elif (self.batch_counter == self.total_batches) and (self.assorter_total / self.total_ballots >= 0.5):
            self.T = float('inf')
        elif self.mu >= self.u:
            self.T = 0

        return self.T >= (1 / self.alpha), self.T


    def update_mu_and_u(self, ballot_count, assorter_sum):
        self.ballots_counter += ballot_count
        self.assorter_total += assorter_sum * ballot_count
        if self.total_ballots == self.ballots_counter:
            self.mu = 0.5
        else:
            self.mu = (self.total_ballots*0.5 - self.assorter_total) / (self.total_ballots - self.ballots_counter)
            self.mu = max(self.mu, 0)
            self.u = self.eta.value + EPSILON # max(self.u, self.mu + 2*EPSILON)
        self.eta.u = self.u

        if self.u - self.mu == 0 or self.mu == 0:  # TODO delete
            print('PROBLEMO: ZERO DIVISION INCOMING')
            print('mu ', self.mu)
            print('u', self.u)
            print(self.ballots_counter, ' \ ', self.total_ballots)

    def get_margin(self):
        return self.vote_margin

    @abstractmethod
    def get_assorter_value(self, batch: Batch):
        pass

    def get_batch_prediction(self):  # TODO Make abstract and return NAN for alpha
        x = 0.5 + (self.reported_inner_assorter_margin) / (2*(self.inner_u - self.reported_inner_assorter_margin))
        d = self.batch_num
        min_batches = 1
        max_batches = int(d/(2*x))
        batches = 0
        inequality = lambda j: np.log(self.alpha) + (d + 0.5)*np.log(d) + (d/(2*x) - j - 0.5)*np.log(d/(2*x) - j - 1) \
                  - (d/(2*x) + 0.5)*np.log(d / (2*x)) - (d - j - 0.5)*np.log(d - j - 1)
        while min_batches + 1 != max_batches:
            batches = int((max_batches + min_batches) / 2)
            if inequality(batches) > 0:
                max_batches = batches
            else:
                min_batches = batches
        return batches