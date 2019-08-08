# Load data into MongoDB

import pymongo # pip install pymongo
from bson import json_util # Comes with pymongo
import envoy
import os
import sys
import json

data_file = os.path.join(os.getcwd(), 'enron.mbox.json')

# Run a command just as you would in a terminal on the virtual machine to
# import the data file into MongoDB.
r = envoy.run('mongoimport --db enron --collection mbox ' + \
              '--file %s' % data_file)

# Print its standard output
print(r.std_out)
print(sys.stderr.write(r.std_err))


# Connects to the MongoDB server running on localhost:27017

client = pymongo.MongoClient()

# Get a reference to the enron database

db = client.enron

# Reference the mbox collection in the Enron database

mbox = db.mbox

# The number of messages in the collection

print("Number of messages in mbox:")
print(mbox.count())

# Pick a message to look at...

msg = mbox.find_one()

# Display the message as pretty-printed JSON. The use of
# the custom serializer supplied by PyMongo is necessary in order
# to handle the date field that is provided as a datetime.datetime
# tuple.

print("A message:")
print(json.dumps(msg, indent=1, default=json_util.default))