CREATE TABLE timers (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	group_id INTEGER DEFAULT 1,
	name TEXT NOT NULL,
	note TEXT DEFAULT NULL,
	start TIMESTAMP DEFAULT NULL,
	end TIMESTAMP DEFAULT NULL,
	sync_date TIMESTAMP DEFAULT NULL,
	FOREIGN KEY(group_id) REFERENCES groups(id)
);

CREATE TABLE groups (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT NOT NULL,
	project_id INTEGER DEFAULT NULL,
	ticket_id INTEGER DEFAULT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE projects (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL,
    sync_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE tickets (
	id INTEGER PRIMARY KEY,
	ticket_id INTEGER NOT NULL,
	project_id INTEGER NOT NULL,
	name TEXT NOT NULL,
	sync_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
	FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE VIEW tickets_extra AS
	SELECT p.id as project_id, p.name as project_name,
		t.ticket_id as ticket_id, t.name as ticket_name
	FROM projects p INNER JOIN tickets t ON p.id = t.project_id;

-- Default data follows
INSERT INTO groups(id, name) VALUES (1, 'None');
