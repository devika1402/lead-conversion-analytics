-- db/init.sql
CREATE TABLE club (
  club_id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  location TEXT,
  contact TEXT,
  operating_hours TEXT
);

CREATE TABLE staff (
  staff_id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT,
  phone TEXT,
  role TEXT,
  hired_date DATE,
  performance_score INT,
  club_id INT REFERENCES club(club_id)
);

CREATE TABLE lead (
  lead_id SERIAL PRIMARY KEY,
  name TEXT,
  email TEXT,
  phone TEXT,
  source TEXT,
  creation_date DATE,
  status TEXT,
  lead_score INT,
  preferred_communication TEXT,
  conversion_date DATE,
  converted_to_member BOOLEAN,
  conversion_channel TEXT,
  staff_id INT REFERENCES staff(staff_id),
  club_id INT REFERENCES club(club_id)
);

CREATE TABLE member (
  member_id SERIAL PRIMARY KEY,
  name TEXT,
  email TEXT,
  phone TEXT,
  join_date DATE,
  membership_status TEXT,
  club_id INT REFERENCES club(club_id)
);

CREATE TABLE subscription (
  subscription_id SERIAL PRIMARY KEY,
  member_id INT REFERENCES member(member_id),
  subscription_type TEXT,
  start_date DATE,
  end_date DATE,
  price NUMERIC,
  payment_status TEXT
);

CREATE TABLE staff_metrics (
    staff_id INTEGER,
    name TEXT,
    month TEXT,
    sales_ranking INTEGER,
    average_conversion_rate TEXT,
    percentage_new_revenue TEXT
);

-- Seed Clubs (Static Data)
INSERT INTO club (name, location) VALUES
('Downtown Gym','Main St'),
('Northside Gym','2nd Ave'),
('Eastside Gym','Maple Rd');

-- Seed 3 salespeople (static data)
INSERT INTO staff (name, email, role, hired_date, club_id) VALUES
('Lucas','lucas@vg.com','Sales','2025-01-05',1),
('Maria','maria@vg.com','Sales','2025-02-10',2),
('Andrea','andrea@vg.com','Sales','2025-03-15',3);

-- Seed Leads (Dynamic Data)
INSERT INTO lead (name, email, phone, source, creation_date, status, lead_score, 
                  preferred_communication, converted_to_member, conversion_date, 
                  conversion_channel, staff_id, club_id)
VALUES 
('John Doe', 'john.doe1@example.com', '123-456-7801', 'Online', '2025-02-01', 'Converted', 80, 
 'Email', TRUE, '2025-02-03', 'Website', 1, 1),
('Jane Smith', 'jane.smith1@example.com', '123-456-7802', 'Referral', '2025-02-10', 'New', 65, 
 'Phone', FALSE, NULL, NULL, 2, 2),
('Alice Johnson', 'alice.johnson1@example.com', '123-456-7803', 'Social Media', '2025-02-15', 
 'Converted', 90, 'Email', TRUE, '2025-02-17', 'Social Media', 3, 3),
('John Doe', 'john.doe2@example.com', '123-456-7804', 'Referral', '2025-03-05', 'Converted', 75, 
 'Email', TRUE, '2025-03-07', 'Website', 1, 1),
('Jane Smith', 'jane.smith2@example.com', '123-456-7805', 'Online', '2025-03-10', 'New', 60, 
 'Phone', FALSE, NULL, NULL, 2, 2),
('Alice Johnson', 'alice.johnson2@example.com', '123-456-7806', 'Referral', '2025-03-15', 
 'Converted', 85, 'Email', TRUE, '2025-03-18', 'Referral', 3, 3);

-- Populate members for every converted lead
INSERT INTO member (
    name,
    email,
    phone,
    join_date,
    membership_status,
    club_id
)
SELECT DISTINCT
    l.name,
    l.email,
    l.phone,
    l.conversion_date    AS join_date,
    'Active'             AS membership_status,
    l.club_id
FROM lead l
WHERE l.converted_to_member = TRUE
ON CONFLICT (email) DO NOTHING;

-- Insert subscriptions
INSERT INTO subscription (
    member_id,
    subscription_type,
    start_date,
    end_date,
    price,
    payment_status
)
SELECT
    m.member_id,
    'Monthly'                         AS subscription_type,
    l.conversion_date                 AS start_date,
    l.conversion_date + INTERVAL '1 month' - INTERVAL '1 day' AS end_date,
    100.00                            AS price,
    'Paid'                            AS payment_status
FROM lead l
JOIN member m
  ON m.email = l.email
WHERE l.converted_to_member = TRUE;