import numpy as np
from CensusProfile import CensusProfile, STATE_IND, IN_CENSUS_IND, IN_PES_IND, CENSUS_RESIDENTS_IND, PES_RESIDENTS_IND
from CensusAssertion import CensusAssorter
from tqdm import tqdm
import matplotlib.pyplot as plt

class CensusAuditor:
    def __init__(self, census_profile: CensusProfile, risk_limit, divisor_func, max_residents, allowed_seat_disc=0):
        self.census_profile = census_profile
        self.risk_limit = risk_limit
        self.household_data = np.copy(census_profile.census_data)

        self.assertions = []
        for i, state1 in enumerate(self.census_profile.census_allocation.keys()):
            for j in range(i):
                state2 = list(self.census_profile.census_allocation.keys())[j]
                state1_reps = self.census_profile.census_allocation[state1]
                state2_reps = self.census_profile.census_allocation[state2]
                if allowed_seat_disc == 0:
                    if state1_reps > 0:
                        self.assertions.append(CensusAssorter(risk_limit, state1, state2, divisor_func,
                                                              census_profile, max_residents, mode=allowed_seat_disc))
                    if state2_reps > 0:
                        self.assertions.append(CensusAssorter(risk_limit, state2, state1, divisor_func,
                                                              census_profile, max_residents, mode=allowed_seat_disc))
                else:
                    if state1_reps > allowed_seat_disc:
                        self.assertions.append(CensusAssorter(risk_limit, state1, state2, divisor_func,
                                                              census_profile, max_residents, mode=allowed_seat_disc))
                        if state1_reps > allowed_seat_disc:
                            self.assertions.append(CensusAssorter(risk_limit, state1, state2, divisor_func,
                                                                  census_profile, max_residents, mode=-allowed_seat_disc))
                    if state2_reps > 0:
                        self.assertions.append(CensusAssorter(risk_limit, state2, state1, divisor_func,
                                                              census_profile, max_residents, mode=allowed_seat_disc))
                        if state2_reps > allowed_seat_disc:
                            self.assertions.append(CensusAssorter(risk_limit, state2, state1, divisor_func,
                                                                  census_profile, max_residents, mode=-allowed_seat_disc))

    def audit(self):
        print("Auditing... ", self.household_data.shape[0], 'households.')
        np.random.shuffle(self.household_data)
        alpha_list = []
        second_alpha_list = []  # alpha list without the worst assertion

        for i, hh in tqdm(enumerate(self.household_data)):
            alpha = 0
            second_alpha = 0
            for j, assertion in enumerate(self.assertions):
                assertion_done, assertion_t_max = assertion.audit_household(hh)
                if i % 10**6 == 0:
                    print(assertion, assertion_t_max)
                if assertion.state_from != 0 or assertion.state_to != 1:
                    second_alpha = max(second_alpha, 1 / assertion_t_max)
                alpha = max(alpha, 1 / assertion_t_max)
            alpha_list.append(alpha)
            second_alpha_list.append(second_alpha)
            #if i % 1000 == 0 and i > 0:
            #    print(worst_assertion, " marign: ", worst_assertion.resident_margin, " assorter value", worst_assertion.exp_assorter_val)

        return alpha_list, second_alpha_list

"""
    def sample_household(self):  # TODO I was here
        unaudited_households = self.household_data[np.where[self.household_data[:, -1] == 0], :]
        sample_from_pes_prob = np.sum(unaudited_households[:, IN_PES_IND] > 0) / unaudited_households.shape[0]
        if np.random.random() <= sample_from_pes_prob:  # Sample random household from PES
            relevant_household_inds =
        else:  # Sample random household that isn't in H^{PES}
            pass


        return 0, 0, 0

"""