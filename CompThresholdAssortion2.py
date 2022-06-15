from Batch import Batch
from Assorter import Assorter, INVALID_BALLOT, DEFAULT_MU
from ElectionProfile import ElectionProfile, EPSILON
from AdaptiveEta import AdaptiveEta, ADAPTIVE_ETA
from MyEta import MY_ETA, MyEta


class CompThresholdAssertion2(Assorter):
    """
    Asserts the hypothesis that a certain party has at least a certain share of the valid votes.
    """

    def __init__(self, risk_limit, party, threshold, election_profile: ElectionProfile, eta_mode=ADAPTIVE_ETA):
        self.type = 1
        self.party = party
        self.threshold = threshold
        self.parties_n = 1 + threshold
        self.profile = election_profile  # TODO delete
        self.inner_u = 1 / (2*threshold)

        eta = None
        self.reported_inner_assorter_margin = self.get_inner_assorter_mean(election_profile.tot_batch.reported_tally[party],
                                                                    election_profile.tot_batch.reported_invalid_votes,
                                                                    election_profile.tot_batch.total_votes) - 0.5
        vote_margin = election_profile.tot_batch.reported_tally[party] - \
                      threshold * (election_profile.tot_batch.total_votes - election_profile.tot_batch.reported_invalid_votes)
        u = 0.5 + (self.reported_inner_assorter_margin) / (2*self.inner_u) + EPSILON
        self.reported_assorter_mean = u - EPSILON
        if eta_mode == ADAPTIVE_ETA:
            eta = AdaptiveEta(u, self.reported_assorter_mean, 100000, DEFAULT_MU)
        elif eta_mode == MY_ETA:
            eta = MyEta(self.reported_assorter_mean, election_profile.tot_batch.total_votes)
        super().__init__(risk_limit, election_profile, u, eta, vote_margin, vote_margin)

    def audit_ballot(self, ballot):
        return None, None

    def audit_batch(self, batch: Batch):

        assorter_value = self.get_assorter_value(batch)
        self.T *= (assorter_value/self.mu) * (self.eta.value-self.mu) / (self.u-self.mu) + (self.u - self.eta.value) / \
                  (self.u - self.mu)
        if self.T < 0:
            print(self.T)
        self.update_mu_and_u(batch.total_votes, assorter_value)
        self.eta.calculate_eta(batch.total_votes, assorter_value * batch.total_votes, self.mu)  # Prepare eta for next batch
        # print("Assorter value: ", assorter_value, ".  T: ", str(self.T), '.  Eta: ' + str(self.eta.value))
        if self.mu <= 0:
            self.T = float('inf')

        return self.T >= (1 / self.alpha), self.T

    def get_assorter_value(self, batch: Batch):
        discrepancy = self.get_inner_assorter_mean(batch.reported_tally[self.party], batch.reported_invalid_votes, batch.total_votes) \
                    - self.get_inner_assorter_mean(batch.true_tally[self.party], batch.true_invalid_votes, batch.total_votes)
        return 0.5 + (self.reported_inner_assorter_margin - discrepancy) / (2*self.inner_u)

    def get_inner_assorter_mean(self, party_votes, invalid_votes, total_votes):
        return (self.inner_u * party_votes +
                                  0.5 * invalid_votes) / \
                                 total_votes

    def __str__(self):
        return "Batch-comp (total discrepancy) passed threshold: " + self.party
