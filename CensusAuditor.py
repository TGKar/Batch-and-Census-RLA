import numpy as np
from CensusProfile import CensusProfile, STATE_IND, IN_CENSUS_IND, IN_PES_IND, CENSUS_RESIDENTS_IND, PES_RESIDENTS_IND
from CensusAssorter import CensusAssorter
from tqdm import tqdm
class CensusAuditor:
    def __init__(self, census_profile: CensusProfile, risk_limit, divisor_func, max_residents):
        self.census_profile = census_profile
        self.risk_limit = risk_limit
        self.household_data = np.copy(census_profile.census_data)

        self.assertions = []
        for i, state1 in enumerate(self.census_profile.census_allocation.keys()):
            for j in range(i):
                state2 = list(self.census_profile.census_allocation.keys())[j]
                if self.census_profile.census_allocation[state1] > 0:
                    self.assertions.append(CensusAssorter(risk_limit, state1, state2, divisor_func,
                                                          census_profile, max_residents))
                if self.census_profile.census_allocation[state2] > 0:
                    self.assertions.append(CensusAssorter(risk_limit, state2, state1, divisor_func,
                                                          census_profile, max_residents))

    def audit(self):
        print("Auditing...")
        np.random.shuffle(self.household_data)
        alpha_list = []

        for i, hh in enumerate(self.household_data):
            alpha = 0
            for j, assorter in enumerate(self.assertions):
                assertion_done, assertion_t_max = assorter.audit_household(hh)
                alpha = max(alpha, 1 / assertion_t_max)
            alpha_list.append(alpha)
        return alpha_list

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