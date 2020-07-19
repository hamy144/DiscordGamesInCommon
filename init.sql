create database discordbot;

create table if not exists steamids(
    discordid bigint not null primary key,
    steamid bigint not null
);