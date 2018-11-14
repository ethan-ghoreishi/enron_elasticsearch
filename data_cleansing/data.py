import sys
import os
import envoy # pip install envoy
from urllib.request import urlopen
import time

URL = "http://www.cs.cmu.edu/~enron/enron_mail_20110402.tgz"
DOWNLOAD_DIR = "."

# Downloads a file and displays a download status every 5 seconds

def download(url, download_dir):
    file_name = url.split('/')[-1]
    u = urlopen(url)
    f = open(os.path.join(download_dir, file_name), 'wb')
    meta = u.info()
    file_size = int(meta.get_all("Content-Length")[0])
    print("Downloading: %s Bytes: %s" % (file_name, file_size))

    file_size_dl = 0
    block_sz = 8192
    last_update = time.time()
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        download_status = r"%10d MB  [%3.2f%%]" % (file_size_dl / 1000000.0, file_size_dl * 100.0 / file_size)
        download_status = download_status + chr(8)*(len(download_status)+1)
        if time.time() - last_update > 5:
            print(download_status,)
            sys.stdout.flush()
            last_update = time.time()
    f.close()
    return f.name

# Extracts a gzipped tarfile. e.g. "$ tar xzf filename.tgz"

def tar_xzf(f):
    # Call out to the shell for a faster decompression.
    # This will still take a while because Vagrant synchronizes
    # thousands of files that are extracted to the host machine
    r = envoy.run("tar xzf %s -C %s" % (f, DOWNLOAD_DIR))
    print(r.std_out)
    print(r.std_err)

f = download(URL, DOWNLOAD_DIR)
print("Download complete: %s" % (f,))
tar_xzf(f)
print("Decompression complete")
print("Data is ready")

######
# Converting the Enron corpus to a standardized mbox format
######

import email
from time import asctime
import re
from dateutil.parser import parse  # pip install python_dateutil

MAILDIR = 'enron_mail_20110402/' + \
          'maildir'

# Where to write the converted mbox

MBOX = 'enron.mbox'

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

#####
# Convert an mbox to a JSON structure suitable to import into MongoDB
#####

import mailbox
import email
import quopri
import json
import time
from bs4 import BeautifulSoup

MBOX = 'enron.mbox'
OUT_FILE = MBOX + '.json'


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


# The generator itself...
def gen_json_msgs(mb):
    while 1:
        msg = mb.next()
        if msg is None:
            break

        yield jsonify_message(msg)


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
# for easy import into MongoDB via mongoimport

f = open(OUT_FILE, 'w')
for msg in mbox:
    if msg != None:
        f.write(json.dumps(jsonify_message(msg), cls=Encoder) + '\n')
f.close()

print("All done")

