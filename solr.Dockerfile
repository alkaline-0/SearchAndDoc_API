FROM solr:9.1.1

COPY ./db/security.json /opt/solr-9.1.1/server/solr/
COPY ./db/solr-config.sh /opt/solr-9.1.1/server/solr/
COPY ./db/solrconfig.xml /opt/solr-9.1.1/server/solr/configsets/basic_configs/conf/
COPY ./schemas/managed-schema.xml /opt/solr-9.1.1/server/solr/configsets/basic_configs/conf/

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["sh", "/opt/solr-9.1.1/server/solr/solr-config.sh"]
