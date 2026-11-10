-- Simulated city data for development and demonstration (Łódź city centre).
-- password_hash values are PLACEHOLDERS (not real bcrypt hashes). Demo users
-- will be created through POST /auth/register once the service exists (Lab 5).
INSERT INTO users (id, email, password_hash, display_name, role) VALUES
 ('00000000-0000-0000-0000-000000000001', 'admin@parking.local',
  '$2b$12$C6UzMDM.H6dfI/f/IKcEeO5Q7b0aJ8YQb9h0xYk0uX9F1bQm4Y6a2', 'Admin', 'ADMIN'),
 ('00000000-0000-0000-0000-000000000002', 'driver@parking.local',
  '$2b$12$C6UzMDM.H6dfI/f/IKcEeO5Q7b0aJ8YQb9h0xYk0uX9F1bQm4Y6a2', 'Demo Driver', 'DRIVER');

INSERT INTO parking_facilities (id, name, address, latitude, longitude, data_source) VALUES
 ('10000000-0000-0000-0000-000000000001', 'Manufaktura P1', 'ul. Drewnowska 58', 51.779800, 19.447300, 'SEED_SIMULATED'),
 ('10000000-0000-0000-0000-000000000002', 'Piotrkowska Centrum', 'al. Kościuszki 10', 51.766500, 19.455800, 'SEED_SIMULATED'),
 ('10000000-0000-0000-0000-000000000003', 'Łódź Fabryczna', 'pl. Sałacińskiego 1', 51.769000, 19.468900, 'SEED_SIMULATED');

INSERT INTO parking_spaces (facility_id, label, space_type, price_per_hour) VALUES
 ('10000000-0000-0000-0000-000000000001', 'A-01', 'STANDARD', 4.00),
 ('10000000-0000-0000-0000-000000000001', 'A-02', 'STANDARD', 4.00),
 ('10000000-0000-0000-0000-000000000001', 'A-03', 'EV',       6.00),
 ('10000000-0000-0000-0000-000000000002', 'B-01', 'STANDARD', 5.50),
 ('10000000-0000-0000-0000-000000000002', 'B-02', 'DISABLED', 0.00),
 ('10000000-0000-0000-0000-000000000003', 'C-01', 'STANDARD', 3.50),
 ('10000000-0000-0000-0000-000000000003', 'C-02', 'STANDARD', 3.50);
