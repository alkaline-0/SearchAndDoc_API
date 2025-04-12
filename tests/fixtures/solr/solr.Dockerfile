FROM solr:8.11.1

COPY ../../../db/security.json /opt/solr-8.11.1/server/solr/
COPY ./solr-config.sh /opt/solr-8.11.1/server/solr/
COPY ../../../db/solrconfig.xml /opt/solr-8.11.1/server/solr/configsets/basic_configs/conf/
COPY ../../../schemas/managed-schema.xml /opt/solr-8.11.1/server/solr/configsets/basic_configs/conf/

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["sh", "/opt/solr-8.11.1/server/solr/solr-config.sh"]
