from math import ceil

import numpy as np
from SetEta import SetEta
from abc import ABC, abstractmethod
from CensusProfile import CensusProfile, EPSILON, STATE_IND, IN_CENSUS_IND, IN_PES_IND, CENSUS_RESIDENTS_IND, PES_RESIDENTS_IND

MAX_ERR = 10**(-10)

class CensusAssorter(ABC):
    def __init__(self, risk_limit, state_from, state_to, divisor_func, census_profile: CensusProfile,
                 max_residents_per_household, mode=0):
        """

        :param risk_limit:
        :param state_from:
        :param state_to:
        :param divisor_func:
        :param n_state_from:
        :param n_state_to:
        :param census_profile:
        :param eta:
        """
        census_data = census_profile.census_data[:, [STATE_IND, CENSUS_RESIDENTS_IND]]

        self.state_from = state_from
        self.state_to = state_to
        self.divisor_func = divisor_func
        self.state_from_constant = census_profile.state_constants[state_from]
        self.state_to_constant = census_profile.state_constants[state_to]
        self.alpha = risk_limit
        self.mode = mode
        self.max_residents = max_residents_per_household
        self.T = 1
        self.T_max = 1
        self.households_n = census_profile.households_n
        self.state_from_reps = census_profile.census_allocation[state_from] + min(mode, 0)
        self.state_to_reps = census_profile.census_allocation[state_to] + max(mode, 0)
        assert self.state_to_reps >= 0
        assert self.state_from_reps > 0
        self.c, self.z = self.calculate_constants()
        inner_assorter_reported_margin = self.get_inner_assorter_value(census_data) - 0.5
        if inner_assorter_reported_margin < 0:
            inner_assorter_reported_margin = self.get_inner_assorter_value(census_data) - 0.5
        self.u = 0.5 + (inner_assorter_reported_margin + MAX_ERR) / (2*(self.z - inner_assorter_reported_margin))
        self.eta = SetEta(self.u, self.u - EPSILON)

        self.household_counter = 0
        self.assorter_total = 0
        self.mu = 0.5
        self.households_n = census_profile.households_n
        state_from_pop = np.sum(census_data[np.where(census_data[:, 0] == state_from), 1]) + self.state_from_constant
        state_to_pop = np.sum(census_data[np.where(census_data[:, 0] == state_to), 1]) + self.state_to_constant
        self.resident_margin = self.calc_margin(state_from_pop, state_to_pop)
        self.hh_margin = ceil(self.resident_margin / self.max_residents)
        self.census_inner_assorter_margin = self.get_inner_assorter_value(census_data) - 0.5  # m_{s_1, s_2} from the thesis
        if self.census_inner_assorter_margin < 0:
            self.get_inner_assorter_value(census_data) - 0.5

        # For debugging
        self.T_list = []
        self.assorter_mean = []
        self.exp_assorter_val = 0.5 + inner_assorter_reported_margin / (2*(self.z - inner_assorter_reported_margin))

        print(self, "Margin ", self.resident_margin, ". exp assorter value ", self.exp_assorter_val,
              "state from pop:", state_from_pop, "seats: ", self.state_from_reps, ". State to pop:", state_to_pop, "seats:",
              self.state_to_reps)

    def audit_household(self, household):
        self.household_counter += 1

        if not (self.T <= 0 or self.T == np.inf):  # If assertion is not proved right / proved wrong yet
            if household.ndim == 1:
                household = household.reshape((1, -1))
            assorter_value = self.get_assorter_value(household)
            if assorter_value < 0.5 and (household[0, CENSUS_RESIDENTS_IND] == household[0, PES_RESIDENTS_IND]):
                print(self, ' assorter value < 0.5')
                self.get_assorter_value(household)

            if self.mu == 0:
                if assorter_value > 0:
                    self.T = np.inf
            else:
                if (assorter_value/self.mu) * (self.eta.value-self.mu) / (self.u-self.mu) + (self.u-self.eta.value) / (self.u - self.mu) > 10:  # TODO delete
                    print('Overflow incoming?')
                    print('mu ', self.mu, ' eta ', self.eta.value, ' u ', self.u, ' assorter value ', assorter_value)
                self.T *= (assorter_value/self.mu) * (self.eta.value-self.mu) / (self.u-self.mu) + (self.u-self.eta.value) / (self.u - self.mu)

            self.update_mu_and_u(assorter_value)
            self.eta.calculate_eta(1, assorter_value, self.mu)  # Prepare eta for next batch
            if self.mu <= 0 or self.T > 1 / self.alpha:
                self.T = float('inf')
            if self.mu > self.u:
                self.T = 0

        # For debugging purposes
        self.T_list.append(self.T)
        self.assorter_mean.append(self.eta.assorter_sum / self.household_counter)

        self.T_max = max(self.T_max, self.T)
        return self.T_max >= (1 / self.alpha), self.T_max

    def get_assorter_value(self, households):
        """
        Calculates the mean of this census assorter over a number of households.
        :param households: 2d numpy array. Each row is a household. The first column is the household's state, second
        is the number of residents according to the census, third is the number of residents according to the PES.
        :return: The mean of the assorter (A_{s_1,s_2}) over the given households
        """
        discrepancy = self.get_inner_assorter_value(households[:, [STATE_IND, PES_RESIDENTS_IND]]) - \
                      self.get_inner_assorter_value(households[:, [STATE_IND, CENSUS_RESIDENTS_IND]])
        return 0.5 + (self.census_inner_assorter_margin + discrepancy) / (2*(self.z - self.census_inner_assorter_margin))

    def get_inner_assorter_value(self, households):
        """
        :param households: 2d numpy array. Each row is a household. The first column is the household's state, second
        is the number of residents according to the census, third is the number of residents according to the PES.
        :return: The mean of the inner assorter (a_{s_1,s_2}) over the given households
        """
        state_from_residents = households[:, 1] * (households[:, 0] == self.state_from)
        state_to_residents = households[:, 1] * (households[:, 0] == self.state_to)
        state_from_divisor = self.divisor_func(self.state_from_reps)
        state_to_divisor = self.divisor_func(self.state_to_reps + 1)
        return np.mean((state_from_residents / (self.c*state_from_divisor)) + \
               ((self.max_residents - state_to_residents) / (self.c*state_to_divisor)))

    def update_mu_and_u(self, assorter_value):
        self.assorter_total += assorter_value
        if self.households_n == self.household_counter:
            self.mu = 0.5
        else:
            self.mu = (self.households_n * 0.5 - self.assorter_total) / (self.households_n - self.household_counter)
            self.mu = max(self.mu, 0)
            self.u = max(self.u, self.mu + 2*EPSILON)
        self.eta.u = self.u

    def calculate_constants(self):
        state_from_d = self.divisor_func(self.state_from_reps)
        state_to_d = self.divisor_func(self.state_to_reps + 1)
        c = 2 * ((self.max_residents/state_to_d) + (self.state_to_constant / (self.households_n * state_to_d))
                 - (self.state_from_constant / (self.households_n * state_from_d)))
        z = max(1 / (state_from_d*c), 1 / (state_to_d*c), 0) * self.max_residents
        return c, z

    def calc_margin(self, state_from_pop, state_to_pop):

        state_from_divisor = self.divisor_func(self.state_from_reps)
        state_to_divisor = self.divisor_func(self.state_to_reps + 1)
        residents_margin = (state_from_pop / state_from_divisor - state_to_pop / state_to_divisor) / \
                      ((1/state_from_divisor) + (1/state_to_divisor))
        assert residents_margin >= 0
        return residents_margin

    def __str__(self):
        if self.mode == 0:
            return "Census move representative from " + str(self.state_from) + " to " + str(self.state_to)
        elif self.mode < 0:
            return "Census move representative from " + str(self.state_from) + " (" + str(self.mode) + ") to " + str(self.state_to)
        else:
            return "Census move representative from " + str(self.state_from) + " to " + str(self.state_to) + " (" + \
                   str(self.mode) + ")"
