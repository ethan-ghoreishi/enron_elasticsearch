# Convert an mbox to a JSON structure suitable to import into MongoDB

import mailbox
import quopri
import json
import time
from bs4 import BeautifulSoup
from dateutil.parser import parse  # pip install python_dateutil


MBOX = sys.argv[1]
OUT_FILE = None
try:
    OUT_FILE = sys.argv[2]
except Exception, e:
    pass


def clean_content(msg):
    # Decode message from "quoted printable" format, but first
    # re-encode, since decodestring will try to do a decode of its own
    msg = quopri.decodestring(msg.encode('utf-8'))

    # Strip out HTML tags, if any are present.
    # Bail on unknown encodings if errors happen in BeautifulSoup.
    try:
        soup = BeautifulSoup(msg, "lxml")
    except:
        return ''
    return ''.join(soup.findAll(text=True))


# There's a lot of data to process, and the Pythonic way to do it is with a
# generator. See http://wiki.python.org/moin/Generators.
# Using a generator requires a trivial encoder to be passed to json for object
# serialization.

class Encoder(json.JSONEncoder):
    def default(self, o): return list(o)


def jsonify_message(msg):
    json_msg = {'parts': []}
    for (k, v) in msg.items():
        json_msg[k] = v

    # The To, Cc, and Bcc fields, if present, could have multiple items.
    # Note that not all of these fields are necessarily defined.

    for k in ['To', 'Cc', 'Bcc']:
        if not json_msg.get(k):
            continue
        json_msg[k] = json_msg[k].replace('\n', '').replace('\t', '').replace('\r', '') \
            .replace(' ', '').split(',')

    for part in msg.walk():
        json_part = {}

        if part.get_content_maintype() != 'text':
            print(sys.stderr, "Skipping MIME content in JSONification ({0})".format(part.get_content_maintype()))
            continue

        json_part['contentType'] = part.get_content_type()
        content = part.get_payload(decode=False)
        json_part['content'] = clean_content(content)
        json_msg['parts'].append(json_part)

    # Finally, convert date from asctime to milliseconds since epoch using the
    # $date descriptor so it imports "natively" as an ISODate object in MongoDB
        try:
            then = parse(json_msg['Date'])
            millis = int(time.mktime(then.timetuple()) * 1000 + then.microsecond / 1000)
            json_msg['Date'] = {'$date': millis}
        except KeyError:
            json_msg['Date'] = {'$date': ''}

    return json_msg


mbox = mailbox.mbox(MBOX)

# Write each message out as a JSON object on a separate line

f = open(OUT_FILE, 'w')
for msg in mbox:
    if msg != None:
        f.write(json.dumps(jsonify_message(msg), cls=Encoder) + '\n')
f.close()

print("All done")