from ElectionProfile import ElectionProfile
from ThresholdAssertion import ThresholdAssertion
from Auditor import Auditor
import numpy as np
import matplotlib.pyplot as plt


# Constants
# APPARENTMENTS = [("Avoda", "Meretz"), ("Yemina", "Tikva Hadasha"), ("Yesh Atid", "Yisrael Beytenu"), ("Likud", "Tziyonut Detit"), ("Shas", "Yahadut Hatora")] 24!!!
# APPARENTMENTS = [('Likud', 'Yemina'), ('Avoda', 'Kahol Lavan'), ('Yahadut Hatora', 'Shas')] 23!
APPARENTMENTS = [('Kahol Lavan', 'Yisrael Beytenu'), ('Likud', 'Yemina'), ('Avoda', 'Meretz'), ('Yahadut Hatora', 'Shas')]  # 22!
THRESHOLD = 0.0325
SEATS = 120
ALPHA = 0.05

if __name__ == "__main__":


    profile = ElectionProfile("Results 22.csv", THRESHOLD, SEATS, APPARENTMENTS)
    auditor = Auditor(profile, ALPHA, THRESHOLD)
    auditor.audit()

    print("Reported Results:")
    print(profile.reported_seats_won)
    print("True Results:")
    print(profile.true_seats_won)
    print("Reported Tally:")
    print(profile.tot_batch.reported_tally)
    print("True Tally:")
    print(profile.tot_batch.true_tally)
    print("True threshold:", profile.threshold * (profile.tot_batch.total_votes-profile.tot_batch.true_invalid_votes),
          'total voters: ', profile.tot_batch.total_votes)

    print("Reported matches truth: ", np.all(np.array(list(profile.reported_seats_won.values())) == np.array(list(profile.true_seats_won.values()))))
