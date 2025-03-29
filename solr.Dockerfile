FROM solr:8.11.1

COPY ./db/security.json /opt/solr-8.11.1/server/solr/

ENTRYPOINT ["docker-entrypoint.sh"]
 