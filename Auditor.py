from ElectionProfile import ElectionProfile
from ThresholdAssertion import ThresholdAssertion
from MoveSeatAssertion import MoveSeatAssertion
from FailedThresholdAssertion import FailedThresholdAssertion
from CompThresholdAssortion import CompThresholdAssertion
from CompFailedThresholdAssertion import CompFailedThresholdAssertion
from CompMoveSeatAssertion import CompMoveSeatAssertion
from CompThresholdAssortion2 import CompThresholdAssertion2
from CompFailedThresholdAssertion2 import CompFailedThresholdAssertion2
from CompMoveSeatAssertion2 import CompMoveSeatAssertion2
import numpy as np
from MyEta import MY_ETA
import matplotlib.pyplot as plt


MOVE_SEAT_ASSERTION = CompMoveSeatAssertion2
THRESHOLD_ASSERTION = CompThresholdAssertion2
FAILED_ASSERTION = CompFailedThresholdAssertion2


class Auditor:
    def __init__(self, election_profile: ElectionProfile, risk_limit, threshold):
        self.election_profile = election_profile
        self.risk_limit = risk_limit
        self.threshold = threshold
        self.passed_threshold_assertions = []
        self.failed_threshold_assertions = []
        self.comparison_assertions = []
        self.create_threshold_assertions()
        self.create_comparison_assertions()

    def create_threshold_assertions(self):
        # TODO check only parties with minimal number of seats that isn't 0
        for party in self.election_profile.parties:
            if self.election_profile.reported_seats_won[party] == 0:  # Assumes party can't pass threshold and get 0 seats
                self.failed_threshold_assertions.append(FAILED_ASSERTION(self.risk_limit, party, self.threshold, self.election_profile))
            else:
                self.passed_threshold_assertions.append(THRESHOLD_ASSERTION(self.risk_limit, party, self.threshold, self.election_profile))

    def create_comparison_assertions(self):
        # Add paired comparison (combining parties who signed apparentments)
        paired_parties = []
        for party1, party2 in self.election_profile.apparentment:
            paired_parties += [party1, party2]
        for i, party1 in enumerate(self.election_profile.reported_paired_seats_won.keys()):
            if self.election_profile.reported_paired_seats_won[party1] > 0 and (party1 not in paired_parties):
                for j in range(i-1):
                    party2 = list(self.election_profile.reported_paired_seats_won.keys())[j]
                    if self.election_profile.reported_paired_seats_won[party2] > 0 and (party2 not in paired_parties):
                        self.comparison_assertions.append(MOVE_SEAT_ASSERTION(self.risk_limit, party1, party2, self.election_profile, True))
                        self.comparison_assertions.append(MOVE_SEAT_ASSERTION(self.risk_limit, party2, party1, self.election_profile, True))

        # Verify correct seat splitting between parties who signed apparentments
        for party1, party2 in self.election_profile.apparentment:
            self.comparison_assertions.append(MOVE_SEAT_ASSERTION(self.risk_limit, party1, party2, self.election_profile, False))
            self.comparison_assertions.append(MOVE_SEAT_ASSERTION(self.risk_limit, party2, party1, self.election_profile, False))

    def audit(self):
        # Calculate batch sampling probabilities
        batch_probs = np.zeros(len(self.election_profile.batches))
        for i, batch in enumerate(self.election_profile.batches):
            batch_probs[i] = batch.total_votes / self.election_profile.tot_batch.total_votes
        assert(np.sum(batch_probs) == 1.0)

        # TODO delete - plots margin vs required ballots
        required_ballots_moveseat = []
        margin_moveseat = []
        required_ballots_threshold = []
        margin_threshold = []
        required_ballots_failed = []
        margin_failed = []

        # Audit elections
        batch_counter, ballot_counter = 0, 0
        assertions = self.comparison_assertions + self.failed_threshold_assertions + self.passed_threshold_assertions
        statistic_values = np.zeros(len(assertions))
        plot_margin = []
        plot_ballot_counter = []
        while len(assertions) > 0 and batch_counter < len(self.election_profile.batches):
            assert(np.isclose(np.sum(batch_probs), 1.0))
            batch_ind = np.random.choice(list(range(len(batch_probs))), p=batch_probs)
            batch_to_audit = self.election_profile.batches[batch_ind]
            batch_to_audit.audited = True
            completed_assertion_inds = []
            for i, assertion in enumerate(assertions):
                assertion_done, statistic_values[i] = assertion.audit_batch(batch_to_audit)
                if assertion_done:
                    completed_assertion_inds.append(i)

            batch_counter += 1
            ballot_counter += batch_to_audit.total_votes

            for i, delete_ind in enumerate(completed_assertion_inds):  # Remove assertions that were fulfilled
                print("Finished assertion: ", str(assertions[delete_ind - i]), ' with margin ',  assertions[delete_ind - i].vote_margin,'after ballot ', str('{:,}'.format(ballot_counter)))
                #print("Finished assertion: ", str(assertions[delete_ind - i]),'after ballot ', str('{:,}'.format(ballot_counter)))
                #if isinstance(assertions[delete_ind - i], MoveSeatAssertion):  # TODO delete
                #    plot_ballot_counter.append(ballot_counter)
                #    plot_margin.append(assertions[delete_ind - i].vote_margin)
                #    if ballot_counter > 4000000:
                #        pass
                        # assertions[delete_ind - i].plot()
                if assertions[delete_ind - i].type == 1:
                    required_ballots_threshold.append(ballot_counter)
                    margin_threshold.append(assertions[delete_ind - i].vote_margin)
                elif assertions[delete_ind - i].type == 2:
                    required_ballots_failed.append(ballot_counter)
                    margin_failed.append(assertions[delete_ind - i].vote_margin)
                elif assertions[delete_ind - i].type == 3:
                    required_ballots_moveseat.append(ballot_counter)
                    margin_moveseat.append(assertions[delete_ind - i].vote_margin)
                del assertions[delete_ind - i]
            batch_probs[batch_ind] = 0  # Remove audited batch from sampling pool
            if batch_counter + 1 <= len(self.election_profile.batches):
                batch_probs /= np.sum(batch_probs)  # Normalize the distribution
        print("Remaining assertions:")
        for assertion in assertions:
            print(str(assertion) + ". T:" + str(assertion.T) + '. Margin: ' + str(assertion.vote_margin) +
                  ". Reported assorter value: " + str(assertion.reported_assorter_mean) + '. Actual mean value: ' +
                  str(assertion.eta.assorter_sum / assertion.eta.total_ballots) + '. Final eta assorter mean: ' + str(assertion.eta.assorter_sum / assertion.eta.total_ballots))
            print('Ballots examined: ', str(assertion.eta.total_ballots), '/', str(assertion.eta.total_ballots))
            print(assertion.eta.total_ballots)
            #assertio.plot()

        # TODO delete next section
        plt.scatter(margin_threshold, required_ballots_threshold, label='Passed Threshold')
        plt.scatter(margin_failed, required_ballots_failed, label='Failed Threshold')
        plt.scatter(margin_moveseat, required_ballots_moveseat, label='Move-seat Threshold')
        plt.legend()
        plt.xlabel("Assertion Margin")
        plt.ylabel("Required Ballots")
        plt.show()

        return batch_counter, ballot_counter