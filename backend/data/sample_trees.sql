-- Sample Bengaluru Tree Records (50+ rows across wards 1–10)
USE smart_urban_tree;

INSERT INTO trees (species, latitude, longitude, ward, age_years, health_score, last_checked, status) VALUES
-- Ward 1
('Peepal', 12.971599, 77.594566, 1, 25, 82, '2024-10-15', 'healthy'),
('Neem', 12.972100, 77.595200, 1, 18, 65, '2024-09-20', 'stressed'),
('Rain Tree', 12.970500, 77.593800, 1, 30, 90, '2024-10-01', 'healthy'),
('Gulmohar', 12.973000, 77.596000, 1, 12, 45, '2024-08-15', 'diseased'),
('Banyan', 12.971000, 77.594000, 1, 50, 95, '2024-10-20', 'healthy'),

-- Ward 2
('Peepal', 12.980000, 77.600000, 2, 20, 70, '2024-10-10', 'healthy'),
('Neem', 12.981000, 77.601000, 2, 15, 55, '2024-09-05', 'stressed'),
('Ashoka', 12.979500, 77.599500, 2, 8, 88, '2024-10-18', 'healthy'),
('Tamarind', 12.982000, 77.602000, 2, 35, 75, '2024-09-28', 'healthy'),
('Gulmohar', 12.978000, 77.598000, 2, 10, 30, '2024-07-20', 'diseased'),

-- Ward 3
('Banyan', 12.960000, 77.580000, 3, 60, 92, '2024-10-22', 'healthy'),
('Rain Tree', 12.961000, 77.581000, 3, 22, 68, '2024-09-15', 'stressed'),
('Neem', 12.962000, 77.582000, 3, 14, 50, '2024-08-30', 'stressed'),
('Peepal', 12.963000, 77.583000, 3, 28, 85, '2024-10-12', 'healthy'),
('Coconut', 12.964000, 77.584000, 3, 18, 72, '2024-09-25', 'healthy'),

-- Ward 4
('Neem', 12.950000, 77.570000, 4, 10, 15, '2024-10-01', 'critical'),
('Gulmohar', 12.951000, 77.571000, 4, 7, 60, '2024-09-10', 'healthy'),
('Ashoka', 12.952000, 77.572000, 4, 12, 78, '2024-10-05', 'healthy'),
('Tamarind', 12.953000, 77.573000, 4, 40, 88, '2024-10-15', 'healthy'),
('Rain Tree', 12.954000, 77.574000, 4, 25, 42, '2024-08-20', 'diseased'),

-- Ward 5
('Peepal', 12.990000, 77.610000, 5, 32, 90, '2024-10-20', 'healthy'),
('Banyan', 12.991000, 77.611000, 5, 45, 95, '2024-10-18', 'healthy'),
('Neem', 12.992000, 77.612000, 5, 16, 72, '2024-10-01', 'healthy'),
('Gulmohar', 12.993000, 77.613000, 5, 9, 55, '2024-09-12', 'stressed'),
('Coconut', 12.994000, 77.614000, 5, 20, 80, '2024-10-10', 'healthy'),

-- Ward 6
('Rain Tree', 12.940000, 77.560000, 6, 28, 65, '2024-09-28', 'stressed'),
('Neem', 12.941000, 77.561000, 6, 11, 20, '2024-10-02', 'critical'),
('Ashoka', 12.942000, 77.562000, 6, 14, 82, '2024-10-14', 'healthy'),
('Tamarind', 12.943000, 77.563000, 6, 38, 90, '2024-10-19', 'healthy'),
('Peepal', 12.944000, 77.564000, 6, 22, 70, '2024-09-30', 'healthy'),

-- Ward 7
('Neem', 12.930000, 77.550000, 7, 8, 12, '2024-10-03', 'critical'),
('Gulmohar', 12.931000, 77.551000, 7, 6, 35, '2024-08-25', 'diseased'),
('Peepal', 12.932000, 77.552000, 7, 18, 60, '2024-09-18', 'stressed'),
('Banyan', 12.933000, 77.553000, 7, 40, 88, '2024-10-16', 'healthy'),
('Rain Tree', 12.934000, 77.554000, 7, 15, 48, '2024-09-05', 'stressed'),

-- Ward 8
('Coconut', 12.920000, 77.540000, 8, 25, 85, '2024-10-17', 'healthy'),
('Neem', 12.921000, 77.541000, 8, 13, 73, '2024-10-08', 'healthy'),
('Ashoka', 12.922000, 77.542000, 8, 9, 90, '2024-10-20', 'healthy'),
('Tamarind', 12.923000, 77.543000, 8, 42, 78, '2024-09-22', 'healthy'),
('Gulmohar', 12.924000, 77.544000, 8, 11, 62, '2024-09-28', 'stressed'),

-- Ward 9
('Peepal', 12.910000, 77.530000, 9, 29, 88, '2024-10-19', 'healthy'),
('Rain Tree', 12.911000, 77.531000, 9, 24, 75, '2024-10-07', 'healthy'),
('Banyan', 12.912000, 77.532000, 9, 55, 93, '2024-10-21', 'healthy'),
('Neem', 12.913000, 77.533000, 9, 17, 58, '2024-09-16', 'stressed'),
('Coconut', 12.914000, 77.534000, 9, 15, 80, '2024-10-11', 'healthy'),

-- Ward 10
('Gulmohar', 12.900000, 77.520000, 10, 8, 40, '2024-08-30', 'diseased'),
('Neem', 12.901000, 77.521000, 10, 20, 68, '2024-09-24', 'stressed'),
('Ashoka', 12.902000, 77.522000, 10, 11, 84, '2024-10-13', 'healthy'),
('Tamarind', 12.903000, 77.523000, 10, 36, 91, '2024-10-18', 'healthy'),
('Peepal', 12.904000, 77.524000, 10, 22, 76, '2024-10-05', 'healthy');

-- Sample maintenance log entries
INSERT INTO maintenance_log (tree_id, action, date, officer_name, notes, approved_by) VALUES
(4,  'Fungicide application', '2024-08-16', 'Officer Rajan', 'Applied copper fungicide spray', 'Supervisor Mehta'),
(10, 'Soil treatment',        '2024-07-21', 'Officer Priya', 'Added lime to adjust pH',         'Supervisor Mehta'),
(16, 'Emergency inspection',  '2024-10-02', 'Officer Rajan', 'Root rot confirmed, flagged critical', 'Supervisor Mehta'),
(31, 'Watering schedule set', '2024-10-04', 'Officer Kumar', 'Daily watering for 2 weeks',       'Supervisor Mehta'),
(26, 'Pruning completed',     '2024-10-03', 'Officer Priya', 'Dead branches removed',           'Supervisor Mehta');
