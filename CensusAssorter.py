import numpy as np
from SetEta import SetEta
from abc import ABC, abstractmethod
from CensusProfile import CensusProfile, EPSILON, STATE_IND, IN_CENSUS_IND, IN_PES_IND, CENSUS_RESIDENTS_IND, PES_RESIDENTS_IND


class CensusAssorter(ABC):
    def __init__(self, risk_limit, state_from, state_to, divider_func, state_from_constant, state_to_constant,
                 census_profile: CensusProfile, max_residents_per_household, mode=0):
        """

        :param risk_limit:
        :param state_from:
        :param state_to:
        :param divider_func:
        :param n_state_from:
        :param n_state_to:
        :param census_profile:
        :param eta:
        """
        census_data = census_profile.census_data[[STATE_IND, CENSUS_RESIDENTS_IND], :]

        self.state_from = state_from
        self.state_to = state_to
        self.divider_list = divider_func
        self.state_from_constant = state_from_constant
        self.state_to_constant = state_to_constant
        self.alpha = risk_limit
        self.mode = mode
        self.max_residents = max_residents_per_household
        self.T = 1

        self.party_from_reps = 0  # TODO write
        self.party_to_reps = 0  # TODO write

        self.z = max(divider_func(self.party_to_reps) / (2*divider_func(self.party_from_reps)), 1) * \
            max_residents_per_household
        inner_assorter_reported_margin = self.get_inner_assorter_value(census_data) - 0.5
        self.u = 0.5 + inner_assorter_reported_margin / (2*(z - inner_assorter_reported_margin))
        self.eta = SetEta(self.u, self.u - EPSILON)

        self.household_counter = 0
        self.assorter_total = 0
        self.mu = 0.5
        self.total_households = census_profile.households_n
        self.margin = self.calc_margin()
        self.census_inner_assorter_margin = self.get_inner_assorter_value(census_data) - 0.5  # m_{s_1, s_2} from the thesis

        # For debugging
        self.T_list = []
        self.assorter_mean = []


    def audit_household(self, census_residents, pes_residents):
        self.household_counter += 1
        assorter_value = self.get_assorter_value(census_residents, pes_residents)

        if self.mu == 0:
            if assorter_value > 0:
                self.T = np.inf
        else:
            self.T *= (assorter_value/self.mu) * (self.eta.value-self.mu) / (self.u-self.mu) + (self.u - self.eta.value) / \
                      (self.u - self.mu)

        self.update_mu_and_u(assorter_value)
        self.eta.calculate_eta(1, assorter_value, self.mu)  # Prepare eta for next batch
        if self.mu <= 0:
            self.T = float('inf')
        if self.mu > self.u:
            self.T = 0

        # For debugging purposes
        self.T_list.append(self.T)
        self.assorter_mean.append(self.eta.assorter_sum / self.household_counter)

        return self.T >= (1 / self.alpha), self.T

    def get_assorter_value(self, state, census_residents, pes_residents):
        """
        Calculates the value of this assorter over a given household
        :param state: State of the audited household
        :param census_residents: Number of residents in the audited household according to the census
        :param pes_residents: Number of residents in the audited household according to the PES
        :return: The value of the assorter
        """
        discrepancy = self.get_inner_assorter_value(np.array([state, pes_residents])) - \
                      self.get_inner_assorter_value(np.array([state, census_residents]))
        return 0.5 + (self.census_inner_assorter_margin + discrepancy) / (2*(self.census_inner_assorter_margin - self.z))


    def get_inner_assorter_value(self, households):
        """

        :param households: 2d numpy array. Each row is a household. First column is state, second is number of residents.
        :return: The mean of the inner assorter (a_{s_1,s_2}) over the given households
        """
        return 0  # TODO write


    def calc_margin(self):
        return 0  # TODO write


    def update_mu_and_u(self, assorter_value):
        self.assorter_total += assorter_value
        if self.total_households == self.household_counter:
            self.mu = 0.5
        else:
            self.mu = (self.total_households*0.5 - self.assorter_total) / (self.total_households - self.household_counter)
            self.mu = max(self.mu, 0)
            self.u = max(self.u, self.mu + 2*EPSILON)
        self.eta.u = self.u

    def __str__(self):
        if self.mode == 0:
            return "Census move representative from " + self.state_from + " to " + self.state_to
        elif self.mode < 0:
            return "Census move representative from " + self.state_to + " (" + str(self.mode) + ") to " + self.state_to
        else:
            return "Census move representative from " + self.state_from + " to " + self.state_to + " (" + \
                   str(self.mode) + ")"
