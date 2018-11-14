#!/usr/bin/env bash
#
# Loading enron data into elasticsearch
#
# Prerequisites:
# make sure that stream2es utility is present in the path
# install beautifulsoup4 and lxml:
#    sudo easy_install beautifulsoup4
#    sudo easy_install lxml
#
#
if [ ! -d ./data/enron_mail_20110402 ]; then
    echo "Downloading enron file"
    cd ./data/ && curl -O -L http://www.cs.cmu.edu/~enron/enron_mail_20110402.tgz
    tar -xzf ./data/enron_mail_20110402.tgz
fi
if [ ! -f ./data/enron.mbox.json ]; then
    echo "Converting enron emails to mbox format"
    python3 convert_inbox_to_mbox.py ./data/enron_mail_20110402
    echo "Converting enron emails to json format"
    python3 jsonify_mbox.py ./data/enron.mbox > ./data/enron.mbox.json
    rm enron.mbox
fi
echo "Indexing enron emails"
es_host="http://localhost:9200"
curl -XDELETE "$es_host/enron"
curl -XPUT "$es_host/enron" -d '{
    "settings": {
        "index.number_of_replicas": 0,
        "index.number_of_shards": 5,
        "index.refresh_interval": -1
    },
    "mappings": {
        "email": {
            "properties": {
                "Bcc": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "Cc": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "Content-Transfer-Encoding": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "Content-Type": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "Date": {
                    "type" : "date",
                    "format" : "epoch_millis"
                },
                "From": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "Message-ID": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "Mime-Version": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "Subject": {
                    "type": "string"
                },
                "To": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "X-FileName": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "X-Folder": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "X-From": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "X-Origin": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "X-To": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "X-bcc": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "X-cc": {
                    "type": "string",
                    "index": "not_analyzed"
                },
                "bytes": {
                    "type": "long"
                },
                "offset": {
                    "type": "long"
                },
                "parts": {
                    "dynamic": "true",
                    "properties": {
                        "content": {
                            "type": "string"
                        },
                        "contentType": {
                            "type": "string",
                            "index": "not_analyzed"
                        }
                    }
                }
            }
        }
    }
}'
./stream2es stdin --target $es_host/enron/email < ./data/enron.mbox.json