from Batch import Batch
from Assorter import Assorter, INVALID_BALLOT, DEFAULT_MU
from ElectionProfile import ElectionProfile, EPSILON
from AdaptiveEta import AdaptiveEta, ADAPTIVE_ETA
from MyEta import MY_ETA, MyEta
import matplotlib.pyplot as plt

class CompMoveSeatAssertion(Assorter):
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
        self.type = 3
        self.party_from = party_from
        self.party_to = party_to
        self.election_profile = election_profile
        self.mu = DEFAULT_MU
        self.paired = paired

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
        self.inner_u = 0.5 + (party_to_seats + 1)/(2 * party_from_seats)

        reported_inner_assorter_mean = self.get_inner_assorter_mean(reported_party_from_votes, reported_party_to_votes, self.election_profile.tot_batch.total_votes)
        self.reported_inner_margin = reported_inner_assorter_mean - 0.5
        # u = 1 + self.reported_inner_margin / (2*self.inner_u)
        #u = self.inner_u / (self.inner_u - self.reported_inner_margin)
        u = 0.5 + 1/(2 * self.inner_u * election_profile.tot_batch.total_votes) + EPSILON
        self.reported_assorter_mean = 0.5 + (self.reported_inner_margin) / (2*self.inner_u)
        eta = None
        if eta_mode == ADAPTIVE_ETA:
            eta = AdaptiveEta(u, self.reported_assorter_mean, 100000, DEFAULT_MU)
        elif eta_mode == MY_ETA:
            eta = MyEta(self.reported_assorter_mean, self.election_profile.tot_batch.total_votes)
        # TODO delete this section
        self.T_list = []
        self.mu_list = []
        self.eta_list = []
        self.assorter_value = []
        self.plot_x = []

        super().__init__(risk_limit, election_profile, u, eta, -1)

    def audit_ballot(self, ballot):
        if ballot == self.party_from or ballot == self.party_from1 or ballot == self.party_from2:
            assorter_value = self.u
        elif ballot == self.party_to:
            assorter_value = 0
        else:
            assorter_value = 0.5
        self.T *= (1 / self.u)*(assorter_value * self.eta.value / self.mu + \
                  (self.u - assorter_value)*(self.u - self.eta.value)/(self.u - self.mu))
        self.update_mu_and_u(1, assorter_value)
        self.eta.calculate_eta(1, assorter_value, self.mu)
        return (self.T >= 1 / self.alpha), self.T

    def audit_batch(self, batch: Batch):
        if self.paired:
            rep_party_from_votes = batch.reported_paired_tally[self.party_from]
            rep_party_to_votes = batch.reported_paired_tally[self.party_to]
            true_party_from_votes = batch.true_paired_tally[self.party_from]
            true_party_to_votes = batch.true_paired_tally[self.party_to]
        else:
            rep_party_from_votes = batch.reported_tally[self.party_from]
            rep_party_to_votes = batch.reported_tally[self.party_to]
            true_party_from_votes = batch.true_tally[self.party_from]
            true_party_to_votes = batch.true_tally[self.party_to]

        reported_inner_assorter_value = self.get_inner_assorter_mean(rep_party_from_votes, rep_party_to_votes, batch.total_votes)
        true_inner_assorter_value = self.get_inner_assorter_mean(true_party_from_votes, true_party_to_votes, batch.total_votes)

        assorter_value = 0.5 + (self.reported_inner_margin - reported_inner_assorter_value + true_inner_assorter_value) \
                         / (2*self.inner_u)
        #assorter_value = (self.inner_u * batch.total_votes + true_inner_assorter_value - reported_inner_assorter_value) \
        #                 / (2 * batch.total_votes * (self.inner_u - self.reported_inner_margin))
        #if self.u - self.mu == 0 or self.mu == 0:
        #    print(self, self.mu)
        self.T *= (assorter_value/self.mu) * (self.eta.value-self.mu) / (self.u-self.mu) + (self.u - self.eta.value) / \
                  (self.u - self.mu)
        self.update_mu_and_u(batch.total_votes, assorter_value)
        self.eta.calculate_eta(batch.total_votes, assorter_value * batch.total_votes, self.mu)  # Prepare eta for next batch
        #print("Assorter value: ", assorter_value, ".  T: ", str(self.T), '.  Eta: ' + str(self.eta.value))
        #print(self.T)
        if self.mu <= 0:
            self.T = float('inf')
        if self.mu > self.u:
            self.T = 0

        # TODO delete this section
        self.T_list.append(self.T)
        self.mu_list.append(self.mu)
        self.eta_list.append(self.eta.value)
        self.assorter_value.append(self.eta.assorter_sum / self.eta.total_ballots)
        self.plot_x.append(self.eta.total_ballots)

        return self.T >= (1 / self.alpha), self.T

    def __str__(self):
        return "Batch-comp move sit from " + self.party_from + " to " + self.party_to

    def get_margin(self):
        if self.paired:
            party_from_price = self.election_profile.tot_batch.true_paired_tally[self.party_from] / \
                               self.election_profile.reported_paired_seats_won[self.party_from]
            party_to_seats = self.election_profile.reported_paired_seats_won[self.party_to]
            party_to_votes = self.election_profile.tot_batch.true_paired_tally[self.party_to]
        else:
            party_from_price = self.election_profile.tot_batch.true_tally[self.party_from] / \
                               self.election_profile.reported_seats_won[self.party_from]
            party_to_seats = self.election_profile.reported_seats_won[self.party_to]
            party_to_votes = self.election_profile.tot_batch.true_tally[self.party_to]
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

    def get_inner_assorter_mean(self, party_from_votes, party_to_votes, total_votes):
        return (party_from_votes * self.inner_u + 0.5 * (total_votes - party_from_votes - party_to_votes)) / total_votes
