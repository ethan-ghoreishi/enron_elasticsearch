# Converting the Enron corpus to a standardized mbox format

import email
from time import asctime
import re
import os
from dateutil.parser import parse  # pip install python_dateutil

MAILDIR = './data/enron_mail_20110402/' + \
          'maildir'

# Where to write the converted mbox

MBOX = './data/enron.mbox'

# Create a file handle that we'll be writing into...

mbox = open(MBOX, 'w')

# Walk the directories and process any folder named 'inbox'

for (root, dirs, file_names) in os.walk(MAILDIR):

    if root.split(os.sep)[-1].lower() != 'inbox':
        continue

    # Process each message in 'inbox'

    for file_name in file_names:
        file_path = os.path.join(root, file_name)
        message_text = open(file_path, encoding='latin-1').read()

        # Compute fields for the From_ line in a traditional mbox message

        _from = re.search(r"From: ([^\n]+)", message_text).groups()[0]
        _date = re.search(r"Date: ([^\n]+)", message_text).groups()[0]

        # Convert _date to the asctime representation for the From_ line


        _date = asctime(parse(_date).timetuple())

        msg = email.message_from_string(message_text)
        msg.set_unixfrom('From %s %s' % (_from, _date))

        mbox.write(msg.as_string(unixfrom=True) + "\n\n")

mbox.close()