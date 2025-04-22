FROM solr:9.1.1

COPY ./configs/security.json /opt/solr-9.1.1/server/solr/
COPY ./configs/solr-config.sh /opt/solr-9.1.1/server/solr/
COPY ./configs/solrconfig.xml /opt/solr-9.1.1/server/solr/configsets/basic_configs/conf/
COPY ./configs/managed-schema.xml /opt/solr-9.1.1/server/solr/configsets/basic_configs/conf/

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["sh", "/opt/solr-9.1.1/server/solr/solr-config.sh"]
