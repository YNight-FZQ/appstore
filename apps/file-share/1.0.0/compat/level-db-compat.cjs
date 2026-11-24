const { mkdir } = require('node:fs/promises');
const { Level } = require('level');
const LevelDbAdapter = require('./LevelDbAdapter');

// File Share 1.0.13 ships Level 8, while its initializer uses the older Level API.
LevelDbAdapter.prototype.init = async function init() {
  await mkdir(this.dbPath, { recursive: true });
  this.db = new Level(this.dbPath, { valueEncoding: 'json' });
  await this.db.open();

  for await (const [key, value] of this.db.iterator()) {
    this.cache.set(key, value);
  }
};
