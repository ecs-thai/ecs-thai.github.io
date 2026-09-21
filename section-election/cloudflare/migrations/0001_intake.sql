CREATE TABLE settings (id INTEGER PRIMARY KEY CHECK(id=1), nominations_open INTEGER NOT NULL DEFAULT 0, profiles_open INTEGER NOT NULL DEFAULT 1);
INSERT INTO settings(id) VALUES(1);
CREATE TABLE nominations (id TEXT PRIMARY KEY, email TEXT NOT NULL, office TEXT NOT NULL, data TEXT NOT NULL, created INTEGER NOT NULL, UNIQUE(email,office));
CREATE TABLE candidates (id TEXT PRIMARY KEY, invite_hash TEXT NOT NULL UNIQUE, expires INTEGER NOT NULL, profile TEXT NOT NULL, office TEXT NOT NULL DEFAULT '', photo_key TEXT, public_photo TEXT, revision INTEGER NOT NULL DEFAULT 0, shortlisted_revision INTEGER, approved_revision INTEGER, consent_at INTEGER);
CREATE TABLE audit (id INTEGER PRIMARY KEY AUTOINCREMENT, candidate_id TEXT, action TEXT NOT NULL, revision INTEGER, created INTEGER NOT NULL);
CREATE TABLE request_limits (key TEXT PRIMARY KEY, window INTEGER NOT NULL, count INTEGER NOT NULL);
