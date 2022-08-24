from Batch import Batch
from Assorter import Assorter, INVALID_BALLOT, DEFAULT_MU, MAX_ERR, MAX_DISC_SHARE
from ElectionProfile import ElectionProfile, EPSILON
from AdaptiveEta import AdaptiveEta, ADAPTIVE_ETA
from MyEta import MY_ETA, MyEta
import numpy as np

class CompFailedThresholdAssertion(Assorter):
    """
    Asserts the hypothesis that a certain party has at least a certain share of the valid votes.
    """

    def __init__(self, risk_limit, party, threshold, election_profile: ElectionProfile, eta_mode=ADAPTIVE_ETA):  # TODO Support more eta types
        self.type = 2
        self.party = party
        self.threshold = threshold

        """
        self.inner_u = 0
        for batch in election_profile.batches:
            batch_max_disc = self.get_inner_assorter_value(batch.reported_tally[party], batch.reported_invalid_votes, batch.total_votes)
            self.inner_u = max(batch_max_disc, self.inner_u)
        """
        #self.inner_u = 1 / (2*(1 - threshold))

        reported_inner_assorter_mean = self.get_inner_assorter_value(election_profile.tot_batch.reported_tally[party],
                                                                    election_profile.tot_batch.reported_invalid_votes,
                                                                    election_profile.tot_batch.total_votes)
        self.reported_inner_assorter_margin = reported_inner_assorter_mean - 0.5
        eta = None
        vote_margin = (election_profile.tot_batch.total_votes - election_profile.tot_batch.reported_invalid_votes) * threshold \
                      - election_profile.tot_batch.reported_tally[party]

        if self.reported_inner_assorter_margin >= MAX_DISC_SHARE:
            self.inner_u = 1 / (2*(1 - threshold))
        else:
            self.inner_u = MAX_DISC_SHARE / (2 * (1 - threshold))

        #u = 0.5 + self.reported_inner_assorter_margin / (2*(self.inner_u - self.reported_inner_assorter_margin)) + EPSILON
        u = 0.5 + (self.reported_inner_assorter_margin + MAX_ERR / (2*(1 - self.threshold))) / (
                2 * (self.inner_u - self.reported_inner_assorter_margin))
        self.reported_assorter_mean = u - EPSILON
        if eta_mode == ADAPTIVE_ETA:
            eta = AdaptiveEta(u, self.reported_assorter_mean, 100000, DEFAULT_MU)
        elif eta_mode == MY_ETA:
            eta = MyEta(self.reported_assorter_mean, election_profile.tot_batch.total_votes)
        super().__init__(risk_limit, election_profile, u, eta, vote_margin, vote_margin)

    def audit_ballot(self, ballot):
        return None, None

    def get_assorter_value(self, batch: Batch):
        discrepancy = self.get_inner_assorter_value(batch.reported_tally[self.party], batch.reported_invalid_votes, batch.total_votes) \
                    - self.get_inner_assorter_value(batch.true_tally[self.party], batch.true_invalid_votes, batch.total_votes)
        return 0.5 + (self.reported_inner_assorter_margin - discrepancy) / (2*(self.inner_u - self.reported_inner_assorter_margin))

    def get_inner_assorter_value(self, party_votes, invalid_votes, total_votes):
        non_party_votes = total_votes - invalid_votes - party_votes
        return (non_party_votes/(2*(1 - self.threshold)) + 0.5*invalid_votes) / total_votes

    def __str__(self):
        return "Batch-comp (total discrepancy) didn't pass threshold: " + self.party
