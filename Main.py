from ElectionProfile import ElectionProfile
from Auditor import Auditor
import numpy as np
import matplotlib.pyplot as plt


# Constants
#APPARENTMENTS = [("Avoda", "Meretz"), ("Yemina", "Tikva Hadasha"), ("Yesh Atid", "Yisrael Beytenu"), ("Likud", "Tziyonut Detit"), ("Shas", "Yahadut Hatora")] # 24!
APPARENTMENTS = [('Likud', 'Yemina'), ('Avoda', 'Kahol Lavan'), ('Yahadut Hatora', 'Shas')]  # 23!
#APPARENTMENTS = [('Kahol Lavan', 'Yisrael Beytenu'), ('Likud', 'Yemina'), ('Avoda', 'Meretz'), ('Yahadut Hatora', 'Shas')]  # 22!
THRESHOLD = 0.0325
SEATS = 120
ALPHA = 0.05
RESULTS_FILE = "Results 23.csv"

if __name__ == "__main__":

    reps = 1
    correct_approvals = 0
    correct_rejections = 0
    wrong_approvals = 0
    wrong_rejections = 0

    for i in range(reps):
        print("REPEATING: " + str(i))
        profile = ElectionProfile(RESULTS_FILE, THRESHOLD, SEATS, APPARENTMENTS, shuffle_true_tallies=False)
        auditor = Auditor(profile, ALPHA, THRESHOLD)
        audit_approves = auditor.ballot_audit()
        #audit_approves = auditor.ballot_audit()

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

        reported_matches_truth = np.all(np.array(list(profile.reported_seats_won.values())) == np.array(list(profile.true_seats_won.values())))
        print("Reported matches truth: ", reported_matches_truth)

    if reported_matches_truth and audit_approves:
        correct_approvals += 1
    elif reported_matches_truth and (not audit_approves):
        wrong_rejections += 1
    elif (not reported_matches_truth) and audit_approves:
        wrong_approvals += 1
        wrong_approvals += 1
    else:
        correct_rejections += 1
    print("FINISHED!!!")
    print("Correct approvals:", correct_approvals)
    print("Correct rejections:", correct_rejections)
    print("Wrong approvals:", wrong_approvals)
    print("Wrong rejections:", wrong_rejections)
