from Batch import Batch
from Assorter import Assorter, INVALID_BALLOT, DEFAULT_MU
from ElectionProfile import ElectionProfile
import Eta
from AdaptiveEta import AdaptiveEta, ADAPTIVE_ETA
from MyEta import MY_ETA, MyEta

TYPE = 2

class FailedThresholdAssertion(Assorter):
    """
    Asserts the hypothesis that a certain party has at most a certain share of the valid votes.
    """

    def __init__(self, risk_limit, party, threshold, election_profile: ElectionProfile, eta_mode=ADAPTIVE_ETA):  # TODO Support more eta types
        self.party = party
        self.threshold = threshold
        self.mu = DEFAULT_MU
        self.type = TYPE
        eta = None
        u = 1 / (2*(1 - threshold))
        vote_margin = (election_profile.tot_batch.total_votes - election_profile.tot_batch.reported_invalid_votes)*threshold - \
                      election_profile.tot_batch.reported_tally[party]

        reported_non_party_votes = election_profile.tot_batch.total_votes - election_profile.tot_batch.reported_invalid_votes - \
                                   election_profile.tot_batch.true_tally[party]
        reported_assorter_mean = (u * reported_non_party_votes + 0.5 * election_profile.tot_batch.reported_invalid_votes) / \
                                 election_profile.tot_batch.total_votes
        if eta_mode == ADAPTIVE_ETA:

            eta = AdaptiveEta(u, reported_assorter_mean, 5000, DEFAULT_MU)
        elif eta_mode == MY_ETA:
            eta = MyEta(reported_assorter_mean, election_profile.tot_batch.total_votes)
        super().__init__(risk_limit, election_profile, u, eta, vote_margin)

    def audit_ballot(self, ballot):
        if ballot == self.party:
            assorter_value = 0
        elif ballot == INVALID_BALLOT:
            assorter_value = 0.5
        else:
            assorter_value = 1 / (2*(1 - self.threshold))
        self.T *= (1 / self.u)*(assorter_value * self.eta.value / self.mu + \
                  (self.u - assorter_value)*(self.u - self.eta.value)/(self.u - self.mu))
        self.update_mu(1, assorter_value)
        self.eta.calculate_eta(1, assorter_value, self.mu)
        return (self.T >= 1 / self.alpha), self.T

    def audit_batch(self, batch: Batch):
        non_party_votes = batch.total_votes - batch.true_invalid_votes - batch.true_tally[self.party]
        assorter_value = (1 / batch.total_votes) * (non_party_votes / (2*(1 - self.threshold)) + 0.5 * batch.true_invalid_votes)
        self.T *= (assorter_value/self.mu) * (self.eta.value-self.mu) / (self.u-self.mu) + (self.u - self.eta.value) / \
                  (self.u - self.mu)
        self.update_mu(batch.total_votes, assorter_value)
        self.eta.calculate_eta(batch.total_votes, assorter_value * batch.total_votes, self.mu)  # Prepare eta for next batch
        #print("Assorter value: ", assorter_value, ".  T: ", str(self.T), '.  Eta: ' + str(self.eta.value))
        #print(self.T)
        if self.mu < 0:
            self.T = float('inf')
        elif self.mu > self.u:
            self.T = 0
        return self.T >= (1 / self.alpha), self.T

    def __str__(self):
        return "Didn't pass threshold: " + self.party