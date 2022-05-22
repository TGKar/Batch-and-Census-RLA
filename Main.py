from ElectionProfile import ElectionProfile
from ThresholdAssertion import ThresholdAssertion
from Auditor import Auditor
import numpy as np
import matplotlib.pyplot as plt


# Constants
APPARENTMENTS = [("Avoda", "Meretz"), ("Yemina", "Tikva Hadasha"), ("Yesh Atid", "Yisrael Beytenu"), ("Likud", "Tziyonut Detit"), ("Shas", "Yahadut Hatora")]
THRESHOLD = 0.0325
SEATS = 120
ALPHA = 0.05

if __name__ == "__main__":
    party = "Raam"
    party_to = "Kahol Lavan"
    party_from = "Likud + Tziyonut Detit"
    profile = ElectionProfile("Results.csv", THRESHOLD, SEATS, APPARENTMENTS)
    auditor = Auditor(profile, ALPHA, THRESHOLD)
    """
    for batch in profile.batches:
        for assertion in (auditor.comparison_assertions + auditor.past_threshold_assertions + auditor.failed_threshold_assertions):
            assertion.audit_batch(batch)
    for assertion in (auditor.comparison_assertions + auditor.past_threshold_assertions + auditor.failed_threshold_assertions):
        if profile.tot_batch.total_votes != assertion.eta.total_ballots:
            print("Bad ballot count: " + str(assertion))
        if abs(assertion.reported_assorter_mean - assertion.eta.assorter_sum) > 0.0001:
            print("Bad assorter sum: ", str(assertion), '. Difference ', str(assertion.reported_assorter_mean - assertion.eta.assorter_sum))
    """
    auditor.audit()
    print("Reported Results:")
    print(profile.reported_seats_won)
    print("True Results:")
    print(profile.true_seats_won)
    print("Reported Tally:")
    print(profile.tot_batch.reported_tally)
    print("True Tally:")
    print(profile.tot_batch.true_tally)
    print("True threshold:", profile.threshold * (profile.tot_batch.total_votes-profile.tot_batch.true_invalid_votes),
          'total voters: ', profile.tot_batch.total_votes)

    print("Reported matches truth: ", np.all(np.array(list(profile.reported_seats_won.values())) == np.array(list(profile.true_seats_won.values()))))
    exit(0)

    #reported_assorter_share = profile.tot_batch.tally[party] / profile.tot_batch.valid_votes
    #reported_invalid_share = profile.tot_batch.invalid_votes / profile.tot_batch.total_votes
    #assertion = ThresholdAssertion(ALPHA, party, THRESHOLD, profile)



    done = False
    i = 0

    """
    while not done:
        parties = list(profile.tot_batch.tally.keys()) + [Assorter.INVALID_BALLOT]
        probs = np.array(list(profile.tot_batch.tally.values()) + [profile.tot_batch.invalid_votes]) / profile.tot_batch.total_votes
        ballot = np.random.choice(parties, p=probs)
        done, t = assertion.assert_ballot(ballot)
        i += 1
        print(t)
    print(i)
    exit(0)
    """
    # assertion = ThresholdAssertion(ALPHA, party, THRESHOLD, reported_assorter_share, profile.tot_batch.invalid_votes)
    p = []
    for batch in profile.batches:
        p.append(batch.total_votes / profile.tot_batch.total_votes)
    batch = np.random.choice(profile.batches, p=p)
    i = 0
    REPS = 1
    for j in range(REPS):
        #assertion = ComparisonAssertion(ALPHA, party_from, party_to, profile, True)
        assertion = ThresholdAssertion(ALPHA, party, THRESHOLD, profile)
        done = False
        while not done:
            batch = np.random.choice(profile.batches, p=p)
            done, t = assertion.audit_batch(batch)
            i += 1
            if i % 100 == 0:
                print(str(i), ': T: ', str(t), '  mu: ',  str(assertion.mu),'eta: ', str(assertion.eta.value))
    print("Approved after " + str(i / REPS) + " batches")