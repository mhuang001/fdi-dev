create table fdi_action_record(
  id bigint(20) not null primary key auto_increment,
  username varchar(100),
  action varchar(20),
  poolname varchar(200),
  change_time datetime(6)
);
