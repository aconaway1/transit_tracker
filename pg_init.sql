create table lines (
	id serial PRIMARY KEY,
	line_name VARCHAR (50),
	friendly_name VARCHAR (50)
);

insert into lines (line_name, friendly_name) values
  ('reds', 'Red Line, S'),
  ('redn', 'Red Line, N'),
  ('golds', 'Gold Line, S'),
  ('goldn', 'Gold Line, N'),
  ('bluee', 'Blue Line, E'),
  ('bluew', 'Blue Line, W'),
  ('greene', 'Green Line, E'),
  ('greenw', 'Green Line, W')
;

create table observed_cars (
	car_no INT NOT NULL,
	line INT,
	observation_date DATE
);