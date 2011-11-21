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
    
    versions = [1,2,3]
    
    player_count = 0
    for version in versions:
      for i in range(1, version+4):
        player_count += 1
        self.db.save(make_player('Player %d' % player_count, version=version))
  
    design_name = '_design/migration'
    views = {}
    for version in versions:
      view_name = 'v%d' % version
      views[view_name] = {
        'map' : """
          function(doc) {
            if (doc.version && doc.version == %d) {
              emit(doc._id);
            }
          }
        """ % version
      }
    self.db[design_name] = {
      'views' : views
    }


  def tearDown(self):
    pass
    # self.server.delete(DBNAME)
  

  def test_01_views(self):
    self.assert_(self.db)
    v1 = self.db.view('_design/migration/_view/v1')
    self.assertEqual(4, len(v1.rows))
    v2 = self.db.view('_design/migration/_view/v2')
    self.assertEqual(5, len(v2.rows))
    v3 = self.db.view('_design/migration/_view/v3')
    self.assertEqual(6, len(v3.rows))



if __name__=='__main__':
  unittest.main()
