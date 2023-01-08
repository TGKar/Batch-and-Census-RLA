from ElectionProfile import ElectionProfile
from ElectionAuditor import Auditor
from PluralityAuditor import PluralityAuditor
import numpy as np
import matplotlib.pyplot as plt
import Plotter
from tqdm import tqdm

# Constants
KNESSET_NUM = 25
APPARENTMENTS = dict()
APPARENTMENTS[25] = [("Hamahane Hamamlahti", "Yesh Atid"), ("Likud", "Tziyonut Detit"), ("Shas", "Yahadut Hatora")] # ("Meretz", "Avoda"), ("Balad", "Hadash Taal"), ("Yisrael Beytenu", "Raam")
APPARENTMENTS[24] = [("Avoda", "Meretz"), ("Yemina", "Tikva Hadasha"), ("Yesh Atid", "Yisrael Beytenu"), ("Likud", "Tziyonut Detit"), ("Shas", "Yahadut Hatora")]
APPARENTMENTS[23] = [('Likud', 'Yemina'), ('Avoda', 'Kahol Lavan'), ('Yahadut Hatora', 'Shas')]
APPARENTMENTS[22] = [('Kahol Lavan', 'Yisrael Beytenu'), ('Likud', 'Yemina'), ('Avoda', 'Meretz'), ('Yahadut Hatora', 'Shas')]
THRESHOLD = 0.0325
SEATS = 120
ALPHA = 0.05
RESULTS_FILE = 'Results ' + str(KNESSET_NUM) + '.csv'
ELECTION_NAME = "Knesset " + str(KNESSET_NUM)


"""
def plurality_race():
    reported_tally = {'p1': 380, 'p2': 310, 'p3': 310}
    true_ballots = ['p1']*reported_tally['p1'] + ['p2']*reported_tally['p2'] + ['p3']*reported_tally['p3']
    ballot_counter = 0
    for _ in range(1000):
        profile = ElectionProfile(reported_tally, true_ballots)
        auditor = PluralityAuditor(profile, ALPHA)
        ballot_counter += auditor.ballot_audit()
    print(ballot_counter / 1000)


def make_batchcomp_plot(profile, alpha=ALPHA, threshold=THRESHOLD):
    auditor = Auditor(profile, alpha, threshold)
    audit_approves, assertions = auditor.batch_audit()
    if audit_approves:
        Plotter.assertions_plot(assertions, profile.tot_batch.total_votes)
"""

def make_comp_plot(profile, knesset_num, reps=10, alpha=ALPHA, threshold=THRESHOLD):
    batchcomp_assertions_list = []
    alpha_assertions_list = []
    for rep in range(reps):
        batchcomp_auditor = Auditor(profile, alpha, threshold)
        alpha_auditor = Auditor(profile, alpha, threshold, bathcomp=False)

        batchcomp_audit_approves, batchcomp_assertions = batchcomp_auditor.batch_audit()
        alpha_audit_approves, alpha_assertions = alpha_auditor.batch_audit()
        assert alpha_audit_approves and batchcomp_audit_approves
        alpha_assertions_list.append(alpha_assertions)
        batchcomp_assertions_list.append(batchcomp_assertions)

    Plotter.assertions_comparison_plots(alpha_assertions_list, batchcomp_assertions_list, profile.tot_batch.total_votes,
                                        len(profile.batches), knesset_num)

def make_error_plot(reps=10, alpha=ALPHA, threshold=THRESHOLD):
    for knesset_i in [23, 24]:
        noised_assertions_list = []
        unnoised_assertions_list = []
        unnoised_profile = ElectionProfile('Results ' + str(knesset_i) + '.csv', THRESHOLD, SEATS, APPARENTMENTS[knesset_i])
        for rep in range(reps):
            noised_profile = ElectionProfile('Results ' + str(knesset_i) + '.csv', THRESHOLD, SEATS, APPARENTMENTS[knesset_i], noise=True)
            noised_auditor = Auditor(noised_profile, alpha, threshold)
            unnoised_auditor = Auditor(unnoised_profile, alpha, threshold)

            noised_audit_approves, noised_assertions = noised_auditor.batch_audit()
            unnoised_audit_approves, unnoised_assertions = unnoised_auditor.batch_audit()
            assert unnoised_audit_approves and noised_audit_approves
            unnoised_assertions_list.append(unnoised_assertions)
            noised_assertions_list.append(noised_assertions)

        Plotter.assertions_with_error_plots(unnoised_assertions_list, noised_assertions_list, unnoised_profile.tot_batch.total_votes,
                                            len(unnoised_profile.batches), knesset_i)


def make_prediction_plots(profiles, reps=10, alpha=ALPHA, threshold=THRESHOLD):
    assertions_lists = []
    for profile in tqdm(profiles):
        assertions_list = []
        for rep in range(reps):
            auditor = Auditor(profile, alpha, threshold)
            audit_approves, assertions = auditor.batch_audit()
            assert audit_approves
            assertions_list.append(assertions)
        assertions_lists.append(assertions_list)

    Plotter.prediction_plots(assertions_lists)


def old_plot(profile, reps=1):
    correct_approvals = 0
    correct_rejections = 0
    wrong_approvals = 0
    wrong_rejections = 0

    for i in range(reps):
        print("REPEATING: " + str(i))
        auditor = Auditor(profile, ALPHA, THRESHOLD)
        audit_approves, assertions = auditor.batch_audit()

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
        else:
            correct_rejections += 1
    print("FINISHED!!!")
    print("Correct approvals:", correct_approvals)
    print("Correct rejections:", correct_rejections)
    print("Wrong approvals:", wrong_approvals)
    print("Wrong rejections:", wrong_rejections)


if __name__ == "__main__":
    election_profiles = []
    #prof = ElectionProfile(RESULTS_FILE, THRESHOLD, SEATS, APPARENTMENTS[KNESSET_NUM])

    # make_error_plot(1)

    #make_comp_plot(prof, KNESSET_NUM, reps=1)
    for knesset_i in [22, 23, 24]:
        prof = ElectionProfile('Results ' + str(knesset_i) + '.csv', THRESHOLD, SEATS, APPARENTMENTS[knesset_i])
        make_comp_plot(prof, knesset_i, reps=10)
        #election_profiles.append(prof)
    make_error_plot()
    #make_prediction_plots(election_profiles)
