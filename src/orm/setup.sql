drop database if exists featurefactory;

create database featurefactory;

use featurefactory;

create table users (
    id int NOT NULL AUTO_INCREMENT,
    name varchar(200) NOT NULL,
    password varchar(200) NOT NULL, primary key (id)
);

create table problems (
    id int(11) NOT NULL AUTO_INCREMENT,
    name varchar(100) NOT NULL,
    primary key (id),
    created_at timestamp DEFAULT CURRENT_TIMESTAMP
);

create table notebooks (
    id int(11) NOT NULL AUTO_INCREMENT,
    name varchar(100) NOT NULL,
    user_id int(11) DEFAULT NULL,
    problem_id int(11) DEFAULT NULL,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP,

    primary key (id),
    key user_id (user_id),
    key problem_id (problem_id),
    constraint notebooks_ibfk_1 FOREIGN KEY (user_id) REFERENCES users(id),
    constraint notebooks_ibfk_2 FOREIGN KEY (problem_id) REFERENCES problems (id)
);

create table features (
    id int(11) NOT NULL AUTO_INCREMENT,
    name varchar(100) NOT NULL,
    user_id int(11) DEFAULT NULL,
    problem_id int(11) NOT NULL,
    score float DEFAULT NULL,
    code text NOT NULL,
    md5 varchar(32) DEFAULT NULL,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP,

    primary key (id) ,
    key user_id (user_id),
    key problem_id (problem_id),
    constraint features_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (id),
    constraint features_ibfk_2 FOREIGN KEY (problem_id) REFERENCES problems (id)
);

-- factory.py uses a specific problem from the database, so you need to add one before it will run
-- INSERT into problems (name, created_at) VALUES ('problem_name', NOW());
