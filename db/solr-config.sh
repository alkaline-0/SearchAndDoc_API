#!/bin/sh
solr zk cp /opt/solr-8.11.1/server/solr/security.json zk:security.json -z zoo1:2181
./server/scripts/cloud-scripts/zkcli.sh -zkhost zoo1:2181 -cmd clusterprop -name legacyCloud -val true
./server/scripts/cloud-scripts/zkcli.sh -zkhost zoo1:2181 -cmd upconfig -confdir /opt/solr-8.11.1/server/solr/configsets/basic_configs/conf/ -confname solrconfig.xml
bin/solr start -z zoo1:2181
tail -F /dev/null
