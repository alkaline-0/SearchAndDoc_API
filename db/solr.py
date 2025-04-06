import json

import pysolr
import requests


class Solr:
    _pysolr_obj: any
    _admin_url: str
    _user_name: str
    _password: str
    _conn_url: str
    _collection_conn_url: str
    _config_name: str
    _instance_dir: str
    _schema_name: str

    def __init__(
        self, user_name: str, password: str, solr_host: str, solr_port: str
    ) -> None:
        self._user_name = user_name
        self._password = password
        self._construct_url(solr_host=solr_host, solr_port=solr_port)
        self._pysolr_obj = pysolr.Solr(self._conn_url, always_commit=True)
        self._instance_dir = "/opt/solr-8.11.1/server/solr"
        self._config_name = "solrconfig.xml"
        self._schema_name = "managed-schema.xml"

    def create_collection(self, collection_name: str) -> json:
        if self._collection_exist(collection_name):
            return None

        params = {
            "action": "CREATE",
            "name": collection_name,
            "numShards": 1,
            "collection.configName": self._config_name,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        resp = requests.get(
            self._collection_conn_url,
            data=pysolr.safe_urlencode(params),
            headers=headers,
        )
        try:
            resp.raise_for_status()

            return json.loads(pysolr.force_unicode(resp.content))
        except requests.exceptions.HTTPError as e:
            print(f"Error in creating collection: {e}")
            raise
        except Exception as e:
            print(
                f"Unexpected error occured when sending request to Solr database: {e}"
            )
            raise

    def create_new_core(
        self, discord_server_id: str, collection_name: str = "vault"
    ) -> json:
        params = {
            "action": "CREATE",
            "name": discord_server_id,
            "config": self._config_name,
            "instance_dir": self._instance_dir,
            "schema": self._schema_name,
            "collection": collection_name,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        resp = requests.get(
            self._admin_url, data=pysolr.safe_urlencode(params), headers=headers
        )
        try:
            resp.raise_for_status()
            return json.loads(pysolr.force_unicode(resp.content))
        except requests.exceptions.HTTPError as e:
            print(f"Error in creating core: {e}")
            raise
        except Exception as e:
            print(
                f"Unexpected error occured when sending request to Solr database: {e}"
            )
            raise

    def _construct_url(self, solr_host: str, solr_port: str) -> None:
        self._conn_url = (
            f"http://{self._user_name}:{self._password}@{solr_host}:{solr_port}/solr"
        )
        self._admin_url = f"{self._conn_url}/admin/cores"
        self._collection_conn_url = f"{self._conn_url}/admin/collections"

    def _collection_exist(self, collection_name: str) -> bool:
        params = {"action": "LIST"}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        resp = requests.get(
            self._collection_conn_url,
            data=pysolr.safe_urlencode(params),
            headers=headers,
        )
        try:
            resp.raise_for_status()

            json_resp = json.loads(pysolr.force_unicode(resp.content))
            return collection_name in json_resp["collections"]
        except requests.exceptions.HTTPError as e:
            print(
                f"Request to validate collection presence in Solr database failed due to: {e}"
            )
            raise
        except Exception as e:
            print(
                f"Unexpected error occured when sending request to Solr database: {e}"
            )
            raise
