#!/bin/sh
solr zk cp /opt/solr-9.1.1/server/solr/security.json zk:security.json -z zoo1:2182
./server/scripts/cloud-scripts/zkcli.sh -zkhost zoo1-test:2182 -cmd upconfig -confdir /opt/solr-9.1.1/server/solr/configsets/basic_configs/conf/ -confname solrconfig.xml
bin/solr start -m 4g -z zoo1-test:2182 -f
tail -F /dev/null
