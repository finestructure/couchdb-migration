import unittest
import couchdb
import random

URL='http://localhost:5984'
DBNAME = 'migration'


def make_player(name, version):
  player = {
    'type':'player',
    'version':version,
    'name:':name,
    'xp':int(1000*random.random())
  }
  if version == 1:
    return player
  elif version == 2:
    player['level'] = player['xp']/100 + 1
  elif version == 3:
    player['level'] = player['xp']/200 + 1
  return player


def migrate_v1_v2(db):
  v1 = db.view('_design/migration/_view/v1')
  for row in v1.rows:
    doc = db[row.key]
    if doc['version'] == 1:
      doc['version'] = 2
      # we want to add the level stat, which is simply xp/100, starting from 1
      doc['level'] = doc['xp']/100 + 1
      db[doc.id] = doc


def migrate_v2_v3(db):
  v2 = db.view('_design/migration/_view/v2')
  for row in v2.rows:
    doc = db[row.key]
    if doc['version'] == 2:
      doc['version'] = 3
      # ok, we found folks are leveling too fast, so we recompute all levels
      # from existing xp values, players are going to love this!
      doc['level'] = doc['xp']/200 + 1
      db[doc.id] = doc


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


  def test_02_migrate_v1_v2(self):
    migrate_v1_v2(self.db)
    v1 = self.db.view('_design/migration/_view/v1')
    self.assertEqual(0, len(v1.rows))

    v2 = self.db.view('_design/migration/_view/v2')
    self.assertEqual(9, len(v2.rows))
    for row in v2.rows:
      doc = self.db[row.key]
      self.assertEqual(doc['xp']/100 + 1, doc['level'])
    
    v3 = self.db.view('_design/migration/_view/v3')
    self.assertEqual(6, len(v3.rows))
    for row in v3.rows:
      doc = self.db[row.key]
      self.assertEqual(doc['xp']/200 + 1, doc['level'])


  def test_03_migrate_v2_v3(self):
    migrate_v2_v3(self.db)
    v1 = self.db.view('_design/migration/_view/v1')
    self.assertEqual(4, len(v1.rows))
    v2 = self.db.view('_design/migration/_view/v2')
    self.assertEqual(0, len(v2.rows))
    v3 = self.db.view('_design/migration/_view/v3')
    self.assertEqual(11, len(v3.rows))


  def test_03_migrate_v1_v3(self):
    migrate_v1_v2(self.db)
    migrate_v2_v3(self.db)
    v1 = self.db.view('_design/migration/_view/v1')
    self.assertEqual(0, len(v1.rows))
    v2 = self.db.view('_design/migration/_view/v2')
    self.assertEqual(0, len(v2.rows))
    v3 = self.db.view('_design/migration/_view/v3')
    self.assertEqual(15, len(v3.rows))


if __name__=='__main__':
  unittest.main()
