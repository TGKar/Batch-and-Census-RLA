from ElectionAuditor import ElectionAuditor
from ElectionAssertion import Assorter
import matplotlib.pyplot as plt
from matplotlib import rc
from matplotlib.ticker import MaxNLocator
import numpy as np
import time


ASSERTION_LABELS = ['Above Threshold', 'Below Threshold', 'Move Seat Between Parties']
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

    bc_req_ballots = dict()  # Helps calculate the variance of batchcomp per assertion
    for batchcomp_assertions in batchcomp_assertions_list:
        for assertion in batchcomp_assertions:
            if assertion.type == 1 or assertion.type == 2:
                name = (assertion.party, '-')
            else:
                name = (assertion.party_from, assertion.party_to)
            if name not in bc_req_ballots:
                bc_req_ballots[name] = []
            assertion_data[name][BATCHCOMP_REQ_BALLOTS_IND] += assertion.ballots_counter
            bc_req_ballots[name].append(assertion.ballots_counter)

    assertion_data_mat = np.array(list(assertion_data.values()))
    assertion_data_mat[:, [ALPHA_REQ_BALLOTS_IND, BATCHCOMP_REQ_BALLOTS_IND]] /= len(alpha_assertions_list)  # Average over all repetitions
    max_margin = max(assertion_data_mat[:, MARGIN_IND])

    # Calculate per assertion req ballots variance
    assertions_var = np.std(list(bc_req_ballots.values()), axis=-1)
    print("Mean SD: ", np.mean(assertions_var), " with max SD: ", np.max(assertions_var))

    # Print last three assertions
    top_assertions = assertion_data_mat[np.argsort(assertion_data_mat[:, BATCHCOMP_REQ_BALLOTS_IND])[-TOP_ASSERTION_NUM:], :]
    for i in range(top_assertions.shape[0]):
        print("Assertion margin:", top_assertions[i, MARGIN_IND],": Required ballots batchcomp: ",
              str('{:,}'.format(top_assertions[i, BATCHCOMP_REQ_BALLOTS_IND])), ". Required ballots ALPHA: ",
              str('{:,}'.format(top_assertions[i, ALPHA_REQ_BALLOTS_IND])))

    # Plot comparison
    fig_alpha, ax_alpha = plt.subplots()
    fig_bc, ax_bc = plt.subplots()
    fig_diff, ax_diff = plt.subplots()
    fig_alpha.subplots_adjust(left=0.07, bottom=0.11, top=0.88, right=0.98, hspace=0.28)
    fig_bc.subplots_adjust(left=0.07, bottom=0.11, top=0.88, right=0.98, hspace=0.28)
    fig_diff.subplots_adjust(left=0.07, bottom=0.11, top=0.88, right=0.98, hspace=0.28)

    for i, lab in enumerate(ASSERTION_LABELS):
        slicer = np.where(assertion_data_mat[:, ASSERTION_TYPE_IND] == i + 1)
        ax_alpha.scatter(assertion_data_mat[slicer, MARGIN_IND], assertion_data_mat[slicer, ALPHA_REQ_BALLOTS_IND], label=lab)
        ax_bc.scatter(assertion_data_mat[slicer, MARGIN_IND], assertion_data_mat[slicer, BATCHCOMP_REQ_BALLOTS_IND], label=lab)
    ax_alpha.plot([0, max_margin], [total_voters, total_voters], '--', label='Total Voters')
    ax_bc.plot([0, max_margin], [total_voters, total_voters], '--', label='Total Voters')
    #axs[0].set_xlim((0, max_margin + total_voters / 10**5))

    ax_bc.set_xscale('log')
    ax_alpha.set_xscale('log')
    ax_diff.set_xscale('log')

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    voters_batches_txt = str('{:,}'.format(total_voters)) + " Voters, " + str('{:,}'.format(total_batches)) + str(" Batches")
    #ax_alpha.text(0.7, 0.85, voters_batches_txt, transform=ax_alpha.transAxes, fontsize=15, verticalalignment='top', bbox=props)
    ax_alpha.annotate(voters_batches_txt, xy=(0.75, 0.85), xycoords='axes fraction', fontsize=18)
    ax_bc.annotate(voters_batches_txt, xy=(0.75, 0.85), xycoords='axes fraction', fontsize=18)
    ax_diff.annotate(voters_batches_txt, xy=(0.75, 0.85), xycoords='axes fraction', fontsize=18)

    #ax_bc.text(0.7, 0.85, voters_batches_txt, transform=ax_alpha.transAxes, fontsize=15, verticalalignment='top', bbox=props)
    #ax_diff.text(0.7, 0.85, voters_batches_txt, transform=ax_alpha.transAxes, fontsize=15, verticalalignment='top', bbox=props)

    ax_alpha.set_title("Knesset " + str(knesset_num) + ' - ALPHA-Batch Required Number of Ballots by Assorter Margin')
    ax_bc.set_title("Knesset " + str(knesset_num) + ' - Batchcomp Required Number of Ballots by Assorter Margin')
    ax_diff.set_title("Knesset " + str(knesset_num) + ' - Difference in Required Ballots (ALPHA Batch - Batchcomp)')

    # Plot Difference
    diff = assertion_data_mat[:, ALPHA_REQ_BALLOTS_IND] - assertion_data_mat[:, BATCHCOMP_REQ_BALLOTS_IND]
    for i, lab in enumerate(ASSERTION_LABELS):
        slicer = np.where(assertion_data_mat[:, ASSERTION_TYPE_IND] == i + 1)
        ax_diff.scatter(assertion_data_mat[slicer, MARGIN_IND], diff[slicer], label=lab)
    ax_diff.plot([0, max_margin], [0, 0], '--', label='0')


    ax_alpha.set_xlabel("Assertion Margin (Log Scale)")
    ax_alpha.set_ylabel("Required Ballots")
    ax_bc.set_xlabel("Assertion Margin (Log Scale)")
    ax_bc.set_ylabel("Required Ballots")
    ax_diff.set_xlabel("Assertion Margin (Log Scale)")
    ax_diff.set_ylabel("Required Ballots")
    ax_alpha.legend(loc='right', prop={'size': 18})
    ax_bc.legend(loc='right', prop={'size': 18})
    ax_diff.legend(loc='right', prop={'size': 18})

    timestamp = time.strftime('%b-%d-%Y_%H%M', time.localtime())
    #fig_alpha.savefig(str(timestamp) + ' plot alpha.png', bbox_inches='tight')
    #fig_bc.savefig(str(timestamp) + ' plot bc.png', bbox_inches='tight')
    #fig_diff.savefig(str(timestamp) + ' plot alpha-bc diff.png', bbox_inches='tight')
    fig_alpha.show()
    fig_bc.show()
    fig_diff.show()
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
    fig_errors, ax_errors = plt.subplots()
    fig_accurate, ax_accurate = plt.subplots()
    fig_diff, ax_diff = plt.subplots()


    fig_errors.subplots_adjust(left=0.07, bottom=0.11, top=0.88, right=0.98, hspace=0.28)
    fig_accurate.subplots_adjust(left=0.07, bottom=0.11, top=0.88, right=0.98, hspace=0.28)
    fig_diff.subplots_adjust(left=0.1, bottom=0.11, top=0.88, right=0.98, hspace=0.28)

    for i, lab in enumerate(ASSERTION_LABELS):
        slicer = np.where(assertion_data_mat[:, ASSERTION_TYPE_IND] == i + 1)
        ax_accurate.scatter(assertion_data_mat[slicer, MARGIN_IND], assertion_data_mat[slicer, ALPHA_REQ_BALLOTS_IND], label=lab)
        ax_errors.scatter(assertion_data_mat[slicer, MARGIN_IND], assertion_data_mat[slicer, BATCHCOMP_REQ_BALLOTS_IND], label=lab)
    ax_accurate.plot([0, max_margin], [total_voters, total_voters], '--', label='Total Voters')
    ax_errors.plot([0, max_margin], [total_voters, total_voters], '--', label='Total Voters')



    # Plot Difference
    diff = assertion_data_mat[:, BATCHCOMP_REQ_BALLOTS_IND] - assertion_data_mat[:, ALPHA_REQ_BALLOTS_IND]
    for i, lab in enumerate(ASSERTION_LABELS):
        slicer = np.where(assertion_data_mat[:, ASSERTION_TYPE_IND] == i + 1)
        ax_diff.scatter(assertion_data_mat[slicer, MARGIN_IND], diff[slicer], label=lab)
    ax_diff.plot([0, max_margin], [0, 0], '--', label='0')

    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    voters_batches_txt = str('{:,}'.format(total_voters)) + " Voters, " + str('{:,}'.format(total_batches)) + str(
        " Batches")

    ax_errors.annotate(voters_batches_txt, xy=(0.75, 0.85), xycoords='axes fraction', fontsize=18)
    ax_accurate.annotate(voters_batches_txt, xy=(0.75, 0.85), xycoords='axes fraction', fontsize=18)
    ax_diff.annotate(voters_batches_txt, xy=(0.75, 0.55), xycoords='axes fraction', fontsize=18)

    #ax_errors.text(0.78, 0.85, voters_batches_txt, transform=ax_errors.transAxes, fontsize=15, verticalalignment='top', bbox=props)
    #ax_accurate.text(0.78, 0.85, voters_batches_txt, transform=ax_accurate.transAxes, fontsize=15, verticalalignment='top', bbox=props)
    #ax_diff.text(0.78, 0.85, voters_batches_txt, transform=ax_errors.transAxes, fontsize=15, verticalalignment='top', bbox=props)
    ax_errors.set_title("Knesset " + str(knesset_num) + ' - Batchcomp Required Number of Ballots by Assorter Margin With Counting Errors')
    ax_accurate.set_title("Knesset " + str(knesset_num) + " - Batchcomp Required Number of Ballots by Assorter Margin Without Counting Errors")
    ax_diff.set_title("Knesset " + str(knesset_num) + " Difference in Ballots Required (With Errors - Without Errors)")
    ax_errors.set_xlabel("Assertion Margin (Log Scale)")
    ax_accurate.set_xlabel("Assertion Margin (Log Scale)")
    ax_diff.set_xlabel("Assertion Margin (Log Scale)")
    ax_errors.set_ylabel("Required Ballots")
    ax_accurate.set_ylabel("Required Ballots")
    ax_diff.set_ylabel("Required Ballots")
    ax_accurate.set_xscale('log')
    ax_errors.set_xscale('log')
    ax_diff.set_xscale('log')
    ax_accurate.legend(loc='right', prop={'size': 18})
    ax_errors.legend(loc='right', prop={'size': 18})
    ax_diff.legend(loc='upper right', prop={'size': 18})

    timestamp = time.strftime('%b-%d-%Y_%H%M', time.localtime())
    #fig_accurate.savefig(str(timestamp) + ' plot accurate.png', bbox_inches='tight')
    #fig_errors.savefig(str(timestamp) + ' plot errors.png', bbox_inches='tight')
    #fig_diff.savefig(str(timestamp) + ' plot diff.png', bbox_inches='tight')

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
    plt.legend(loc='lower left', prop={'size': 12})
    plt.title('Share of Batches Audited per Assertion')
    plt.xlabel("Prediction")
    plt.ylabel("Actual")
    plt.show()


def census_plot(alpha_lists, allowed_seat_disc, max_x=1.0, title=None):
    set_font()
    rounded_max_x = int(max_x * len(alpha_lists[0])) / len(alpha_lists[0])
    alpha = np.mean(alpha_lists, axis=0)[:int(rounded_max_x * len(alpha_lists[0]))]
    #print(np.where(alpha <= 0.1)[0][0] / len(alpha), '% of households required for risk limit 0.1.')
    #print(np.where(alpha <= 0.05)[0][0] / len(alpha), '% of households required for risk limit 0.05.')
    fig, ax = plt.subplots()
    ax.plot(rounded_max_x * np.arange(1, len(alpha) + 1) / (len(alpha) + 1), alpha)
    fig.subplots_adjust(left=0.05, bottom=0.08, top=0.93, right=0.97)
    ax.set_xticks(np.linspace(0, rounded_max_x, 11))
    ax.set_yticks(np.linspace(0, 1, 11))
    ax.set_xlabel('Share of Households Examined')
    ax.set_ylabel('Outputted Risk-Limit')
    ax.set_xlim(0, 1.05*max_x)
    ax.set_ylim(0, 1.05)
    ax.xaxis.set_major_locator(MaxNLocator(prune='lower'))

    if title is None:
        plot_title = 'Risk-Limit by Share of Households Examined During the PES'
        if allowed_seat_disc > 0:
            plot_title += '- Up to ' + str(allowed_seat_disc) + ' Seat Discrepancy'
    else:
        plot_title = title
    ax.set_title(plot_title)
    ax.grid()
    plt.show()

def set_font():
    rc('font', **{'family': 'serif', 'serif': ['Computer Modern'], 'size': 18})
    rc('text', usetex=True)