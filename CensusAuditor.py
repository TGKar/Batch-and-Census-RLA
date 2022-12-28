import numpy as np
from CensusProfile import CensusProfile, STATE_IND, IN_CENSUS_IND, IN_PES_IND, CENSUS_RESIDENTS_IND, PES_RESIDENTS_IND
from CensusAssorter import CensusAssorter

class CensusAuditor:

    def __init__(self, census_profile: CensusProfile, risk_limit, divider_func, state_const_dict, max_residents):
        self.census_profile = census_profile
        self.risk_limit = risk_limit
        self.household_data = np.hstack((census_profile.census_data,
                                         np.zeros(census_profile.census_data.shape[0]).reshape(-1, 1)))  # Last column is whether the household was already audited

        self.assorters = []
        for i, state1 in enumerate(self.census_profile.census_allocation.keys()):
            for j in range(i):
                state2 = list(self.census_profile.census_allocation.keys())[j]
                if self.census_profile.census_allocation[state1] > 0:
                    self.assorters.append(CensusAssorter(risk_limit, state1, state2, divider_func,
                                                         state_const_dict[state1], state_const_dict[state2],
                                                         census_profile, max_residents))
                if self.census_profile.census_allocation[state2] > 0:
                    self.assorters.append(CensusAssorter(risk_limit, state2, state1, divider_func,
                                                         state_const_dict[state2], state_const_dict[state1],
                                                         census_profile, max_residents))

    def audit(self):
        unaudited_households_inds = range(self.census_profile.households_n)
        required_households = []
        assorters_margin = []
        household_counter = 0

        while (household_counter < self.census_profile.households_n) and (len(self.assorters) > 0):
            household_to_audit = self.sample_household()
            household_counter += 1

            completed_assertion_inds = []
            for i, assorter in enumerate(self.assorters):
                assertion_done, _ = assorter.audit_household(household_to_audit)
                if assertion_done:
                    completed_assertion_inds.append(i)
            for i, delete_ind in enumerate(completed_assertion_inds):  # Remove assertions that were fulfilled
                assorter_true_mean = self.assorters[delete_ind - i].get_assorter_value(self.census_profile.census_data)


                if assorter_true_mean < 0.5:
                    print("A WRONG ASSERTION WAS APPROVED!!!")

                print("Finished assertion: ", str(self.assorters[delete_ind - i]), ' with reported margin ',
                      self.assorters[delete_ind - i].margin, 'after household ', str('{:,}'.format(household_counter)))

                required_households.append(household_counter)
                assorters_margin.append(self.assorters[delete_ind - i].margin)
                del self.assorters[delete_ind - i]

        if len(self.assorters) > 0:
            print("Remaining assertions:")
            for assorter in self.assorters:
                print(str(assorter) + ". T:" + str(assorter.T) + '. Margin: ' + str(assorter.margin) +
                      ". Reported assorter value: " + str(assorter.census_inner_assorter_margin + 0.5) +
                      '. Actual mean value: ' + str(assorter.get_assorter_value(self.census_profile.census_data)) +
                      '. Final eta assorter mean: ' + str(assorter.eta.assorter_sum / assorter.eta.total_ballots))
        else:
            print('Results approved!')

        return len(self.assorters) == 0


    def sample_household(self):  # TODO I was here
        sample_from_pes_prob = self.household_data[:, -1]
        if np.random.random() >
        sample_from_pes =


        return 0, 0, 0

