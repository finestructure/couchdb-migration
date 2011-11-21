import unittest
import couchdb

URL='http://localhost:5984'
DBNAME = 'migration'


def make_player(name, version):
  return {
    'type':'player',
    'version':version,
    'name:':name,
  }


class TestMigration(unittest.TestCase):

  def setUp(self):
    self.server = couchdb.Server(URL)
    self.server.delete(DBNAME)
    self.server.create(DBNAME)
    self.db = self.server[DBNAME]
    
    for i in range(1,5):
      self.db.save(make_player('Player %d', version=1))
  
  def tearDown(self):
    pass
    # self.server.delete(DBNAME)
  

  def test_01(self):
    self.assert_(self.db)



if __name__=='__main__':
  unittest.main()
