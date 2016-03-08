drop table if exists meals;
create table meals (
  english_name text not null,
  chinese_name text not null,
  price REAL not null,
  image_url text not null
);

drop table if exists orders;
create table orders (
  order_number int not null,
  order_time TIME not null,
  order_contents text not null
);
