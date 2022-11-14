from ElectionProfile import ElectionProfile
from PluralityAssertion import PluralityAssertion
import numpy as np
from MyEta import MY_ETA
import matplotlib.pyplot as plt


class PluralityAuditor:
    def __init__(self, election_profile: ElectionProfile, risk_limit):
        self.profile = election_profile
        self.risk_limit = risk_limit
        self.parties = election_profile.parties
        self.election_profile = election_profile
        rep_winner = max(election_profile.tot_batch.reported_tally, key=election_profile.tot_batch.reported_tally.get)

        self.assertions = []
        for party in self.parties:
            if party != rep_winner:
                self.assertions.append(PluralityAssertion(risk_limit, rep_winner, party, election_profile))

    def ballot_audit(self):
        required_ballots_moveseat = []

        # Audit elections
        ballot_counter = 0
        while len(self.assertions) > 0 and ballot_counter < len(self.election_profile.ballots):
            ballot_to_audit = self.election_profile.ballots[ballot_counter]
            completed_assertion_inds = []
            for i, assertion in enumerate(self.assertions):
                assertion_done, _ = assertion.audit_ballot(ballot_to_audit)
                if assertion_done:
                    completed_assertion_inds.append(i)

            ballot_counter += 1

            for i, delete_ind in enumerate(completed_assertion_inds):  # Remove assertions that were fulfilled
                print("Finished assertion: ", str(self.assertions[delete_ind - i]), ' with margin ',
                      self.assertions[delete_ind - i].vote_margin, 'after ballot ', str('{:,}'.format(ballot_counter)))

                del self.assertions[delete_ind - i]

        print("Remaining assertions:")
        for assertion in self.assertions:
            print(str(assertion) + ". T:" + str(assertion.T) + '. Margin: ' + str(assertion.vote_margin) +
                  ". Reported assorter value: " + str(assertion.reported_assorter_mean) + '. Actual mean value: ' +
                  str(assertion.eta.assorter_sum / assertion.eta.total_ballots) + '. Final eta assorter mean: ' + str(
                assertion.eta.assorter_sum / assertion.eta.total_ballots))
            print('Ballots examined: ', str(assertion.eta.total_ballots), '/', str(assertion.eta.total_ballots))

        return ballot_counter

