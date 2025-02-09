-- Create Tables
CREATE TABLE PASNIEDZEJI (
    PASN_ID NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    VARDS VARCHAR2(30),
    UZVARDS VARCHAR2(30),
    LIETOTAJVARDS VARCHAR2(30),
    EPASTS VARCHAR2(50),
    PAROLE VARCHAR2(64)
);

CREATE TABLE ADMINISTRATORS (
    ADMIN_ID NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    VARDS VARCHAR2(30),
    UZVARDS VARCHAR2(30),
    LIETOTAJVARDS VARCHAR2 (30),
    EPASTS VARCHAR2(50),
    PAROLE VARCHAR2(64)
);

CREATE TABLE GRUPA (
    GRUPA_ID INTEGER PRIMARY KEY,
    NOSAUKUMS VARCHAR2(30) UNIQUE,
    SEMINARANR INTEGER,
    CONSTRAINT GRUPA_PASNIEDZEJI_FK FOREIGN KEY (SEMINARANR) REFERENCES SEMINARI(SEMINARANR)
);

CREATE TABLE STUDENTI (
    STUD_ID NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    VARDS VARCHAR2(30),
    UZVARDS VARCHAR2(30),
    LIETOTAJVARDS VARCHAR2 (30),
    EPASTS VARCHAR2(50),
    PAROLE VARCHAR2(64),
    GRUPA_ID INTEGER,
    CONSTRAINT GRUPA_STUDENTI_FK FOREIGN KEY (GRUPA_ID) REFERENCES GRUPA(GRUPA_ID)
);

CREATE TABLE RAKSTI (
    RAKSTANR INTEGER PRIMARY KEY,  
    NOSAUKUMS VARCHAR2(50),  
    STUDENTUGRUPA VARCHAR2(30),
    STUD_ID INTEGER,
    CONSTRAINT STUDENTI_RAKSTI_FK FOREIGN KEY (STUD_ID) REFERENCES STUDENTI(STUD_ID)
);

CREATE TABLE SEMINARI (
    NOSAUKUMS VARCHAR2(50) PRIMARY KEY,   
    SEMINARANR INTEGER UNIQUE,
    DATUMS TIMESTAMP, 
    VIETA VARCHAR2(30),
    PASN_ID INTEGER,
    CONSTRAINT SEMINARI_PASNIEDZEJI_FK FOREIGN KEY (PASN_ID) REFERENCES PASNIEDZEJI(PASN_ID)
);

CREATE TABLE SEMINARI_RAKSTI (
    RAKSTANR INTEGER,
    SEMINARANR INTEGER,
    PRIMARY KEY (RAKSTANR, SEMINARANR),
    CONSTRAINT RAKSTI_SEMINARI_FK FOREIGN KEY (RAKSTANR) REFERENCES RAKSTI(RAKSTANR),
    CONSTRAINT SEMINARI_RAKSTI_FK FOREIGN KEY (SEMINARANR) REFERENCES SEMINARI(SEMINARANR)
);

-- Pievienojam pasniedzējus
INSERT INTO PASNIEDZEJI (VARDS, UZVARDS, LIETOTAJVARDS, EPASTS, PAROLE) --parole(Parole123)
VALUES ('Jānis', 'Kalniņš', 'JanKal', 'janis.kalnins@example.com', '20479b35a5e168bbbb446a59f3a7dc324293ef41a38096431310a316b19d99f2');

INSERT INTO PASNIEDZEJI (VARDS, UZVARDS, LIETOTAJVARDS, EPASTS, PAROLE) --parole(AnnaParole)
VALUES ('Anna', 'Bērziņa', 'PasniedzAnna', 'anna.berzina@example.com', '9444708f96fa644af43137c8e608916cb0cb3a629726c1954137449730c56480');

-- Pievienojam administratoru
INSERT INTO ADMINISTRATORS (VARDS, UZVARDS, LIETOTAJVARDS, EPASTS, PAROLE) --parole(Admin123)
VALUES ('Pēteris', 'Liepa', 'PeterAdmin', 'peteris.liepa@example.com', '3b612c75a7b5048a435fb6ec81e52ff92d6d795a8b5a9c17070f6a63c97a53b2');

-- Pievienojam seminārus
INSERT INTO SEMINARI (SEMINARANR, NOSAUKUMS, DATUMS, VIETA, PASN_ID)
VALUES (1, 'Datu analīzes seminārs', TO_TIMESTAMP('2024-03-15 10:30:00', 'YYYY-MM-DD HH24:MI:SS'), 'Rīga', 1);

INSERT INTO SEMINARI (SEMINARANR, NOSAUKUMS, DATUMS, VIETA, PASN_ID)
VALUES (2, 'MI un tā pielietojums', TO_TIMESTAMP('2024-04-10 14:00:00', 'YYYY-MM-DD HH24:MI:SS'), 'Liepāja', 2);

-- Pievienojam grupas
INSERT INTO GRUPA (GRUPA_ID, NOSAUKUMS, SEMINARANR)
VALUES (1, 'Datu analīze', 1);

INSERT INTO GRUPA (GRUPA_ID, NOSAUKUMS, SEMINARANR)
VALUES (2, 'Mākslīgais intelekts', 2);

-- Pievienojam studentus
INSERT INTO STUDENTI (VARDS, UZVARDS, LIETOTAJVARDS, EPASTS, PAROLE, GRUPA_ID) --parole(Stud123)
VALUES ('Marta', 'Ozoliņa', 'MG1234', 'marta.ozolina@example.com', '6e81b51ae06e9803d46257a3246b0e262331f06d30a30980b4e1d7ea176205cb', 1);

INSERT INTO STUDENTI (VARDS, UZVARDS, LIETOTAJVARDS, EPASTS, PAROLE, GRUPA_ID) --parole(Stud456)
VALUES ('Andris', 'Eglītis', 'MG2435', 'andris.eglitiss@example.com', 'aa4dd218269b2a0a1718a2b507458fd0c3366fda82870f32485fcbd9dde9f1dd', 1);

INSERT INTO STUDENTI (VARDS, UZVARDS, LIETOTAJVARDS, EPASTS, PAROLE, GRUPA_ID) --parole(Stud789)
VALUES ('Laura', 'Kļaviņa', 'MG782', 'laura.klavina@example.com', '39a76bc42d4a89ee70743c6d5f7718e384acae0a0a765da7301013656be15ab2', 1);

INSERT INTO STUDENTI (VARDS, UZVARDS, LIETOTAJVARDS, EPASTS, PAROLE, GRUPA_ID) --parole(StudABC)
VALUES ('Edgars', 'Zālītis', 'BH2765', 'edgars.zalitis@example.com', 'cda221a33616982c25e5ae3af854db3d269613df325a0e90c70a79534a92f073', 2);

INSERT INTO STUDENTI (VARDS, UZVARDS, LIETOTAJVARDS, EPASTS, PAROLE, GRUPA_ID) --parole(StudDEF)
VALUES ('Ilze', 'Krūmiņa', 'BH9087', 'ilze.krumina@example.com', '6b7360b2ffe6b151d19ed1676b6832f99969199c6d77b86c77190c415b86ab2f', 2);

INSERT INTO STUDENTI (VARDS, UZVARDS, LIETOTAJVARDS, EPASTS, PAROLE, GRUPA_ID) --parole(StudGHI)
VALUES ('Juris', 'Lūsis', 'BH9992', 'juris.lusis@example.com', 'c1c5fbfabca6c6b3157b99c2fb762a98b2919ff4a9a7158ada6a572e3fec1e17', 2);

-- Pievienojam rakstus
INSERT INTO RAKSTI (RAKSTANR, NOSAUKUMS, STUDENTUGRUPA, STUD_ID)
VALUES (101, 'Datu analīzes metodes', 'Datu analīze', 1);

INSERT INTO RAKSTI (RAKSTANR, NOSAUKUMS, STUDENTUGRUPA, STUD_ID)
VALUES (102, 'Neironu tīkli un MI', 'Mākslīgais intelekts', 4);

INSERT INTO RAKSTI (RAKSTANR, NOSAUKUMS, STUDENTUGRUPA, STUD_ID)
VALUES (103, 'SQL indeksu optimizācija', 'Datu analīze', 2);

-- Pievienojam saistību starp semināriem un rakstiem
INSERT INTO SEMINARI_RAKSTI (RAKSTANR, SEMINARANR)
VALUES (101, 1);

INSERT INTO SEMINARI_RAKSTI (RAKSTANR, SEMINARANR)
VALUES (102, 2);

INSERT INTO SEMINARI_RAKSTI (RAKSTANR, SEMINARANR)
VALUES (103, 1);

