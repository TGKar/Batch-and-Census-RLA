from ElectionAuditor import Auditor
from ElectionAssorter import Assorter
import matplotlib.pyplot as plt
from matplotlib import rc
import numpy as np
import time, os, fnmatch, shutil


ASSERTION_LABELS = ['Passed Threshold', 'Failed Threshold', 'Move Seat Between Parties']
TOP_ASSERTION_NUM = 3

# Assertion dictionary indexes
ASSERTION_TYPE_IND = 0
ALPHA_REQ_BALLOTS_IND = 1
BATCHCOMP_PREDICTION_IND = 1
BATCHCOMP_REQ_BALLOTS_IND = 2
BATCHCOMP_REQ_BATCHES_IND = 2
MARGIN_IND = 3



def assertions_comparison_plots(alpha_assertions_list, batchcomp_assertions_list, total_voters, total_batches, knesset_num):
    set_font()

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
            assertion_data[name][ALPHA_REQ_BALLOTS_IND] += assertion.ballots_counter

    for batchcomp_assertions in batchcomp_assertions_list:
        for assertion in batchcomp_assertions:
            if assertion.type == 1 or assertion.type == 2:
                name = (assertion.party, '-')
            else:
                name = (assertion.party_from, assertion.party_to)
            assertion_data[name][BATCHCOMP_REQ_BALLOTS_IND] += assertion.ballots_counter

    assertion_data_mat = np.array(list(assertion_data.values()))
    assertion_data_mat[:, [ALPHA_REQ_BALLOTS_IND, BATCHCOMP_REQ_BALLOTS_IND]] /= len(alpha_assertions_list)  # Average over all repetitions
    max_margin = max(assertion_data_mat[:, MARGIN_IND])

    # Print last three assertions
    top_assertions = assertion_data_mat[np.argsort(assertion_data_mat[:, BATCHCOMP_REQ_BALLOTS_IND])[-TOP_ASSERTION_NUM:], :]
    for i in range(top_assertions.shape[0]):
        print("Assertion margin:", top_assertions[i, MARGIN_IND],": Required ballots batchcomp: ",
              str('{:,}'.format(top_assertions[i, BATCHCOMP_REQ_BALLOTS_IND])), ". Required ballots ALPHA: ",
              str('{:,}'.format(top_assertions[i, ALPHA_REQ_BALLOTS_IND])))

    # Plot comparison
    fig, axs = plt.subplots(3, 1, sharex=True, sharey=True)
    for i, lab in enumerate(ASSERTION_LABELS):
        slicer = np.where(assertion_data_mat[:, ASSERTION_TYPE_IND] == i + 1)
        axs[0].scatter(assertion_data_mat[slicer, MARGIN_IND], assertion_data_mat[slicer, ALPHA_REQ_BALLOTS_IND], label=lab)
        axs[1].scatter(assertion_data_mat[slicer, MARGIN_IND], assertion_data_mat[slicer, BATCHCOMP_REQ_BALLOTS_IND], label=lab)
    axs[0].plot([0, max_margin], [total_voters, total_voters], '--', label='Total Voters')
    axs[1].plot([0, max_margin], [total_voters, total_voters], '--', label='Total Voters')
    #axs[0].set_xlim((0, max_margin + total_voters / 10**5))
    axs[0].legend()
    axs[0].set_xscale('log')
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    voters_batches_txt = str('{:,}'.format(total_voters)) + " Voters, " + str('{:,}'.format(total_batches)) + str(" Batches")
    axs[0].text(0.75, 0.85, voters_batches_txt, transform=axs[0].transAxes, fontsize=12, verticalalignment='top', bbox=props)


    fig.suptitle("Knesset " + str(knesset_num) + ' - Required Number of Ballots by Assorter Margin')
    axs[0].set_title("ALPHA-Batch")
    axs[1].set_title("Batchcomp")

    # Plot Difference
    diff = assertion_data_mat[:, ALPHA_REQ_BALLOTS_IND] - assertion_data_mat[:, BATCHCOMP_REQ_BALLOTS_IND]
    for i, lab in enumerate(ASSERTION_LABELS):
        slicer = np.where(assertion_data_mat[:, ASSERTION_TYPE_IND] == i + 1)
        axs[2].scatter(assertion_data_mat[slicer, MARGIN_IND], diff[slicer], label=lab)
        axs[2].plot([0, max_margin], [0, 0], '--')
    axs[2].set_title('Difference (ALPHA - Batchcomp)')

    fig.supxlabel("Assertion Margin (Log Scale)")
    fig.supylabel("Required Ballots")
    timestamp = time.strftime('%b-%d-%Y_%H%M', time.localtime())
    plt.savefig(str(timestamp) + ' plot.png', bbox_inches='tight')
    plt.show()
    save_filename = ".\\Results\\Knesset " + str(knesset_num) + ' data matrix - ' + timestamp
    np.save(save_filename, assertion_data_mat)


def assertions_with_error_plots(assertions_list, noised_assertions_list, total_voters, total_batches, knesset_num):
    set_font()

    assertion_data = dict()  # Contains lists of required ballots using ALPHA / batchcomp and the assertion's margin

    # Create dictionary of assertions that holds the # of audited ballots for each method
    for assertions in assertions_list:
        for i, assertion in enumerate(assertions):
            if assertion.type == 1 or assertion.type == 2:
                name = (assertion.party, '-')
            else:
                name = (assertion.party_from, assertion.party_to)
            if name not in assertion_data:
                assertion_data[name] = [0]*4
                assertion_data[name][ASSERTION_TYPE_IND] = assertion.type
                assertion_data[name][MARGIN_IND] = assertion.vote_margin
            assertion_data[name][ALPHA_REQ_BALLOTS_IND] += assertion.ballots_counter

    for assertions in noised_assertions_list:
        for assertion in assertions:
            if assertion.type == 1 or assertion.type == 2:
                name = (assertion.party, '-')
            else:
                name = (assertion.party_from, assertion.party_to)
            assertion_data[name][BATCHCOMP_REQ_BALLOTS_IND] += assertion.ballots_counter

    assertion_data_mat = np.array(list(assertion_data.values()))
    assertion_data_mat[:, [ALPHA_REQ_BALLOTS_IND, BATCHCOMP_REQ_BALLOTS_IND]] /= len(assertions_list)  # Average over all repetitions
    max_margin = max(assertion_data_mat[:, MARGIN_IND])

    # Plot comparison
    fig, axs = plt.subplots(3, 1, sharex=True)
    for i, lab in enumerate(ASSERTION_LABELS):
        slicer = np.where(assertion_data_mat[:, ASSERTION_TYPE_IND] == i + 1)
        axs[0].scatter(assertion_data_mat[slicer, MARGIN_IND], assertion_data_mat[slicer, ALPHA_REQ_BALLOTS_IND], label=lab)
        axs[1].scatter(assertion_data_mat[slicer, MARGIN_IND], assertion_data_mat[slicer, BATCHCOMP_REQ_BALLOTS_IND], label=lab)
    axs[0].plot([0, max_margin], [total_voters, total_voters], '--', label='Total Voters')
    axs[1].plot([0, max_margin], [total_voters, total_voters], '--', label='Total Voters')
    axs[0].set_xscale('log')
    axs[0].legend()
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    voters_batches_txt = str('{:,}'.format(total_voters)) + " Voters, " + str('{:,}'.format(total_batches)) + str(
        " Batches")
    axs[0].text(0.75, 0.85, voters_batches_txt, transform=axs[0].transAxes, fontsize=12, verticalalignment='top',
                bbox=props)
    fig.suptitle("Knesset " + str(knesset_num) + ' - Batchcomp Required Number of Ballots by Assorter Margin')
    axs[0].set_title("Without Counting Errors")
    axs[1].set_title("With Counting Errors")
    fig.supxlabel("Assertion Margin (Log Scale)")
    fig.supylabel("Required Ballots")

    # Plot Difference
    diff = assertion_data_mat[:, BATCHCOMP_REQ_BALLOTS_IND] - assertion_data_mat[:, ALPHA_REQ_BALLOTS_IND]
    for i, lab in enumerate(ASSERTION_LABELS):
        slicer = np.where(assertion_data_mat[:, ASSERTION_TYPE_IND] == i + 1)
        axs[2].scatter(assertion_data_mat[slicer, MARGIN_IND], diff[slicer], label=lab)
        axs[2].plot([0, max_margin], [0, 0], '--')
    axs[2].set_title('Difference (With Errors - Without Errors)')
    timestamp = time.strftime('%b-%d-%Y_%H%M', time.localtime())
    plt.savefig(str(timestamp) + ' plot.png', bbox_inches='tight')
    plt.show()

def prediction_plots(assertions_lists):
    set_font()

    # Create a dictionary with every assertion's data across all repeats
    assertion_data = dict()
    for election_num, assertions_list in enumerate(assertions_lists):
        for rep, assertions in enumerate(assertions_list):
            for assertion_i, assertion in enumerate(assertions):
                if assertion.type == 1 or assertion.type == 2:
                    name = (election_num, assertion.party, '-')
                else:
                    name = (election_num, assertion.party_from, assertion.party_to)
                if name not in assertion_data:
                    assertion_data[name] = [0] * 4
                    assertion_data[name][ASSERTION_TYPE_IND] = assertion.type
                    assertion_data[name][MARGIN_IND] = assertion.vote_margin
                    assertion_data[name][BATCHCOMP_PREDICTION_IND] = assertion.get_batch_prediction() / assertion.total_batches
                assertion_data[name][BATCHCOMP_REQ_BATCHES_IND] = (assertion_data[name][BATCHCOMP_REQ_BALLOTS_IND] * rep + \
                                                                   (assertion.batch_counter / assertion.total_batches)) / (rep + 1)
    assertion_data_mat = np.array(list(assertion_data.values()))

    # Plot
    for assertion_i, lab in enumerate(ASSERTION_LABELS):
        slicer = np.where(assertion_data_mat[:, ASSERTION_TYPE_IND] == assertion_i + 1)
        plt.scatter(assertion_data_mat[slicer, BATCHCOMP_PREDICTION_IND], assertion_data_mat[slicer, BATCHCOMP_REQ_BALLOTS_IND], label=lab)
    max_x = np.max(assertion_data_mat[:, [BATCHCOMP_PREDICTION_IND, BATCHCOMP_REQ_BATCHES_IND]])
    plt.plot([0, max_x], [0, max_x],'--')
    plt.legend()
    plt.title('Share of Batches Audited per Assertion')
    plt.xlabel("Prediction")
    plt.ylabel("Actual")
    plt.show()


def set_font():
    rc('font', **{'family': 'serif', 'serif': ['Computer Modern']})
    rc('text', usetex=True)