from Batch import Batch
from Assorter import Assorter, INVALID_BALLOT, DEFAULT_MU
from ElectionProfile import ElectionProfile
from AdaptiveEta import AdaptiveEta, ADAPTIVE_ETA
from MyEta import MY_ETA, MyEta


class CompThresholdAssertion(Assorter):
    """
    Asserts the hypothesis that a certain party has at least a certain share of the valid votes.
    """

    def __init__(self, risk_limit, party, threshold, election_profile: ElectionProfile, eta_mode=ADAPTIVE_ETA):  # TODO Support more eta types
        self.type = 1
        self.party = party
        self.threshold = threshold
        eta = None
        self.inner_u = 1 / (2*threshold)
        reported_inner_assorter_mean = self.get_inner_assorter_mean(election_profile.tot_batch.reported_tally[party],
                                                               election_profile.tot_batch.reported_invalid_votes,
                                                               election_profile.tot_batch.total_votes)
        self.reported_inner_margin = reported_inner_assorter_mean - 0.5
        # u = 1 + self.reported_inner_margin / (2*self.inner_u)
        #u = self.inner_u / (self.inner_u - self.reported_inner_margin)
        u = 0.5 + 1/(2 * self.inner_u * election_profile.tot_batch.total_votes)
        self.reported_assorter_mean = 0.5 + (self.reported_inner_margin) / (2*self.inner_u)
        if eta_mode == ADAPTIVE_ETA:
            eta = AdaptiveEta(u, self.reported_assorter_mean, 100000, DEFAULT_MU)
        elif eta_mode == MY_ETA:
            eta = MyEta(self.reported_assorter_mean, election_profile.tot_batch.total_votes)
            # print("Reported assorter mean: ", reported_assorter_mean)
        super().__init__(risk_limit, election_profile, u, eta, -1)

    def audit_ballot(self, ballot):
        return None, None

    def audit_batch(self, batch: Batch):

        reported_inner_assorter_value = self.get_inner_assorter_mean(batch.reported_tally[self.party],
                                                                     batch.reported_invalid_votes, batch.total_votes)
        true_inner_assorter_value = self.get_inner_assorter_mean(batch.true_tally[self.party],
                                                                     batch.true_invalid_votes, batch.total_votes)
        assorter_value = 0.5 + (self.reported_inner_margin - reported_inner_assorter_value + true_inner_assorter_value) \
                         / (2*self.inner_u)
        #assorter_value = (self.inner_u*batch.total_votes + true_inner_assorter_value - reported_inner_assorter_value) \
        #                 / (2 * batch.total_votes * (self.inner_u - self.reported_inner_margin))
        self.T *= (assorter_value/self.mu) * (self.eta.value-self.mu) / (self.u-self.mu) + (self.u - self.eta.value) / \
                  (self.u - self.mu)
        self.update_mu(batch.total_votes, assorter_value)
        self.eta.calculate_eta(batch.total_votes, assorter_value * batch.total_votes, self.mu)  # Prepare eta for next batch
        #print("Assorter value: ", assorter_value, ".  T: ", str(self.T), '.  Eta: ' + str(self.eta.value))
        #print(self.T)
        if self.mu < 0:
            self.T = float('inf')
        if self.mu > self.u:
            self.T = 0

        return self.T >= (1 / self.alpha), self.T

    def __str__(self):
        return "Batch-comp passed threshold: " + self.party

    def get_inner_assorter_mean(self, party_votes, invalid_votes, total_votes):
        return (self.inner_u * party_votes +
                                  0.5 * invalid_votes) / \
                                 total_votes