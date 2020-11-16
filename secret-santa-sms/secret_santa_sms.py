'''
Generates a secret santa matching and sends SMS 
notification to all participants

'''
import os
from twilio.rest import Client
import numpy as np
from collections import OrderedDict 

class SecretSantaSMS():
    def __init__(self, participants_numbers):
        super(SecretSantaSMS, self).__init__()

        self.participants_numbers = participants_numbers
        self.n_participants = len(self.participants_numbers)

        # Set the environment variables TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN
        # to the Twilio Account SID and Twilio Auth Token, respectively, prior
        # to running this program
        self.account_sid = os.environ['TWILIO_ACCOUNT_SID']
        self.auth_token = os.environ['TWILIO_AUTH_TOKEN']
        self.client = Client(self.account_sid, self.auth_token)

    def send_message(self, message_text, to_number):
        message = self.client.messages.create(
                body=message_text,
                from_='+18255026064',
                to=to_number
            )
    
    def generate_secret_santa(self):
        # NOTE: A valid secret santa matching is a bijective function without
        # any identity mappings. The bijectivity ensures that no two secret santas
        # are assigned the same person (one-to-one), and that every person has a secret santa (onto).
        # Exclusion of identity mappings ensures that no person is secret santa to themselves.

        # To generate a valid secret santa matching, we take a randomized approach. It is trivial to
        # generate a random bijective function in Python; however, adding the "no identity mappings"
        # condition makes the mapping generation less trivial. Instead of deterministically generating
        # a valid function, we instead generate a bijective function and do postprocessing checks for its validity.

        # Note that there are n! possible bijective functions on n participants, and (n-1)! possible bijective functions
        # without identity mappings. Thus, the probability that a random bijective function is "valid" is (n-1)! / n! = 1/n.
        # In other words, the expected value of function generations required before we have a valid secret santa matching
        # is n; i.e.) we have a linear randomized solution, which is tractable in our case.

        # For easy indexing
        index_participants = {}
        participants_index = {}
        for i, participant in enumerate(self.participants_numbers.keys()):
            index_participants[i] = participant
            participants_index[participant] = i

        # Generate a valid matching
        is_valid = False
        while not is_valid:
            matching = np.random.permutation(self.n_participants)
            
            is_valid = True
            for i in range(self.n_participants):
                if matching[i] == i:
                    is_valid = False
                    break

            # Daniel doesn't want Bryn; Bryn doesn't want Daniel...
            if matching[participants_index['Daniel']] == participants_index['Bryn']:
                is_valid = False
            if matching[participants_index['Bryn']] == participants_index['Daniel']:
                is_valid = False 

        for i, (participant, number) in enumerate(self.participants_numbers.items()):
            message = "\n\nSECRET SANTA MESSAGE: You({}) shop for {}!".format(participant, index_participants[matching[i]])
            self.send_message(message, number)
            print("Message sent to {}.".format(participant))
        print("All messages sent...")

# Run SecretSantaSMS
participants_numbers = OrderedDict()
participants_numbers['A'] = '+1403#######'
participants_numbers['B'] = '+1403#######'
participants_numbers['C'] = '+1403#######'
participants_numbers['D'] = '+1403#######'
participants_numbers['E'] = '+1403#######'
participants_numbers['F'] = '+1403#######'

secret_santa_sms = SecretSantaSMS(participants_numbers)
secret_santa_sms.generate_secret_santa()

