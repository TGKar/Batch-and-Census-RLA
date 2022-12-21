import numpy as np

EPSILON = 10**(-10)
STATE_IND = 0
IN_CENSUS_IND = 1
CENSUS_RESIDENTS_IND = 2
IN_PES_IND = 3
PES_RESIDENTS_IND = 4

class CensusProfile:
    def __init__(self, census_data):
        """

        :param census_data: Each row represents a household. First index
        """
        self.census_data = census_data
        self.households_n = census_data.shape[1]
        self.census_allocation = dict()  # TODO write
        self.pes_allocation = dict()  # TODO write
