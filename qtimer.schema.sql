create table timers (
	id integer primary key autoincrement,
	group_id integer,
	name text not null,
	note text,
	start timestamp,
	end timestamp
);


create table groups (
	id integer primary key autoincrement,
	name text not null,
    project_id integer,
    ticket_id integer
);

create table projects (
	id integer primary key,
	name text not null,
    sync_date timestamp default current_timestamp
);

create table tickets (
	id integer primary key,
	project_id integer,
	name text not null,
	sync_date timestamp default current_timestamp
);
