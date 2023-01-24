-- Creation of user_account table
CREATE TABLE IF NOT EXISTS user_account (
  id CHAR(1) NOT NULL,
  email VARCHAR(250) NOT NULL,
  initialized BIT NOT NULL,
  PRIMARY KEY (id)
);

--IF NOT EXISTS(SELECT 1 FROM user_account)
--  INSERT INTO user_account VALUES ('A', 'gio@test.be', 0);
