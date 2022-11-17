import numpy as np
from Batch import Batch
from csv import reader
from collections import Counter

# XLS constants
INVALID_VOTES_INDEX = 5
PARTY_INDEX = 6
INVALID_BALLOT = 'Invalid'
EPSILON = 10**(-9)  # Min difference between eta and mu


class ElectionProfile:

    def __init__(self, xls_file, threshold, seats, apparentments, shuffle_true_tallies=False, redraw_tallies=False):
        """
        Creates an election profile from a result xls (formatted as in the gov's website)
        :param xls_file: Path to the file which contains the election results.
        :param threshold: Ratio of votes a party has to win to earn any seats (ahuz hasima).
        :param seats: Number of seats to elect
        :param apparentments remainder-sharing agreements between parties, as a list of tuples containing the party
        (Heskem Odafim)
        names.
        """
        self.threshold = threshold
        self.seats = seats
        self.apparentments = apparentments
        reported_matches_truth = False
        while not reported_matches_truth:
            with open(xls_file, "r") as results_file:
                file_reader = reader(results_file)
                header = next(file_reader)
                self.parties = header[PARTY_INDEX:]

                # Load batches
                self.batches = []
                empty_tally = dict(zip(self.parties, [0]*len(self.parties)))
                self.tot_batch = Batch(0, empty_tally, empty_tally, 0, 0, apparentments)
                for i, line in enumerate(file_reader):
                    tally = dict(zip(self.parties, list(map(int, line[PARTY_INDEX:]))))
                    invalid_votes = int(line[INVALID_VOTES_INDEX])
                    if redraw_tallies:
                        true_tally, true_invalid_votes = self.redraw_tally(tally, invalid_votes)
                        rep_tally, rep_invalid_votes = self.redraw_tally(tally, invalid_votes)
                        batch = Batch(i, rep_tally, true_tally, rep_invalid_votes, true_invalid_votes, apparentments)
                    else:
                        true_tally, true_invalid_votes = self.add_noise(tally, invalid_votes)
                        batch = Batch(i, tally, true_tally, invalid_votes, true_invalid_votes, apparentments)
                    self.batches.append(batch)
                    self.tot_batch += batch

                # Load ballots
                self.ballots = []
                for party in self.parties:
                    self.ballots += [party]*self.tot_batch.true_tally[party]
                self.ballots += [INVALID_BALLOT]*self.tot_batch.true_invalid_votes
                np.random.shuffle(self.ballots)

                # Shuffle true tallies
                if shuffle_true_tallies:
                    self.tot_batch = Batch(0, empty_tally, empty_tally, 0, 0, apparentments)
                    perm = np.arange(len(self.batches))
                    np.random.shuffle(perm)
                    batches_copy = [self.batches[i].copy() for i in range(len(self.batches))]
                    for i, j in enumerate(perm):
                        self.batches[i].true_tally = batches_copy[j].true_tally.copy()
                        self.batches[i].true_invalid_votes = batches_copy[j].true_invalid_votes
                        self.batches[i].true_paired_tally = batches_copy[j].true_paired_tally.copy()
                        if self.batches[i].total_votes > self.batches[i].true_invalid_votes + sum(self.batches[i].true_tally.values()):
                            self.batches[i].true_invalid_votes = self.batches[i].total_votes - sum(self.batches[i].true_tally.values())
                        else:
                            self.batches[i].reported_invalid_votes = self.batches[i].true_invalid_votes + \
                                                                     sum(self.batches[i].true_tally.values()) - \
                                                                     sum(self.batches[i].reported_tally.values())
                        assert sum(self.batches[i].true_tally.values()) + self.batches[i].true_invalid_votes == \
                               sum(self.batches[i].reported_tally.values()) + self.batches[i].reported_invalid_votes
                        self.batches[i].total_votes = sum(self.batches[i].reported_tally.values()) + self.batches[i].reported_invalid_votes
                        self.tot_batch += self.batches[i]
                #print(self.tot_batch)
                self.reported_seats_won, self.reported_paired_seats_won = \
                    self.calculate_reported_results(self.tot_batch.reported_tally, self.tot_batch.reported_paired_tally)
                self.true_seats_won, true_paired_seats_won = self.calculate_reported_results(self.tot_batch.true_tally, self.tot_batch.true_paired_tally)  # TODO remove self.
                reported_matches_truth = np.all(np.fromiter(self.reported_seats_won.values(), dtype=int) ==
                                                 np.fromiter(self.true_seats_won.values(), dtype=int))
                print("Elections Tallies Loaded")
                reported_matches_truth = True
            #print(self.reported_results)
            #print(sum(self.reported_results.values()))

    """
    def __init__(self, reported_tally, true_ballots, reported_invalid_votes=0, true_invalid_votes=0):
        self.parties = list(reported_tally.keys())

        # Load batches
        true_tally = Counter(true_ballots)
        batch = Batch(0, reported_tally, true_tally, reported_invalid_votes, true_invalid_votes, ())
        self.batches = [batch]
        self.tot_batch = batch

        # Load ballots
        self.ballots = true_ballots.copy()
        np.random.shuffle(self.ballots)
    """

    def calculate_reported_results(self, tally, paired_tally):
        """
        Calculates the election results based on this profile's batches.
        """
        def split_seats(sub_tally, seat_num):
            """
            Splits a given number of seats based on a given tally. Returns the number of seats each party receives.
            """
            seat_price_table = np.array(list(sub_tally.values()), dtype=np.float).reshape(-1, 1) / \
                               (np.arange(seat_num).reshape(1, -1) + 1)  # [i,j] contains the price party i pays for j seats
            seat_price_rank_table = seat_price_table.ravel().argsort().argsort().reshape(seat_price_table.shape)
            seat_winning_table = seat_price_rank_table >= (seat_price_rank_table.size - seat_num)
            return dict(zip(sub_tally.keys(), list(np.sum(seat_winning_table, axis=-1))))

        thresholded_paired_tally = dict()
        vote_threshold = np.sum(list(tally.values())) * self.threshold

        # Calculate which parties passed the threshold
        for key in paired_tally.keys():
            parties_to_check = key.split(' + ')
            passed_parties = []
            for party in parties_to_check:
                if tally[party] > vote_threshold:
                    passed_parties.append(party)
            if len(passed_parties) == len(parties_to_check):  # All parties in apparentment passed the threshold
                thresholded_paired_tally[key] = paired_tally[key]
            elif len(passed_parties) == 1:
                thresholded_paired_tally[passed_parties[0]] = tally[passed_parties[0]]

        paired_seats_won = split_seats(thresholded_paired_tally, self.seats)

        # Split seats between parties who signed apparentment agreements
        seats_won = dict(zip(self.parties, [0]*len(self.parties)))
        for i, key in enumerate(paired_seats_won):
            if i < len(self.apparentments):
                party1, party2 = self.apparentments[i]
                if party1 + ' + ' + party2 in paired_seats_won.keys():
                    paired_parties_tally = dict()
                    paired_parties_tally[party1] = tally[party1]
                    paired_parties_tally[party2] = tally[party2]
                    paired_parties_seats = split_seats(paired_parties_tally, paired_seats_won[party1 + ' + ' + party2])
                    seats_won[party1] = paired_parties_seats[party1]
                    seats_won[party2] = paired_parties_seats[party2]
                else:
                    seats_won[party1] = paired_seats_won.get(party1, 0)
                    seats_won[party2] = paired_seats_won.get(party2, 0)
            else:
                seats_won[key] = paired_seats_won[key]
        return seats_won, paired_seats_won

    def add_noise(self, tally, invalid_votes, error_ratio=0.0, invalidation_rate=0.0, invalid_to_valid_ratio=0.0):
        """
        Adds error to a tally
        :param tally: Vote tally
        :param invalid_votes: Number of invalid votes
        :param error_ratio: Desired error ratio from valid votes (in expectancy)
        :param invalidation_rate: Rate of invalidation of votes, from total errors
        :param invalid_to_valid_ratio: Rate of validating an invalid vote.
        :return: The noised tally, the noised number of invalid votes
        """
        noised_tally = tally.copy()
        valid_voters = np.sum(list(noised_tally.values()))
        invalid_to_valid_num = min(np.random.poisson(invalid_votes * invalid_to_valid_ratio), invalid_votes)
        noised_invalid = invalid_votes - invalid_to_valid_num
        invalid_to_valid_to = np.random.choice(self.parties, size=invalid_to_valid_num)
        if valid_voters > 0:
            # Add noise from reported tally to other parties / invalidation
            choice_probs = np.array(list(noised_tally.values())) / valid_voters
            errors = np.random.binomial(valid_voters, error_ratio)
            errors_from = np.random.choice(self.parties, size=errors, p=choice_probs)
            errors_to = np.random.choice(self.parties, size=errors)
            for i in range(errors):
                if noised_tally[errors_from[i]] > 0:
                    noised_tally[errors_from[i]] -= 1
                    if np.random.random() < invalidation_rate:
                        noised_invalid += 1
                    else:
                        noised_tally[errors_to[i]] += 1

        for party_to in invalid_to_valid_to:
            noised_tally[party_to] += 1
        assert np.sum(list(tally.values())) + invalid_votes == np.sum(list(noised_tally.values())) + noised_invalid
        return noised_tally, noised_invalid


    def redraw_tally(self, tally, invalid_votes):
        n_ballots = np.sum(list(tally.values())) + invalid_votes
        full_tally = tally.copy()
        full_tally[INVALID_BALLOT] = invalid_votes
        tally_values = np.array(list(full_tally.values()))
        # TODO sample more efficiently
        sampled_ballots = np.random.choice(list(full_tally.keys()), size=n_ballots, p=tally_values / n_ballots)
        new_tally = dict()
        new_tally.update(zip(full_tally.keys(), np.zeros(len(full_tally.values()), dtype=int)))
        if not new_tally.__contains__(INVALID_BALLOT):
            print("bad")
        new_tally.update(dict(Counter(sampled_ballots)))
        new_invalid = new_tally[INVALID_BALLOT]
        del new_tally[INVALID_BALLOT]
        return new_tally, new_invalid
