from Batch import Batch
from Assorter import Assorter, INVALID_BALLOT, DEFAULT_MU
from ElectionProfile import ElectionProfile
from AdaptiveEta import AdaptiveEta, ADAPTIVE_ETA
from MyEta import MY_ETA, MyEta
import matplotlib.pyplot as plt

TYPE = 3


class MoveSeatAssertion(Assorter):
    """
    Asserts the hypothesis a seat from one party shouldn't be given to another specific party (specific for this assertion)
    instead.
    """

    def __init__(self, risk_limit, party_from, party_to, election_profile: ElectionProfile, paired, eta_mode=ADAPTIVE_ETA):  # TODO Support more eta types
        """
        :param risk_limit: Risk limit of the audit
        :param party_from: Party that a seat should potentially be taken away from
        :param party_to: Party that a seat should potentially be given to
        :param election_profile: Profile of this election
        :param paired: Whether this assertion is done pre-apparentments (true) or post (false)
        :param mu: Assorter mean under the null hypothesis.
        :param eta_mode: Which alternative hypothesis class to use
        """
        self.party_from = party_from
        self.party_to = party_to
        self.election_profile = election_profile
        self.mu = DEFAULT_MU
        self.paired = paired
        self.type = TYPE

        self.party_from1, self.party_from2 = None, None
        if paired:
            reported_party_from_votes = election_profile.tot_batch.reported_paired_tally[party_from]
            reported_party_to_votes = election_profile.tot_batch.reported_paired_tally[party_to]
            if ' + ' in party_to:
                party_to1, party_to2 = party_to.split(' + ')
                party_to_seats = election_profile.reported_seats_won[party_to1] + election_profile.reported_seats_won[party_to2]
            else:
                party_to_seats = election_profile.reported_seats_won[party_to]
            if ' + ' in party_from:
                self.party_from1, self.party_from2 = party_from.split(' + ')
                party_from_seats = election_profile.reported_seats_won[self.party_from1] + election_profile.reported_seats_won[self.party_from2]
            else:
                party_from_seats = election_profile.reported_seats_won[party_from]
        else:
            reported_party_from_votes = election_profile.tot_batch.reported_tally[party_from]
            reported_party_to_votes = election_profile.tot_batch.reported_tally[party_to]
            party_from_seats = election_profile.reported_seats_won[party_from]
            party_to_seats = election_profile.reported_seats_won[party_to]
        u = 0.5 + (party_to_seats + 1)/(2 * party_from_seats)

        neutral_votes = (self.election_profile.tot_batch.total_votes - reported_party_to_votes -
                         reported_party_from_votes)
        self.reported_assorter_mean = (reported_party_from_votes * u + 0.5 * neutral_votes) / \
                                      self.election_profile.tot_batch.total_votes
        eta = None
        if eta_mode == ADAPTIVE_ETA:

            eta = AdaptiveEta(u, self.reported_assorter_mean, 100000, DEFAULT_MU)
        elif eta_mode == MY_ETA:
            eta = MyEta(self.reported_assorter_mean, self.election_profile.tot_batch.total_votes)
        # Debugging stuff
        self.T_list = []
        self.mu_list = []
        self.eta_list = []
        self.assorter_value = []
        self.plot_x = []

        super().__init__(risk_limit, election_profile, u, eta, self.calc_margin())

    def audit_ballot(self, ballot):
        if ballot in self.party_from.split(' + '):
            assorter_value = self.u
        elif ballot in self.party_to.split(' + '):
            assorter_value = 0
        else:
            assorter_value = 0.5

        self.T *= (1 / self.u)*(assorter_value * self.eta.value / self.mu + \
                  (self.u - assorter_value)*(self.u - self.eta.value)/(self.u - self.mu))
        self.update_mu_and_u(1, assorter_value)
        self.eta.calculate_eta(1, assorter_value, self.mu)
        return (self.T >= 1 / self.alpha), self.T

    def audit_batch(self, batch: Batch):
        assorter_value = self.get_assorter_value(batch)
        self.T *= (assorter_value/self.mu) * (self.eta.value-self.mu) / (self.u-self.mu) + (self.u - self.eta.value) / \
                  (self.u - self.mu)
        self.update_mu_and_u(batch.total_votes, assorter_value)
        self.eta.calculate_eta(batch.total_votes, assorter_value * batch.total_votes, self.mu)  # Prepare eta for next batch

        if self.mu < 0:
            self.T = float('inf')
        elif self.mu > self.u:
            self.T = 0

        # Debugging stuff
        self.T_list.append(self.T)
        self.mu_list.append(self.mu)
        self.eta_list.append(self.eta.value)
        self.assorter_value.append(self.eta.assorter_sum / self.eta.total_ballots)
        self.plot_x.append(self.eta.total_ballots)

        return self.T >= (1 / self.alpha), self.T

    def __str__(self):
        return "Move seat from " + self.party_from + " to " + self.party_to

    def get_assorter_value(self, batch: Batch):
        if self.paired:
            party_from_votes = batch.true_paired_tally[self.party_from]
            party_to_votes = batch.true_paired_tally[self.party_to]
        else:
            party_from_votes = batch.true_tally[self.party_from]
            party_to_votes = batch.true_tally[self.party_to]
        return (1 / batch.total_votes) * (self.u*party_from_votes + 0.5*(batch.total_votes - party_from_votes - party_to_votes))

    def calc_margin(self):
        if self.paired:
            party_from_price = self.election_profile.tot_batch.reported_paired_tally[self.party_from] / \
                               self.election_profile.reported_paired_seats_won[self.party_from]
            party_to_seats = self.election_profile.reported_paired_seats_won[self.party_to]
            party_to_votes = self.election_profile.tot_batch.true_paired_tally[self.party_to]
        else:
            party_from_price = self.election_profile.tot_batch.reported_tally[self.party_from] / \
                               self.election_profile.reported_seats_won[self.party_from]
            party_to_seats = self.election_profile.reported_seats_won[self.party_to]
            party_to_votes = self.election_profile.tot_batch.reported_tally[self.party_to]
        return party_from_price * (party_to_seats+1) - party_to_votes

    # TODO delete
    def plot(self):
        fig, axs = plt.subplots(2)
        axs[0].plot(self.plot_x, self.mu_list, label='mu')
        axs[0].plot(self.plot_x, self.eta_list, label='eta')
        axs[0].plot(self.plot_x, self.assorter_value, label='Assorter mean value')
        axs[0].legend()
        axs[1].plot(self.plot_x, self.T_list, label='T')
        fig.suptitle(str(self) + ' (margin: ' + str('{:,}'.format(self.get_margin())) + ')')
        plt.show()
