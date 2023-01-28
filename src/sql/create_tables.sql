-- Creation of account table
CREATE TABLE IF NOT EXISTS account (
  account_id CHAR(1) PRIMARY KEY,
  email VARCHAR(250) UNIQUE NOT NULL,
  password BYTEA NULL,
  initialized BOOLEAN NOT NULL
);

-- Creation of loginfo table
CREATE TABLE IF NOT EXISTS loginfo (
  loginfo_id SERIAL PRIMARY KEY,
  account_id CHAR(1) NOT NULL,
  log_date TIMESTAMP NOT NULL,
  log_description VARCHAR(100),
  CONSTRAINT fk_account
      FOREIGN KEY(account_id)
    REFERENCES account(account_id)
);

-- Fill account table
INSERT INTO account(account_id, email, initialized)
VALUES ('A', 'a@unknown.com', FALSE),
       ('B', 'b@unknown.com', FALSE),
       ('C', 'c@unknown.com', FALSE),
       ('D', 'd@unknown.com', FALSE)
ON CONFLICT (account_id) DO NOTHING;
