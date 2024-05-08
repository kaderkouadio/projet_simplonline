DROP DATABASE IF EXISTS BD_GOUA
CREATE DATABASE BD_GOUA


USE BD_GOUA;

DROP TABLE IF EXISTS Utilisateurs;
CREATE TABLE Utilisateurs (
    IdUtilisateurs INT NOT NULL PRIMARY KEY IDENTITY(1,1),
	Images VARCHAR(MAX),
    Nom VARCHAR(200),
    Prenoms VARCHAR(200),
    Telephone VARCHAR(200),
	Adresse VARCHAR(200),
    Email VARCHAR(200),
    Mot_de_pass VARCHAR(200),
    Roles VARCHAR(200),
);



select * from Utilisateurs

select * from Produits

select * from Stocks

select * from Clients

select * from Vente

select * from Fournisseurs

DELETE FROM Utilisateurs;


DROP TABLE IF EXISTS Fournisseurs;
CREATE TABLE Fournisseurs (
    IdFournisseurs INT NOT NULL PRIMARY KEY IDENTITY(1,1),
    NomEntreprise VARCHAR(200),
	Nom_Contact VARCHAR(200),
	Adresse VARCHAR(200),
	Telephone VARCHAR(200),
	Email VARCHAR(200),
	Conditions_paiement VARCHAR(200),   
);


DROP TABLE IF EXISTS Clients;
CREATE TABLE Clients (
    IdClients INT NOT NULL PRIMARY KEY IDENTITY(1,1),
    Nom VARCHAR(200),
    Prenoms VARCHAR(200),
    Telephone VARCHAR(200),
    Email VARCHAR(200),
    Genre VARCHAR(200),
	Adresse VARCHAR(200),
	DatesCreation VARCHAR(200),
);



DROP TABLE IF EXISTS Produits;
CREATE TABLE Produits (
    IdProduits INT NOT NULL PRIMARY KEY IDENTITY(1,1),
    NomProduit VARCHAR(200),
    Descriptions VARCHAR(MAX),
	Categories VARCHAR(200),
	DateAjout VARCHAR(200),
    PrixUnitaire DECIMAL(10, 2),
    IdFournisseurs INT NOT NULL,
    FOREIGN KEY (IdFournisseurs) REFERENCES Fournisseurs (IdFournisseurs)
);




DROP TABLE IF EXISTS Stocks;
CREATE TABLE Stocks (
    IdStocks INT NOT NULL PRIMARY KEY IDENTITY(1,1),
    DateMiseAjout DATE, 
    Quantite INT,
    Statut VARCHAR(200),
    IdProduits INT NOT NULL,
    FOREIGN KEY (IdProduits) REFERENCES Produits (IdProduits)
);



DROP TABLE IF EXISTS Vente;
CREATE TABLE Vente (
    IdVente INT NOT NULL PRIMARY KEY IDENTITY(1,1),
    Quantite INT,
    PrixUnitaire DECIMAL(10, 2),
    Montant_Total DECIMAL(10, 2),
    Dates_vente date,
	Mode_paiement VARCHAR(200),
    IdProduits INT NOT NULL,
	IdClients INT NOT NULL,
	IdUtilisateurs INT NOT NULL,
    FOREIGN KEY (IdProduits) REFERENCES Produits (IdProduits),
    FOREIGN KEY (IdClients) REFERENCES Clients (IdClients),
	FOREIGN KEY (IdUtilisateurs) REFERENCES Utilisateurs (IdUtilisateurs)
);   

