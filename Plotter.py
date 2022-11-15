from Auditor import Auditor
from Assorter import Assorter
import matplotlib.pyplot as plt
import numpy as np


ELECTION_NAME = "Knesset 25"
ASSERTION_LABELS = ['Passed Threshold', 'Failed Threshold', 'Move Seat Between Parties']

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
    assertion_type = np.zeros(len(alpha_assertions))
    assertion_parties = [('', '')]*len(alpha_assertions)  # Either a single party (for failed / threshold) or a tuple of parties (for move-seat)
    assertion_margin = np.zeros(len(alpha_assertions))
    required_ballots = np.zeros((len(alpha_assertions), 2))

    for i, assertion in enumerate(alpha_assertions):
        assertion_type[i] = assertion.type
        assertion_margin[i] = assertion.vote_margin
        required_ballots[i, 0] = assertion.ballots_examined
        if assertion.type == 1 or assertion.type == 2:  # threshold / failed threshold assertion
            assertion_parties[i] = (assertion.party, '-')
        elif assertion.type == 3:  # move seat
            assertion_parties[i] = (assertion.party_from, assertion.party_to)

    for assertion in batchcomp_assertions:
        name = ('-', '-')
        if assertion.type == 1 or assertion.type == 2:
            name = (assertion.party, '-')
        elif assertion.type == 3:
            name = (assertion.party_from, assertion.party_to)
        assertion_index = assertion_parties.index(name)
        required_ballots[assertion_parties.index(name), 1] = assertion.ballots_examined

    max_margin = max(assertion_margin)

    # Plot comparison
    for i, lab in enumerate(ASSERTION_LABELS):
        slicer = np.where(assertion_type == i + 1)
        plt.scatter(assertion_margin[slicer], required_ballots[slicer, 0], label=lab + ' - ALPHA')
        plt.scatter(assertion_margin[slicer], required_ballots[slicer, 1], label=lab + ' - Batchcomp')
        for slice in slicer:
            plt.plot([assertion_margin[slice], assertion_margin[slice]], [required_ballots[slice, 0], required_ballots[slice, 1]], '--', color='grey')
    plt.plot([0, max_margin], [total_voters, total_voters], '--', label='Total Voters')
    plt.xlim((-10000, max_margin + 10000))
    plt.legend()
    plt.title(ELECTION_NAME + ' - Required # of Ballots vs. Assorter Margin')
    plt.xlabel("Assertion Margin")
    plt.ylabel("Required Ballots")
    plt.show()

    # Plot Difference

    diff = required_ballots[:, 0] - required_ballots[:, 1]
    for i, lab in enumerate(ASSERTION_LABELS):
        slicer = np.where(assertion_type == i + 1)
        plt.scatter(assertion_margin[slicer], diff[slicer], label=lab)
        plt.plot([0, max_margin], [0, 0], '--')
        plt.xlim((-10000, max_margin + 10000))
        plt.legend()
        plt.title(ELECTION_NAME + ' - Required # of Ballots Improvement via Batchcomp')
        plt.xlabel("Assertion Margin")
        plt.ylabel("Required Ballots")
        plt.show()


