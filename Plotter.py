from Auditor import Auditor
from Assorter import Assorter
import matplotlib.pyplot as plt
import numpy as np


ELECTION_NAME = "Knesset 25"
ASSERTION_LABELS = ['Passed Threshold', 'Failed Threshold', 'Move Seat Between Parties']

# Assertion dictionary indexes
ASSERTION_TYPE_IND = 0
ALPHA_REQ_BALLOTS_IND = 1
BATCHCOMP_REQ_BALLOTS_IND = 2
MARGIN_IND = 3


def assertions_plot(assertions, total_voters):
    required_ballots_moveseat = []
    margin_moveseat = []
    required_ballots_threshold = []
    margin_threshold = []
    required_ballots_failed = []
    margin_failed = []

    for assertion in assertions:
        if assertion.type == 1:
            required_ballots_threshold.append(assertion.ballots_examined)
            margin_threshold.append(assertion.vote_margin)
        elif assertion.type == 2:
            required_ballots_failed.append(assertion.ballots_examined)
            margin_failed.append(assertion.vote_margin)
        elif assertion.type == 3:
            required_ballots_moveseat.append(assertion.ballots_examined)
            margin_moveseat.append(assertion.vote_margin)

    max_margin = max(margin_failed + margin_moveseat + margin_threshold)
    plt.scatter(margin_threshold, required_ballots_threshold, label='Passed Threshold')
    plt.scatter(margin_failed, required_ballots_failed, label='Failed Threshold')
    plt.scatter(margin_moveseat, required_ballots_moveseat, label='Move Seat Between Parties')
    plt.plot([0, max_margin],
             [total_voters, total_voters], '--',
             label='Total Voters')
    plt.xlim((-10000, max_margin + 10000))
    plt.legend()
    plt.title(ELECTION_NAME + ' - Required # of Ballots vs. Assorter Margin')
    plt.xlabel("Assertion Margin")
    plt.ylabel("Required Ballots")
    plt.show()


def assertions_comparison_plots(alpha_assertions, batchcomp_assertions, total_voters):
    assert len(alpha_assertions) == len(batchcomp_assertions)
    assertion_data = dict()  # Contains lists of required ballots using ALPHA / batchcomp and the assertion's margin

    # Create dictionary of assertions that holds the # of audited ballots for each method
    for i, assertion in enumerate(alpha_assertions):
        if assertion.type == 1 or assertion.type == 2:
            name = (assertion.party, '-')
        else:
            name = (assertion.party_from, assertion.party_to)
        assertion_data[name] = [0]*4
        assertion_data[name][ASSERTION_TYPE_IND] = assertion.type
        assertion_data[name][ALPHA_REQ_BALLOTS_IND] = assertion.ballots_examined
        assertion_data[name][MARGIN_IND] = assertion.vote_margin

    for assertion in batchcomp_assertions:
        if assertion.type == 1 or assertion.type == 2:
            name = (assertion.party, '-')
        else:
            name = (assertion.party_from, assertion.party_to)
        assertion_data[name][BATCHCOMP_REQ_BALLOTS_IND] = assertion.ballots_examined

    assertion_data_mat = np.array(list(assertion_data.values()))
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
    #axs[0].set_xscale('log')
    axs[0].legend()
    fig.suptitle(ELECTION_NAME + ' - Required # of Ballots vs. Assorter Margin')
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
    plt.title(ELECTION_NAME + ' - Required # of Ballots Per Assertion: Difference betewen ALPHA and Batchcomp')
    plt.xlabel("Assertion Margin")
    plt.ylabel("Required Ballots")
    plt.show()

