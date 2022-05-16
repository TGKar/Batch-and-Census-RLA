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
                batch = Batch(i, tally, tally, int(line[INVALID_VOTES_INDEX]), int(line[INVALID_VOTES_INDEX]), apparentments)
                # TODO delete from here

                to_remove_total = 0
                true_tally = tally.copy()
                for party in ['Meretz']:
                    to_remove = int(0*tally[party])
                    true_tally[party] -= to_remove
                    true_tally['Avoda'] += to_remove
                    to_remove_total += to_remove
                batch = Batch(i, tally, true_tally, int(line[INVALID_VOTES_INDEX]), int(line[INVALID_VOTES_INDEX]),
                              apparentments)

                # TODO delete to here
                self.batches.append(batch)
                self.tot_batch += batch

            #print(self.tot_batch)
            self.reported_seats_won, self.reported_paired_seats_won= self.calculate_reported_results()
            #print(self.reported_results)
            #print(sum(self.reported_results.values()))

    def calculate_reported_results(self):
        """
        Calculates the election results based on this profile's batches.
        """
        def split_seats(tally, seat_num):
            """
            Splits a given number of seats based on a given tally. Returns the number of seats each party receives.
            """
            seat_price_table = np.array(list(tally.values()), dtype=np.float).reshape(-1, 1) / \
                               (np.arange(seat_num).reshape(1, -1) + 1)  # [i,j] contains the price party i pays for j seats
            seat_price_rank_table = seat_price_table.ravel().argsort().argsort().reshape(seat_price_table.shape)
            seat_winning_table = seat_price_rank_table >= (seat_price_rank_table.size - seat_num)
            return dict(zip(tally.keys(), list(np.sum(seat_winning_table, axis=-1))))


        thresholded_paired_tally = dict()

        # Calculate which parties passed the threshold
        for key in self.tot_batch.reported_paired_tally:
            if self.tot_batch.reported_paired_tally[key] > self.tot_batch.reported_valid_votes * self.threshold:
                thresholded_paired_tally[key] = self.tot_batch.reported_paired_tally[key]
        paired_seats_won = split_seats(thresholded_paired_tally, self.seats)
        #print(paired_seats_won)
        # Split seats between parties who signed apparentment agreements
        seats_won = dict(zip(self.parties, [0]*len(self.parties)))
        for i, key in enumerate(paired_seats_won):
            if i < len(self.apparentment):
                party1, party2 = self.apparentment[i]
                paired_parties_tally = dict()
                paired_parties_tally[party1] = self.tot_batch.reported_tally[party1]
                paired_parties_tally[party2] = self.tot_batch.reported_tally[party2]
                paired_parties_seats = split_seats(paired_parties_tally, paired_seats_won[party1 + ' + ' + party2])
                seats_won[party1] = paired_parties_seats[party1]
                seats_won[party2] = paired_parties_seats[party2]
            else:
                seats_won[key] = paired_seats_won[key]
        return seats_won, paired_seats_won
