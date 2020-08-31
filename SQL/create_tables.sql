create table games (game_id int auto_increment primary key, pasword char(20) default null, turn int(11) default '0', created timestamp null default current_timestamp, winner char(1) default 
null);
create table players (game_id int, player char(1), player_name varchar(50) default null, primary key (game_id, player), constraint foreign key (game_id) references games(game_id) on delete cas
cade);
create table board (game_id int, row int, col int, player char(1) default null, primary key(game_id, row, col), constraint foreign key (game_id) references games(game_id) on delete cascade);
