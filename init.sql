DROP TABLE IF EXISTS accounts;
DROP TABLE IF EXISTS item;
DROP TABLE IF EXISTS purchase;
DROP TABLE IF EXISTS message;
DROP TABLE IF EXISTS likes;
DROP TABLE IF EXISTS inCart;
DROP TABLE IF EXISTS inPurchase;
DROP TABLE IF EXISTS itemImageURL;

CREATE TABLE accounts
(
	email TEXT NOT NULL,
	hash TEXT NOT NULL,
	role INTEGER NOT NULL,
	name TEXT NOT NULL,
	address TEXT NOT NULL,
	postalCode INTEGER NOT NULL,
	phone INTEGER,
	PRIMARY KEY (email)
);

CREATE TABLE item
(
	itemID INTEGER NOT NULL,
	name TEXT NOT NULL,
	description TEXT,
	price REAL NOT NULL,
	quantity INTEGER NOT NULL,
	sold INTEGER NOT NULL,
	PRIMARY KEY (itemID)
);

CREATE TABLE purchase
(
	purchaseID INTEGER NOT NULL,
	email TEXT NOT NULL,
	PRIMARY KEY (purchaseID),
	FOREIGN KEY (email) REFERENCES accounts(email)
);

CREATE TABLE message
(
	content INTEGER NOT NULL,
	messageID INTEGER NOT NULL,
	toEmail TEXT NOT NULL,
	fromEmail TEXT NOT NULL,
	subject TEXT NOT NULL,
	dateAndTime TEXT NOT NULL,
	PRIMARY KEY (messageID),
	FOREIGN KEY (toEmail) REFERENCES accounts(email),
	FOREIGN KEY (fromEmail) REFERENCES accounts(email)
);

CREATE TABLE likes
(
	email INTEGER NOT NULL,
	itemID INTEGER NOT NULL,
	PRIMARY KEY (email, itemID),
	FOREIGN KEY (email) REFERENCES accounts(email),
	FOREIGN KEY (itemID) REFERENCES item(itemID)
);

CREATE TABLE inCart
(
	email INTEGER NOT NULL,
	itemID INTEGER NOT NULL,
	quantity INTEGER NOT NULL,
	PRIMARY KEY (email, itemID),
	FOREIGN KEY (email) REFERENCES accounts(email),
	FOREIGN KEY (itemID) REFERENCES item(itemID)
);

CREATE TABLE inPurchase
(
	itemID INTEGER NOT NULL,
	purchaseID INTEGER NOT NULL,
	quantity INTEGER NOT NULL,
	PRIMARY KEY (itemID, purchaseID),
	FOREIGN KEY (itemID) REFERENCES item(itemID),
	FOREIGN KEY (purchaseID) REFERENCES purchase(purchaseID)
);

CREATE TABLE itemImageURL
(
	imageURL TEXT NOT NULL,
	itemID INTEGER NOT NULL,
	PRIMARY KEY (imageURL, itemID),
	FOREIGN KEY (itemID) REFERENCES item(itemID)
);

INSERT INTO item(
	itemID,
	name,
	description,
	price,
	quantity,
	sold
)VALUES(
	0,
	'Toothpaste',
	'Insert description here.',
	5.99,
	872,
	27
);

INSERT INTO accounts(
	email,
	hash,
	role,
	name,
	address,
	postalCode,
	phone
)VALUES(
	'customer@test.com',
	'148de9c5a7a44d19e56cd9ae1a554bf67847afb0c58f6e12fa29ac7ddfca9940',
	0,
	'name',
	'addr',
	0,
	0
);

INSERT INTO accounts(
	email,
	hash,
	role,
	name,
	address,
	postalCode
)VALUES(
	'staff@test.com',
	'148de9c5a7a44d19e56cd9ae1a554bf67847afb0c58f6e12fa29ac7ddfca9940',
	1,
	'name',
	'addr',
	1
);

INSERT INTO itemImageURL(
	imageURL,
	itemID
)VALUES(
	'https://images.unsplash.com/photo-1610216690558-4aee861f4ab3',
	0
);

INSERT INTO itemImageURL(
	imageURL,
	itemID
)VALUES(
	'https://images.unsplash.com/photo-1602797844551-a8657700eaac',
	0
);
