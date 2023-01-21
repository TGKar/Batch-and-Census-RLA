
class Batch:
    def __init__(self, id, reported_tally, true_tally, reported_invalid_votes, true_invalid_votes, apparentments, paired_tally=None):
        """
        :param id: ID of this batch (better use ints)
        :param reported_tally: np array with the reported number of votes for each party
        :param true_tally: np array with the tre number of votes for each party
        :param reported_invalid_votes: reported # of invalid votes in this batch
        :param true_invalid_votes: true # of invalid votes in this batch
        :param apparentments: list of tuples of apparentmen agreements
        """
        self.id = id
        self.true_tally = true_tally
        self.apparentment = apparentments
        if paired_tally is None:
            self.true_paired_tally = self.perform_apparentment(self.true_tally, apparentments)
        else:
            self.true_paired_tally = paired_tally
        self.reported_invalid_votes = reported_invalid_votes
        self.true_invalid_votes = true_invalid_votes
        self.reported_valid_votes = sum(reported_tally.values())
        self.total_votes = self.reported_valid_votes + reported_invalid_votes

        self.reported_tally = reported_tally
        self.reported_paired_tally = self.perform_apparentment(reported_tally, apparentments)


    def __str__(self):
        return "Batch: " + str(self.id) + ", total voters: " + str(self.total_votes) + "\n" + "Tally: " + str(self.true_tally) + \
               "\nPaired tally: " + str(self.true_paired_tally) + "\nInvalid votes: " + str(self.reported_invalid_votes)

    def __add__(self, other):
        """
        Assumes both batches have the same parties in the same order in their tally
        :param other:
        :return:
        """
        add = lambda a,b: a + b
        summed_true_tally = dict(zip(self.true_tally.keys(), list(map(add, self.true_tally.values(), other.true_tally.values()))))
        summed_reported_tally = dict(zip(self.reported_tally.keys(), list(map(add, self.reported_tally.values(), other.reported_tally.values()))))
        return Batch(-1, summed_reported_tally, summed_true_tally, self.reported_invalid_votes + other.reported_invalid_votes,
                     self.true_invalid_votes + other.true_invalid_votes, self.apparentment)

    @staticmethod
    def perform_apparentment(tally, apparentments):
        """
        Unites parties in the given tally based on apparentment agreements.
        """
        result_tally = dict()
        lonely_parties = list(tally.keys())  # Parties who aren't part of an agreement
        for parties in apparentments:
            name = None
            votes = 0
            for party in parties:
                if name is None:
                    name = party
                else:
                    name += ' + ' + party
                lonely_parties.remove(party)
                votes += tally[party]
            result_tally[name] = votes

        for party in lonely_parties:
            result_tally[party] = tally[party]

        return result_tally

    def copy(self):
        return Batch(self.id, self.reported_tally, self.true_tally, self.reported_invalid_votes, self.true_invalid_votes,
                    self.apparentment)
