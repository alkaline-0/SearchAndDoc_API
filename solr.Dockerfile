FROM solr:9.1.1

COPY ./db/config/security.json /opt/solr-9.1.1/server/solr/
COPY ./db/config/solr-config.sh /opt/solr-9.1.1/server/solr/
COPY ./db/config/solrconfig.xml /opt/solr-9.1.1/server/solr/configsets/basic_configs/conf/
COPY ./schema/db/managed-schema.xml /opt/solr-9.1.1/server/solr/configsets/basic_configs/conf/

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["sh", "/opt/solr-9.1.1/server/solr/solr-config.sh"]
