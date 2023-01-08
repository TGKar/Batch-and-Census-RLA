import numpy as np

EPSILON = 10**(-10)
STATE_IND = 0
IN_CENSUS_IND = 1
CENSUS_RESIDENTS_IND = 2
IN_PES_IND = 3
PES_RESIDENTS_IND = 4

# Possible values of the census_data[:, IN_PES_IND]
OUT_OF_PES = 0  # Household not included in pes households
IN_PES_UNSURVEYED = 1  # Household is included in PES households, but was not surveyed during the PES
IN_PES_SURVEYED = 2  # Household is included in PES and was re-surveyed during it.

# Data file names
STATE_POP_FILE = 'state_pop.npy'
HOUSEHOLD_RESIDENTS_P_FILE = 'household_residents_p.npy'

class CensusProfile:
    def __init__(self, census_data, representatives_n, dividers_func, state_constants):
        """

        :param census_data: Each row represents a household. First index
        """
        self.census_data = census_data
        self.representatives_n = representatives_n
        self.dividers_func = dividers_func
        self.state_constants = self.sort_dict(state_constants)  # Sorting so all dictionaries have matching keys and values
        self.households_n = census_data.shape[1]
        self.census_allocation = self.calculate_allocation(census_data[[STATE_IND, CENSUS_RESIDENTS_IND], :])
        self.pes_allocation = self.calculate_allocation(census_data[[STATE_IND, PES_RESIDENTS_IND], :])

    def calculate_allocation(self, households):
        """

        :param households: A 2d array. First index is states, second is number of residents.
        :return: A dictionary where the keys are the states and the values are the number of representatives they're allocated
        """
        # Create dictionary with number of residents at each state
        residents_dict = dict()
        for state in self.state_constants.keys():
            residents_dict[state] = np.sum(households[np.where(households[:, 0] == state)])
        residents_dict = self.sort_dict(residents_dict)

        # Create price table
        dividers = np.vectorize(self.dividers_func)(np.arange(1, self.representatives_n + 1))
        price_table = np.array(list(residents_dict.values()), dtype=np.float).reshape(-1, 1) / dividers.reshape(1, -1)
        price_table += np.array(self.state_constants.values()).reshape(-1, 1)

        # Calculate and return each state's number of representatives
        price_rank_table = price_table.ravel().argsort().argsort().reshape(price_table.shape)
        representative_winning_table = price_rank_table >= (price_rank_table.size - self.representatives_n)
        return dict(zip(residents_dict.keys(), list(np.sum(representative_winning_table, axis=-1))))

    @staticmethod
    def sort_dict(d):
        return dict(sorted(d.items(), key=lambda item: item[0]))

    @staticmethod
    def generate_census_data(noisy_pes=False):
        states_pop = np.load(STATE_POP_FILE)
        household_residents_p = np.load(HOUSEHOLD_RESIDENTS_P_FILE)
        avg_residents_per_hh = np.mean(household_residents_p * np.arange(len(household_residents_p)))
        census_
        for pop in states_pop