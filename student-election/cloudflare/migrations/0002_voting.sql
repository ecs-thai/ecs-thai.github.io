ALTER TABLE settings ADD COLUMN ballot_config TEXT;
CREATE TABLE voters(identity_hash TEXT PRIMARY KEY,token_hash TEXT NOT NULL,receipt TEXT UNIQUE,failures INTEGER NOT NULL DEFAULT 0);
CREATE TABLE ballots(id TEXT PRIMARY KEY,choices TEXT NOT NULL);
-- A transient claim is removed in the same atomic statement. Ballots keep no voter key.
CREATE TABLE claims(identity_hash TEXT PRIMARY KEY,receipt TEXT NOT NULL,choices TEXT NOT NULL,ballot_id TEXT NOT NULL);
CREATE TRIGGER accept_claim AFTER INSERT ON claims BEGIN
 INSERT INTO ballots(id,choices) VALUES(NEW.ballot_id,NEW.choices);
 UPDATE voters SET receipt=NEW.receipt WHERE identity_hash=NEW.identity_hash;
 DELETE FROM claims WHERE identity_hash=NEW.identity_hash;
END;
CREATE TRIGGER freeze_profiles BEFORE UPDATE ON candidates
WHEN (SELECT ballot_config FROM settings WHERE id=1) IS NOT NULL
BEGIN SELECT RAISE(ABORT,'election_frozen'); END;
