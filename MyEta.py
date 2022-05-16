from Eta import Eta

MY_ETA = "MY"

class MyEta(Eta):
    def __init__(self, ultimate_eta, total_ballots):
        super().__init__(None, ultimate_eta)
        self.total_ballots = total_ballots
        self.assorter_sum = 0
        self.ballots_examined = 0


    def calculate_eta(self, samples, assorter_value, mu):
        """
        Updates eta based on an additional number of samples.
        :param samples: Number of samples to update.
        :param assorter_value: The assorter mean over these samples.
        :param mu: null hypothesis regarding the assorter mean
        :return: Eta.
        """
        self.assorter_sum += assorter_value
        self.ballots_examined += samples
        if (self.total_ballots - self.ballots_examined) == 0:
            self.value = 0
        else:
            self.value = (self.total_ballots * self.eta_0 - self.assorter_sum) / (self.total_ballots - self.ballots_examined)
        return self.value
