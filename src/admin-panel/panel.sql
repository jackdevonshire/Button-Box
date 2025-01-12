BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS "configuration" (
	"id"	INTEGER NOT NULL UNIQUE,
	"name"	TEXT NOT NULL,
	"description"	TEXT NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "configuration_button" (
	"id"	INTEGER NOT NULL UNIQUE,
	"configuration_id"	INTEGER NOT NULL,
	"physical_key"	TEXT NOT NULL,
	"event_type"	INTEGER NOT NULL,
	"integration_action_id"	INTEGER NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("configuration_id") REFERENCES "configuration"("id"),
	FOREIGN KEY("integration_action_id") REFERENCES "integration_action"("id")
);
CREATE TABLE IF NOT EXISTS "integration" (
	"id"	INTEGER NOT NULL UNIQUE,
	"name"	TEXT NOT NULL,
	"description"	TEXT NOT NULL,
	"is_active"	INTEGER NOT NULL,
	"configuration"	BLOB,
	PRIMARY KEY("id" AUTOINCREMENT)
);
CREATE TABLE IF NOT EXISTS "integration_action" (
	"id"	INTEGER NOT NULL UNIQUE,
	"integration_id"	INTEGER NOT NULL,
	"name"	TEXT NOT NULL,
	"description"	TEXT,
	"configuration"	BLOB NOT NULL,
	PRIMARY KEY("id" AUTOINCREMENT),
	FOREIGN KEY("integration_id") REFERENCES "integration"("id")
);
COMMIT;
