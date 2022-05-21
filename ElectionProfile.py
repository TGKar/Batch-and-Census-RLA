import numpy as np
from Batch import Batch
from csv import reader

# XLS constants
INVALID_VOTES_INDEX = 5
PARTY_INDEX = 6
APPARENTMENTS = [("Avoda", "Meretz"), ("Yemina", "Tikva Hadasha"), ("Yesh Atid", "Yisrael Beytenu"), ("Likud", "Tziyonut Detit"), ("Shas", "Yahadut Hatora")]
# I didn't add calcalit and kahol lavan because I didn't add support for apparentments when one of the parties didn't pass the threshold
EPSILON = 0.0000001  # Min difference between eta and mu


class ElectionProfile:

    def __init__(self, xls_file, threshold, seats, apparentments):
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
        self.apparentment = apparentments
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
                    reported_invalid_votes = int(line[INVALID_VOTES_INDEX])
                    true_tally, true_invalid_votes = self.add_noise(tally, reported_invalid_votes)
                    batch = Batch(i, tally, true_tally, reported_invalid_votes, true_invalid_votes,
                                  apparentments)

                    self.batches.append(batch)
                    self.tot_batch += batch

                #print(self.tot_batch)
                self.reported_seats_won, self.reported_paired_seats_won= \
                    self.calculate_reported_results(self.tot_batch.reported_tally, self.tot_batch.reported_paired_tally,
                                                    self.tot_batch.reported_invalid_votes)
                self.true_seats_won, true_paired_seats_won = self.calculate_reported_results(self.tot_batch.true_tally, self.tot_batch.true_paired_tally,
                                                    self.tot_batch.true_invalid_votes)  # TODO remove self.
                reported_matches_truth = np.all(np.fromiter(self.reported_seats_won.values(), dtype=int) ==
                                                 np.fromiter(self.true_seats_won.values(), dtype=int))
                reported_matches_truth = True  # TODO delete
                print("Drew noised elections")
            #print(self.reported_results)
            #print(sum(self.reported_results.values()))

    def calculate_reported_results(self, tally, paired_tally, invalid):
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
        vote_threshold = (np.sum(list(tally.values())) - invalid) * self.threshold

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
            if i < len(self.apparentment):
                party1, party2 = self.apparentment[i]
                paired_parties_tally = dict()
                paired_parties_tally[party1] = tally[party1]
                paired_parties_tally[party2] = tally[party2]
                paired_parties_seats = split_seats(paired_parties_tally, paired_seats_won[party1 + ' + ' + party2])
                seats_won[party1] = paired_parties_seats[party1]
                seats_won[party2] = paired_parties_seats[party2]
            else:
                seats_won[key] = paired_seats_won[key]
        return seats_won, paired_seats_won

    def add_noise(self, tally, invalid_votes, error_ratio=0.75, invalidation_rate=0.5, invalid_to_valid_ratio=1.0):
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
        choice_probs = np.array(list(noised_tally.values())) / valid_voters
        invalid_to_valid_to = np.random.choice(self.parties, size=invalid_to_valid_num, p=choice_probs)
        errors = np.random.poisson(error_ratio * valid_voters)
        errors_from = np.random.choice(self.parties, size=errors, p=choice_probs)
        errors_to = np.random.choice(self.parties, size=errors, p=choice_probs)
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

