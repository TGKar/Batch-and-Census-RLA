from ElectionProfile import ElectionProfile
from ElectionAuditor import ElectionAuditor
from CensusProfile import CensusProfile, US_DIVISOR_FUNC, DHONDT_DIVISOR_FUNC, MAX_RESIDENTS
from CensusAuditor import CensusAuditor
import Plotter
from tqdm import tqdm
import pickle

# Constants
KNESSET_NUM = 25
APPARENTMENTS = dict()
APPARENTMENTS[25] = [("Hamahane Hamamlahti", "Yesh Atid"), ("Likud", "Tziyonut Detit"), ("Shas", "Yahadut Hatora")]
APPARENTMENTS[24] = [("Avoda", "Meretz"), ("Yemina", "Tikva Hadasha"), ("Yesh Atid", "Yisrael Beytenu"), ("Likud", "Tziyonut Detit"), ("Shas", "Yahadut Hatora")]
APPARENTMENTS[23] = [('Likud', 'Yemina'), ('Avoda', 'Kahol Lavan'), ('Yahadut Hatora', 'Shas')]
APPARENTMENTS[22] = [('Kahol Lavan', 'Yisrael Beytenu'), ('Likud', 'Yemina'), ('Avoda', 'Meretz'), ('Yahadut Hatora', 'Shas')]
THRESHOLD = 0.0325
SEATS = 120
ALPHA = 0.05
RESULTS_FILE = 'Results ' + str(KNESSET_NUM) + '.csv'
ELECTION_NAME = "Knesset " + str(KNESSET_NUM)


def make_comp_plot(profile, knesset_num, reps=10, alpha=ALPHA, threshold=THRESHOLD):
    """
    Makes comparison plots between Batchcomp and ALPHA-Batch
    :param profile: Election profile
    :param knesset_num: Knesset number
    :param reps: Simulation repetitions
    :param alpha: risk-limit
    :param threshold: Electoral threshold
    """
    batchcomp_assertions_list = []
    alpha_assertions_list = []
    for rep in range(reps):
        batchcomp_auditor = ElectionAuditor(profile, alpha, threshold)
        alpha_auditor = ElectionAuditor(profile, alpha, threshold, bathcomp=False)

        batchcomp_audit_approves, batchcomp_assertions = batchcomp_auditor.batch_audit()
        alpha_audit_approves, alpha_assertions = alpha_auditor.batch_audit()
        # assert alpha_audit_approves and batchcomp_audit_approves
        alpha_assertions_list.append(alpha_assertions)
        batchcomp_assertions_list.append(batchcomp_assertions)

    Plotter.assertions_comparison_plots(alpha_assertions_list, batchcomp_assertions_list, profile.tot_batch.total_votes,
                                        len(profile.batches), knesset_num)

def make_error_plot(reps=10, alpha=ALPHA, threshold=THRESHOLD):
    """
    Makes with / without counting error plots
    :param reps: simulation repititions
    :param alpha: risk-limit
    :param threshold: Electoral threshold
    """
    for knesset_i in [23, 24]:
        noised_assertions_list = []
        unnoised_assertions_list = []
        unnoised_profile = ElectionProfile('Results ' + str(knesset_i) + '.csv', THRESHOLD, SEATS, APPARENTMENTS[knesset_i])
        for rep in range(reps):
            noised_profile = ElectionProfile('Results ' + str(knesset_i) + '.csv', THRESHOLD, SEATS, APPARENTMENTS[knesset_i], noise=True)
            noised_auditor = ElectionAuditor(noised_profile, alpha, threshold)
            unnoised_auditor = ElectionAuditor(unnoised_profile, alpha, threshold)

            noised_audit_approves, noised_assertions = noised_auditor.batch_audit()
            unnoised_audit_approves, unnoised_assertions = unnoised_auditor.batch_audit()
            assert unnoised_audit_approves and noised_audit_approves
            unnoised_assertions_list.append(unnoised_assertions)
            noised_assertions_list.append(noised_assertions)

        Plotter.assertions_with_error_plots(unnoised_assertions_list, noised_assertions_list, unnoised_profile.tot_batch.total_votes,
                                            len(unnoised_profile.batches), knesset_i)

"""
def make_prediction_plots(profiles, reps=10, alpha=ALPHA, threshold=THRESHOLD):
    assertions_lists = []
    for profile in tqdm(profiles):
        assertions_list = []
        for rep in range(reps):
            auditor = ElectionAuditor(profile, alpha, threshold)
            audit_approves, assertions = auditor.batch_audit()
            assert audit_approves
            assertions_list.append(assertions)
        assertions_lists.append(assertions_list)

    Plotter.prediction_plots(assertions_lists)
"""

def make_census_plot(error_rate=0.0, household_mismatch=0.0, reps=10, allowed_seat_disc=0):
    """
    Makes the census risk-limit plot
    :param error_rate: share of household disagreement between census and PES
    :param household_mismatch: Share of households that are only in one of the census / PES
    :param reps: Simulation repetitions
    :param allowed_seat_disc: maximal allowed discrepancy between census and PES allocation.
    """
    alpha_lists = []
    second_alpha_lists = []
    for i in range(reps):
        print("Iteration ", i)
        profile = CensusProfile.generate_census_data(DHONDT_DIVISOR_FUNC, pes_noise=error_rate, household_mismatch=household_mismatch)
        auditor = CensusAuditor(profile, 10**(-100), DHONDT_DIVISOR_FUNC, MAX_RESIDENTS, allowed_seat_disc=allowed_seat_disc)
        alphas, second_alphas = auditor.audit()
        alpha_lists.append(alphas)
        second_alpha_lists.append(second_alphas)

    title = None
    if error_rate > 0.0:
        title = 'Risk-Limit by Share of Households Examined During the PES - ' + str(int(100*error_rate)) + r'\%+' + ' Census and PES Disagreement'

    Plotter.census_plot(alpha_lists, allowed_seat_disc, max_x=0.02, title=title)
    Plotter.census_plot(second_alpha_lists, allowed_seat_disc)

if __name__ == "__main__":
    election_profiles = []
    prof = ElectionProfile(RESULTS_FILE, THRESHOLD, SEATS, APPARENTMENTS[KNESSET_NUM])
    for knesset_i in [22, 23, 24]:
        prof = ElectionProfile('Results ' + str(knesset_i) + '.csv', THRESHOLD, SEATS,  APPARENTMENTS[knesset_i])
        make_comp_plot(prof, knesset_i, reps=10)
        election_profiles.append(prof)
    make_error_plot(reps=10)
    make_census_plot(reps=10, error_rate=0.0)
    make_census_plot(reps=10, error_rate=0.05)