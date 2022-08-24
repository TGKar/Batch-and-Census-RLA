import numpy as np


FILENAME_BATCH = "./results/Knesset 22.txt"
FILENAME_BALLOT = "./results/Knesset 22 - ballot rla.txt.txt"

if __name__ == "__main__":
    assertions = []
    required_ballots = []
    with open(FILENAME_BATCH, "r") as results_file:
        lines = results_file.readlines()[3:-18]
        for line in lines:
            parts = line.split(' ')
            assertion = print(parts)
            ballots = parts[-4]


