import numpy as np
from collections import Counter

REPS_N = 435
MAX_RESIDENTS = 8
EPSILON = 10**(-10)
STATE_IND = 0
IN_CENSUS_IND = 1
CENSUS_RESIDENTS_IND = 2
IN_PES_IND = 3
PES_RESIDENTS_IND = 4

#US_DIVISOR_FUNC = lambda r: np.sqrt(r * (r+1))

# Data file names
STATE_POP_FILE = 'state_pop_small.npy'  # 'state_pop.npy'
HOUSEHOLD_RESIDENTS_P_FILE = 'household_residents_p.npy'

def US_DIVISOR_FUNC(r):
    return np.sqrt(r * (r+1))

class CensusProfile:
    def __init__(self, census_data, representatives_n, dividers_func, state_constants):
        """

        :param census_data: Each row represents a household. First index
        """
        self.census_data = census_data
        self.representatives_n = representatives_n
        self.dividers_func = dividers_func
        self.state_constants = self.sort_dict(state_constants)  # Sorting so all dictionaries have matching keys and values
        self.households_n = census_data.shape[0]
        self.census_allocation = self.calculate_allocation(census_data[:, [STATE_IND, CENSUS_RESIDENTS_IND]])
        self.pes_allocation = self.calculate_allocation(census_data[:, [STATE_IND, PES_RESIDENTS_IND]])
        assert(np.allclose(list(self.census_allocation.values()), list(self.pes_allocation.values())))


    def calculate_allocation(self, households):
        """

        :param households: A 2d array. First index is states, second is number of residents.
        :return: A dictionary where the keys are the states and the values are the number of representatives they're allocated
        """
        # Create dictionary with number of residents at each state
        residents_dict = dict()
        for state in self.state_constants.keys():
            residents_dict[state] = np.sum(households[np.where(households[:, 0] == state), 1]) + self.state_constants[state]
        residents_dict = self.sort_dict(residents_dict)

        # Create price table
        state_pops_list = np.array(list(residents_dict.values()), dtype=np.float)
        state_consts_list = np.array(list(self.state_constants.values()), dtype=np.float)
        dividers = np.vectorize(self.dividers_func)(np.arange(1, self.representatives_n + 1))
        price_table = state_pops_list.reshape(-1, 1) / dividers.reshape(1, -1)
        # price_table += state_consts_list.reshape(-1, 1)

        # Calculate and return each state's number of representatives
        price_rank_table = price_table.ravel().argsort().argsort().reshape(price_table.shape)
        representative_winning_table = price_rank_table >= (price_rank_table.size - self.representatives_n)
        return dict(zip(residents_dict.keys(), list(np.sum(representative_winning_table, axis=-1))))

    @staticmethod
    def sort_dict(d):
        return dict(sorted(d.items(), key=lambda item: item[0]))

    @staticmethod
    def generate_census_data(noisy_pes=False, household_mismatch=0.005):
        state_pop = np.load(STATE_POP_FILE)
        household_residents_p = np.load(HOUSEHOLD_RESIDENTS_P_FILE)
        mean_residents_per_hh = np.sum(household_residents_p * np.arange(len(household_residents_p)))
        state_households = (1+household_mismatch) * state_pop / mean_residents_per_hh
        state_households = state_households.astype(int)
        household_n = np.sum(state_households)

        # create household_data matrix and fill with household states
        household_data = np.zeros((household_n, 5), dtype=int)
        curr_index = 0
        state_inds = [0]
        for i in range(len(state_pop)):
            only_pes_hh_num = int(state_households[i] * household_mismatch / 2)
            only_cen_hh_num = int(state_households[i] * household_mismatch) - only_pes_hh_num
            household_data[curr_index:(curr_index + state_households[i]), STATE_IND] = i
            household_data[curr_index:(curr_index + state_households[i] - only_cen_hh_num), IN_PES_IND] = 1
            household_data[curr_index:(curr_index + state_households[i] - only_cen_hh_num - only_pes_hh_num), IN_CENSUS_IND] = 1
            household_data[(curr_index + state_households[i] - only_cen_hh_num):(curr_index + state_households[i]), IN_CENSUS_IND] = 1
            curr_index += state_households[i]
            state_inds.append(curr_index)

        # Draw household resident counts
        household_data[:, CENSUS_RESIDENTS_IND] = np.random.choice(len(household_residents_p), household_n, p=household_residents_p)
        household_data[:, PES_RESIDENTS_IND] = household_data[:, CENSUS_RESIDENTS_IND]
        household_data[np.where(household_data[:, IN_CENSUS_IND] == 0), CENSUS_RESIDENTS_IND] = 0
        household_data[np.where(household_data[:, IN_PES_IND] == 0), PES_RESIDENTS_IND] = 0
        if noisy_pes:
            pass  # TODO implement

        # Create state_consts to balance state population discrepancies
        state_consts = dict()  # state_const - census_state_population = true_state_population
        for i in range(len(state_pop)):
            state_consts[i] = state_pop[i] - np.sum(household_data[state_inds[i]:state_inds[i + 1], CENSUS_RESIDENTS_IND])
            assert state_consts[i] + np.sum(household_data[np.where(household_data[:, STATE_IND] == i), CENSUS_RESIDENTS_IND])

        return CensusProfile(household_data, REPS_N, US_DIVISOR_FUNC, state_consts)

