import os
from dotenv import load_dotenv
import fixtup
import pytest
from db.solr import Solr

@pytest.fixture(scope='session', autouse=True)
def load_env():
    load_dotenv()


def test_solr_connection():
  with fixtup.up('solr'):
    solr_obj = Solr(user_name=os.getenv("USER_NAME"),password=os.getenv("PASSWORD"), solr_host=os.getenv("SOLR_HOST_TEST"), solr_port=os.getenv("SOLR_PORT_TEST"))
    
    assert solr_obj.ping() == True
    