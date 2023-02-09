from Batch import Batch
from ElectionAssertion import Assorter, INVALID_BALLOT, DEFAULT_MU, MAX_ERR, MAX_DISC_SHARE
from ElectionProfile import ElectionProfile, EPSILON
from AdaptiveEta import AdaptiveEta, ADAPTIVE_ETA
from MyEta import MY_ETA, MyEta
from SetEta import SET_ETA, SetEta
import matplotlib.pyplot as plt
import numpy as np


class AlphaMoveSeatAssertion(Assorter):
    """
    Asserts the hypothesis a seat from one party shouldn't be given to another specific party (specific for this assertion)
    instead.
    """

    def __init__(self, risk_limit, party_from, party_to, election_profile: ElectionProfile, paired,
                 eta_mode=SET_ETA, mode=0):
        """
        :param risk_limit: Risk limit of the audit
        :param party_from: Party that a seat should potentially be taken away from
        :param party_to: Party that a seat should potentially be given to
        :param election_profile: Profile of this election
        :param paired: Whether this assertion is done pre-apparentments (true) or post (false)
        :param mu: Assorter mean under the null hypothesis.
        :param eta_mode: Which alternative hypothesis class to use
        :param mode: If -1, makes sure "party_from" doesn't deserve 2 seats less than it received. If +1, makes sure
        party_to doesn't deserve 2 extra seats. If 0, checks for their exact number of seats.
        """
        if mode < -1 or mode > 1:
            print("ILLEGAL ASSERTION MODE")
        self.type = 3
        self.party_from = party_from
        self.party_to = party_to
        self.election_profile = election_profile
        self.mu = DEFAULT_MU
        self.paired = paired
        self.mode = mode

        if paired:
            self.party_from_seats = election_profile.reported_paired_seats_won[party_from]
            self.party_to_seats = election_profile.reported_paired_seats_won[party_to]
            party_from_reported_votes = election_profile.tot_batch.reported_paired_tally[party_from]
            party_to_reported_votes = election_profile.tot_batch.reported_paired_tally[party_to]
        else:
            self.party_from_seats = election_profile.reported_seats_won[party_from]
            self.party_to_seats = election_profile.reported_seats_won[party_to]
            party_from_reported_votes = election_profile.tot_batch.reported_tally[party_from]
            party_to_reported_votes = election_profile.tot_batch.reported_tally[party_to]

        self.inner_u = 0
        for batch in election_profile.batches:
            if paired:
                party_from_reported_batch_votes = batch.reported_paired_tally[party_from]
                party_to_reported_batch_votes = batch.reported_paired_tally[party_to]
            else:
                party_from_reported_batch_votes = batch.reported_tally[party_from]
                party_to_reported_batch_votes = batch.reported_tally[party_to]
            batch_max_disc = self.get_inner_assorter_value(party_from_reported_batch_votes, party_to_reported_batch_votes, batch.total_votes)
            self.inner_u = max(batch_max_disc, self.inner_u)

        self.inner_u = min(self.inner_u, (0.5 + (self.party_to_seats + 1)/(2 * self.party_from_seats))*MAX_DISC_SHARE)
        self.reported_inner_assorter_margin = self.get_inner_assorter_value(party_from_reported_votes,
                                                                            party_to_reported_votes,
                                                                            election_profile.tot_batch.total_votes) - 0.5

        weighted_vote_margin, vote_margin = self.calc_margins()

        u = 0.5 + (self.reported_inner_assorter_margin + 0.5 + (self.party_to_seats + 1)/(2 * self.party_from_seats)) / \
             (2 * (self.inner_u - self.reported_inner_assorter_margin))
        self.reported_assorter_mean = 0.5 + self.reported_inner_assorter_margin / (2 * (self.inner_u - self.reported_inner_assorter_margin))

        eta = None
        if eta_mode == ADAPTIVE_ETA:
            eta = AdaptiveEta(u, self.reported_assorter_mean, 100000, DEFAULT_MU)
        elif eta_mode == MY_ETA:
            eta = MyEta(self.reported_assorter_mean, self.election_profile.tot_batch.total_votes)
        elif eta_mode == SET_ETA:
            eta = SetEta(u, self.reported_assorter_mean)
        # Next block is for debugging purposes only
        self.inc_T_list = []
        self.T_list = []
        self.mu_list = []
        self.eta_list = []
        self.assorter_mean = []
        self.assorter_values = []
        self.plot_x = []

        super().__init__(risk_limit, election_profile, u, eta, vote_margin=vote_margin, weighted_vote_margin=weighted_vote_margin)


    def audit_ballot(self, ballot):
        return None, None

    def audit_batch(self, batch: Batch):
        #if self.party_from == 'Likud + Yemina' and self.party_to == 'Kahol Lavan + Yisrael Beytenu':
        #    print('now')
        self.batch_counter += 1
        assorter_value = self.get_assorter_value(batch)
        self.T *= (assorter_value/self.mu) * (self.eta.value-self.mu) / (self.u-self.mu) + (self.u - self.eta.value) / \
                  (self.u - self.mu)
        self.update_mu_and_u(batch.total_votes, assorter_value)
        self.eta.calculate_eta(batch.total_votes, assorter_value * batch.total_votes, self.mu)  # Prepare eta for next batch
        if self.mu <= 0:
            print(self, "approved via small mu")
            self.T = float('inf')
        if self.mu > self.u:
            self.T = 0

        # For debugging purposes
        self.T_list.append(self.T)
        if self.mu > 0:
            next_t = (assorter_value/self.mu) * (self.eta.value-self.mu) / (self.u-self.mu) + (self.u - self.eta.value) / \
                  (self.u - self.mu)
        else:
            next_t = 1 / self.alpha
        self.inc_T_list.append(next_t)
        self.mu_list.append(self.mu)
        self.eta_list.append(self.eta.value)
        self.assorter_mean.append(self.eta.assorter_sum / self.eta.total_ballots)
        self.assorter_values.append(assorter_value)
        self.plot_x.append(self.eta.total_ballots)
        return self.T >= (1 / self.alpha), self.T

    def get_assorter_value(self, batch: Batch):

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

        discrepancy = self.get_inner_assorter_value(rep_party_from_votes, rep_party_to_votes, batch.total_votes) - \
                      self.get_inner_assorter_value(true_party_from_votes, true_party_to_votes, batch.total_votes)
        assorter_value = 0.5 + (self.reported_inner_assorter_margin - discrepancy) / (2*(self.inner_u - self.reported_inner_assorter_margin))
        return assorter_value

    def __str__(self):
        if self.mode == 0:
            return "Batch-comp (total discrepancy) move seat from " + self.party_from + " to " + self.party_to + ' u ' + str(self.u)
        elif self.mode == -1:
            return "Batch-comp (total discrepancy) move seat from " + self.party_from + " (-1) to " + self.party_to
        elif self.mode == 1:
            return "Batch-comp (total discrepancy) move seat from " + self.party_from + " to " + self.party_to + " (+1)"
        return "FAULTY ASSERTION: ILLEGAL ASSERTION MODE"

    # For debugging
    def plot(self):
        fig, axs = plt.subplots(2)
        axs[0].plot(self.plot_x, self.mu_list, label='mu')
        axs[0].plot(self.plot_x, self.eta_list, label='eta')
        axs[0].scatter(self.plot_x, self.assorter_values, s=20, label='Assorter value')
        axs[0].plot(self.plot_x, self.assorter_mean, label='Assorter mean value')
        axs[0].legend()
        axs[1].plot(self.plot_x, self.T_list, label='T')
        axs[0].set_xlabel('Ballots')
        axs[0].set_ylabel('Value')
        axs[1].set_xlabel('Ballots')
        axs[1].set_ylabel('T')
        fig.suptitle(str(self) + ' (margin: ' + str('{:,}'.format(self.get_margin())) + ')')
        plt.show()

    def calc_margins(self):
        """
        Calculates and returns this assertion's margins
        """
        if self.paired:
            party_from_votes = self.election_profile.tot_batch.reported_paired_tally[self.party_from]
            party_from_seats = self.election_profile.reported_paired_seats_won[self.party_from] + min(self.mode, 0)
            party_to_seats = self.election_profile.reported_paired_seats_won[self.party_to] + max(self.mode, 0)
            party_to_votes = self.election_profile.tot_batch.reported_paired_tally[self.party_to]
        else:
            party_from_votes = self.election_profile.tot_batch.reported_tally[self.party_from]
            party_from_seats = self.election_profile.reported_seats_won[self.party_from] + min(self.mode, 0)
            party_to_seats = self.election_profile.reported_seats_won[self.party_to] + max(self.mode, 0)
            party_to_votes = self.election_profile.tot_batch.reported_tally[self.party_to]
        party_to_margin = (party_to_seats+1) * party_from_votes / party_from_seats - party_to_votes
        party_from_margin = party_from_votes - party_from_seats * party_to_votes / (party_to_seats+1)

        party_from_ratio = 1 / party_from_seats
        party_to_ratio = 1 / (party_to_seats + 1)
        vote_margin = ((party_from_votes*party_from_ratio) - (party_to_votes*party_to_ratio)) / (party_from_ratio + party_to_ratio)

        weighted_margin = party_from_votes/party_from_seats - party_to_votes/(party_to_seats+1)
        if party_to_margin < party_from_margin:  # Next lines are useful for debugging but not necessary
            self.closer_margin = 'party to'
        else:
            self.closer_margin = 'party_from'
        return weighted_margin, vote_margin


    def get_inner_assorter_value(self, party_from_votes, party_to_votes, total_votes):
        """
        :param party_votes: # of votes for this assertion's party in a batch
        :param invalid_votes: # of invalid votes in this batch
        :param total_votes: total # of votes in the batch
        :return: The value of the inner assorter (a) over the given data
        """
        assorter_max = 0

        if self.mode == 0:
            assorter_max = 0.5 + (self.party_to_seats + 1) / (2*self.party_from_seats)
        elif self.mode == 1:
            assorter_max = 0.5 + (self.party_to_seats + 2) / (2*self.party_from_seats)
        elif self.mode == -1:
            assorter_max = 0.5 + (self.party_to_seats + 1) / (2*(self.party_from_seats - 1))

        return (party_from_votes * assorter_max + 0.5 * (total_votes - party_from_votes - party_to_votes)) / total_votes