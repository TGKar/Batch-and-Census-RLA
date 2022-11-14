from Batch import Batch
from Assorter import Assorter, INVALID_BALLOT, DEFAULT_MU
from ElectionProfile import ElectionProfile
from AdaptiveEta import AdaptiveEta, ADAPTIVE_ETA
from MyEta import MY_ETA, MyEta

TYPE = 4


class PluralityAssertion(Assorter):
    """
    Asserts the hypothesis that a certain party received more votes than another party.
    """

    def __init__(self, risk_limit, win_party, lose_party, election_profile: ElectionProfile, eta_mode=ADAPTIVE_ETA):  # TODO Support more eta types
        self.type = TYPE
        self.win_party = win_party
        self.lose_party = lose_party
        eta = None
        u = 1
        rep_win_party_votes = election_profile.tot_batch.reported_tally[win_party]
        rep_lose_party_votes = election_profile.tot_batch.reported_tally[lose_party]
        vote_margin = (rep_win_party_votes - rep_lose_party_votes) / 2
        self.reported_assorter_mean = (u * rep_win_party_votes + 0.5*(election_profile.tot_batch.total_votes -
                                                                     rep_win_party_votes - rep_lose_party_votes)) / election_profile.tot_batch.total_votes
        if eta_mode == ADAPTIVE_ETA:
            eta = AdaptiveEta(u, self.reported_assorter_mean, 5000, DEFAULT_MU)
        elif eta_mode == MY_ETA:
            eta = MyEta(self.reported_assorter_mean, election_profile.tot_batch.total_votes)
            # print("Reported assorter mean: ", reported_assorter_mean)
        super().__init__(risk_limit, election_profile, u, eta, vote_margin)

    def audit_ballot(self, ballot):
        if ballot == self.win_party:
            assorter_value = self.u
        elif ballot == self.lose_party:
            assorter_value = 0
        else:
            assorter_value = 0.5

        if self.mu == 0:
            print(self.eta.total_ballots)
            print('bad u')
        self.T *= (1 / self.u)*(assorter_value * self.eta.value / self.mu + \
                  (self.u - assorter_value)*(self.u - self.eta.value)/(self.u - self.mu))
        self.update_mu_and_u(1, assorter_value)
        self.eta.calculate_eta(1, assorter_value, self.mu)

        if self.mu <= 0:
            self.T = float('inf')
        if self.mu > self.u:
            self.T = 0
        return (self.T >= 1 / self.alpha), self.T

    def get_assorter_value(self, batch: Batch):
        return (1 / batch.total_votes) * (self.u*batch.true_tally[self.win_party] + 0.5*(batch.total_votes -
                                            batch.true_tally[self.win_party] - batch.true_tally[self.lose_party]))

    def __str__(self):
        return "Party " + str(self.win_party) + " beat party " + str(self.lose_party)