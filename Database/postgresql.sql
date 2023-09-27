CREATE DATABASE animal_chipization;
\c animal_chipization

CREATE TABLE IF NOT EXISTS account (
	id BIGSERIAL PRIMARY KEY,
	firstName VARCHAR(256),
	lastName VARCHAR(256),
	email VARCHAR(256) UNIQUE,
	password VARCHAR(256),
	role VARCHAR(256) DEFAULT 'USER'
);

CREATE TABLE IF NOT EXISTS location_ (
	id BIGSERIAL PRIMARY KEY,
	latitude DOUBLE PRECISION,
	longitude DOUBLE PRECISION,
	UNIQUE (latitude, longitude)
);

CREATE TABLE IF NOT EXISTS area (
	id BIGSERIAL PRIMARY KEY,
	name VARCHAR(256)
);

CREATE TABLE IF NOT EXISTS endpoint (
	areaId BIGINT REFERENCES area (id),
	locationId BIGINT REFERENCES location_ (id)
);

CREATE TABLE IF NOT EXISTS type (
	id BIGSERIAL PRIMARY KEY,
	type VARCHAR(256) UNIQUE
);

CREATE TABLE IF NOT EXISTS animal (
	id BIGSERIAL PRIMARY KEY,
	-- animalTypes [long],
	weight FLOAT,
	length FLOAT,
	height FLOAT,
	gender INT, -- MALE, FEMALE, OTHER: [0, 1, 2]
	lifeStatus INT, -- ALIVE, DEAD: [0, 1]
	chippingDateTime TIMESTAMP,
	chipperId INT,
	chippingLocationId BIGINT,
	-- visitedLocations [long],
	deathDateTime TIMESTAMP,
	FOREIGN KEY (chippingLocationId) REFERENCES location_ (id),
	FOREIGN KEY (chipperId) REFERENCES account (id)
);

CREATE TABLE IF NOT EXISTS animaltypes (
	animalId BIGINT,
	typeId BIGINT,
	UNIQUE (animalId, typeId),
	FOREIGN KEY (animalId) REFERENCES animal (id),
	FOREIGN KEY (typeId) REFERENCES type (id)
);
	
CREATE TABLE IF NOT EXISTS visitedlocations (
	id BIGSERIAL PRIMARY KEY,
	animalId BIGINT,
	locationId BIGINT,
	visitDateTime TIMESTAMP,
	UNIQUE (animalId, locationId),
	FOREIGN KEY (animalId) REFERENCES animal (id),
	FOREIGN KEY (locationId) REFERENCES location_ (id)
);

INSERT INTO account (firstName, lastName, email, password, role) VALUES ('adminFirstName', 'adminLastName', 'admin@simbirsoft.com', 'qwerty123', 'ADMIN');
INSERT INTO account (firstName, lastName, email, password, role) VALUES ('chipperFirstName', 'chipperLastName', 'chipper@simbirsoft.com', 'qwerty123', 'CHIPPER');
INSERT INTO account (firstName, lastName, email, password, role) VALUES ('userFirstName', 'userLastName', 'user@simbirsoft.com', 'qwerty123', 'USER');