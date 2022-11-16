from Auditor import Auditor
from Assorter import Assorter
import matplotlib.pyplot as plt
import numpy as np

ASSERTION_LABELS = ['Passed Threshold', 'Failed Threshold', 'Move Seat Between Parties']

# Assertion dictionary indexes
ASSERTION_TYPE_IND = 0
ALPHA_REQ_BALLOTS_IND = 1
BATCHCOMP_REQ_BALLOTS_IND = 2
MARGIN_IND = 3


def assertions_comparison_plots(alpha_assertions_list, batchcomp_assertions_list, total_voters, knesset_num):
    assertion_data = dict()  # Contains lists of required ballots using ALPHA / batchcomp and the assertion's margin

    # Create dictionary of assertions that holds the # of audited ballots for each method
    for alpha_assertions in alpha_assertions_list:
        for i, assertion in enumerate(alpha_assertions):
            if assertion.type == 1 or assertion.type == 2:
                name = (assertion.party, '-')
            else:
                name = (assertion.party_from, assertion.party_to)
            if name not in assertion_data:
                assertion_data[name] = [0]*4
                assertion_data[name][ASSERTION_TYPE_IND] = assertion.type
                assertion_data[name][MARGIN_IND] = assertion.vote_margin
            assertion_data[name][ALPHA_REQ_BALLOTS_IND] += assertion.ballots_examined

    for batchcomp_assertions in batchcomp_assertions_list:
        for assertion in batchcomp_assertions:
            if assertion.type == 1 or assertion.type == 2:
                name = (assertion.party, '-')
            else:
                name = (assertion.party_from, assertion.party_to)
            assertion_data[name][BATCHCOMP_REQ_BALLOTS_IND] += assertion.ballots_examined

    assertion_data_mat = np.array(list(assertion_data.values()))
    assertion_data_mat[:, [ALPHA_REQ_BALLOTS_IND, BATCHCOMP_REQ_BALLOTS_IND]] /= len(alpha_assertions_list)  # Average over all repetitions
    max_margin = max(assertion_data_mat[:, MARGIN_IND])

    # Plot comparison
    fig, axs = plt.subplots(2, 1, sharex=True, sharey=True)
    for i, lab in enumerate(ASSERTION_LABELS):
        slicer = np.where(assertion_data_mat[:, ASSERTION_TYPE_IND] == i + 1)
        axs[0].scatter(assertion_data_mat[slicer, MARGIN_IND], assertion_data_mat[slicer, ALPHA_REQ_BALLOTS_IND], label=lab)
        axs[1].scatter(assertion_data_mat[slicer, MARGIN_IND], assertion_data_mat[slicer, BATCHCOMP_REQ_BALLOTS_IND], label=lab)
    axs[0].plot([0, max_margin], [total_voters, total_voters], '--', label='Total Voters')
    axs[1].plot([0, max_margin], [total_voters, total_voters], '--', label='Total Voters')
    axs[0].set_xlim((0, max_margin + total_voters / 10**5))
    axs[0].legend()
    fig.suptitle("Knesset " + str(knesset_num) + ' - Required # of Ballots vs. Assorter Margin')
    axs[0].set_title("ALPHA-Batch")
    axs[1].set_title("Batchcomp")
    fig.supxlabel("Assertion Margin")
    fig.supylabel("Required Ballots")
    plt.show()

    # Plot Difference
    diff = assertion_data_mat[:, ALPHA_REQ_BALLOTS_IND] - assertion_data_mat[:, BATCHCOMP_REQ_BALLOTS_IND]
    for i, lab in enumerate(ASSERTION_LABELS):
        slicer = np.where(assertion_data_mat[:, ASSERTION_TYPE_IND] == i + 1)
        plt.scatter(assertion_data_mat[slicer, MARGIN_IND], diff[slicer], label=lab)
        plt.plot([0, max_margin], [0, 0], '--')
    plt.xlim((-total_voters / 10**5, max_margin + total_voters / 10**5))
    plt.legend()
    plt.title("Knesset " + str(knesset_num) + ' - Required # of Ballots Per Assertion: Difference Betewen ALPHA and Batchcomp')
    plt.xlabel("Assertion Margin")
    plt.ylabel("Required Ballots")
    plt.show()


