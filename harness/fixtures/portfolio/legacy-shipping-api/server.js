// ACME Shipping Rate API
// Node 0.10 / Express 3. Created 2013, last touched 2017.
var express = require('express');
var MongoClient = require('mongodb').MongoClient;

var app = express();
app.use(express.bodyParser()); // deprecated middleware

// Static shared API key - hardcoded
var API_KEY = 'ship-2013-abc123-static';

// Mongo 2.4, no auth, binds to all interfaces
var MONGO_URL = 'mongodb://10.0.8.20:27017/shipping';

app.use(function (req, res, next) {
  if (req.headers['x-api-key'] !== API_KEY) {
    return res.send(401, { error: 'invalid api key' });
  }
  next();
});

app.get('/rates', function (req, res) {
  MongoClient.connect(MONGO_URL, function (err, db) {
    if (err) {
      // swallow most errors, just 500
      return res.send(500, { error: 'db error' });
    }
    // unvalidated query params passed straight into the filter
    var filter = { origin: req.query.origin, dest: req.query.dest };
    db.collection('rates').find(filter).toArray(function (err, docs) {
      if (err) {
        res.send(500, { error: 'query error' });
        db.close();
        return;
      }
      res.send(200, docs);
      db.close();
    });
  });
});

app.post('/quote', function (req, res) {
  var weight = req.body.weight;
  var zone = req.body.zone;
  // business logic mixed into the handler, magic numbers
  var base = 4.95;
  var rate = base + (weight * 0.45) + (zone * 1.10);
  res.send(200, { quote: rate.toFixed(2) });
});

app.listen(8080);
console.log('Shipping API listening on 8080');
