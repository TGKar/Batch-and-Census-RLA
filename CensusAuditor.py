import numpy as np
from CensusProfile import CensusProfile
from CensusAssorter import CensusAssorter

class CensusAuditor:

    def __init__(self, census_profile: CensusProfile, risk_limit, divider_func, state_const_dict, max_residents):
        self.census_profile = census_profile
        self.risk_limit = risk_limit

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
        shuffled_households_inds = range(self.census_profile.households_n)
        shuffled_households_inds = np.shuffled(shuffled_households_inds)
        assertion_required_ballots = []
        assertion_margin = []
        household_counter = 0

        while (household_counter < self.census_profile.households_n) and (len(self.assorters) > 0):
            for assorter in self.assorters:



            household_counter += 1