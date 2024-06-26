from flask import Flask, render_template, url_for, redirect, request, session, flash,make_response,send_file,jsonify
from functools import wraps
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import pyodbc
import os
import pandas as pd
from datetime import datetime
import random
import string
from flask_paginate import Pagination, get_page_parameter
from werkzeug.security import generate_password_hash, check_password_hash
import plotly.express as px

#************** pour l'envoi des emails*****************
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


#************** pour generer de facon fictive des donnees*****************
# from faker import Faker
import csv
# fake = Faker()

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table

#************** Exporter vers PDF, Excel*****************


from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table
import io
from openpyxl import Workbook
import tabula
import pdfplumber



app = Flask(__name__)



UPLOAD_FOLDER = "static/images/photos"

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER



app.secret_key = "votre_clé_secrète"
# Configuration de la connexion à SQL Server
app.config["SQL_SERVER_CONNECTION_STRING"] = """
    Driver={SQL Server};
    Server=DESKTOP-VJVVU51\SQLEXPRESS;
    Database=BD_GOUA;
    Trusted_Connection=yes;"""
      
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS 

    
# *********************** enregistrement***********************

@app.route("/register", methods=['GET', 'POST'])
def register():
    
    if request.method == 'POST':
        # Images= request.form['Images']
        Nom= request.form['Nom']
        Prenoms= request.form['Prenoms']
        Email= request.form['Email']
        Mot_de_pass= request.form['Mot_de_pass']
        Adresse = request.form['Adresse']
        Telephone = request.form['Telephone']
        Roles = request.form['Roles']
        
         # Traitement des images
        image_urls = []
        if "myfiles[]" in request.files:
            image_files = request.files.getlist("myfiles[]")
            for image_file in image_files:
                if image_file and allowed_file(image_file.filename):
                    filename = secure_filename(image_file.filename)
                    image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    image_file.save(image_path)
                    image_urls.append(image_path)
    
        # Vérifier si l'email existe déjà
        connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
        cursor = connection.cursor()
        # cursor.execute("SELECT IdUtilisateurs FROM Utilisateurs WHERE Email=?", (Email,))
        cursor.execute("SELECT * FROM Utilisateurs WHERE Email = ? AND Mot_de_pass = ?", (Email, Mot_de_pass))

        existing_user = cursor.fetchone()

        if existing_user:
            flash('L\'adresse e-mail existe déjà. Veuillez choisir une autre adresse e-mail.', 'error')
            return redirect(url_for('register'))

        # Hacher le mot de passe
        hashed_password = generate_password_hash(Mot_de_pass)

        # Effectuer l'insertion uniquement si l'email n'existe pas
        cursor.execute("INSERT INTO Utilisateurs (Images, Nom, Prenoms, Email, Mot_de_pass, Adresse, Telephone, Roles) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (",".join(image_urls) if image_urls else None, Nom, Prenoms, Email, hashed_password, Adresse, Telephone, Roles))
        connection.commit()
        cursor.execute("SELECT * FROM Utilisateurs WHERE Email = ? AND Mot_de_pass = ?", (Email, Mot_de_pass))

        IdUtilisateurs = cursor.fetchone()

        session['IdUtilisateurs'] = IdUtilisateurs
        session['user'] = Email

        cursor.close()
        connection.close()

        return redirect(url_for('connexion'))

    return render_template("Utilisateurs/register.html")

   
    
# *************************  page de connexion(authentification ) **********************************



@app.route('/', methods=['GET', 'POST'])
def connexion():
    if request.method == 'POST':
        Email = request.form.get('email')
        Mot_de_pass = request.form.get('password')
        # Roles = request.form.get('Roles')
        
        # Vérifier si les champs Email, Mot_de_pass et Roles sont vides
        if not Email or not Mot_de_pass :
            flash("Veuillez saisir une adresse email, un mot de passe et un rôle.", "danger")
            return redirect(url_for('connexion'))

        connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
        cursor = connection.cursor()
        
        # Exécutez une requête SQL pour récupérer l'utilisateur avec l'e-mail et le mot de passe donnés
        cursor.execute("SELECT * FROM Utilisateurs WHERE Email = ? ", (Email))
        utilisateurs = cursor.fetchone()
        print(utilisateurs) 

        if utilisateurs:
            session['IdUtilisateurs'] = utilisateurs[0]
            if check_password_hash(utilisateurs[7], Mot_de_pass) and utilisateurs[8] == 'Administrateur' :
                # Redirection en fonction du rôle
                return redirect(url_for('accueiladmin'))
            elif check_password_hash(utilisateurs[7], Mot_de_pass) and utilisateurs[8] == 'Caissier' :
                return redirect(url_for('accueilVendeur'))
            elif check_password_hash(utilisateurs[7], Mot_de_pass) and utilisateurs[8] == 'Gestionnaire_de_Stocks' :
                return redirect(url_for('accueilGestion'))
            else:
                flash("Adresse Email, mot de passe ou rôle incorrects", "danger")
        else:
            flash("Adresse Email, mot de passe ou rôle incorrects", "danger")

    return render_template('Utilisateurs/login.html')



# @app.route('/deconnexion')
# def deconnexion():
#     # Suppression de toutes les informations stockées dans la session
#     logout()

#     # Redirection de l'utilisateur vers la page de connexion
#     return redirect(url_for('connexion'))



@app.route('/deconnection')
def deconnection():
    session.pop('user', None)
    session.pop('IdUtilisateur', None)
    return redirect(url_for('connexion'))



# *************************  page de profil(utilisateurs ) **********************************

@app.route("/profiladmin", methods=['GET', 'POST'])
def profiladmin():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))

    utilisateurs = cursor.fetchone()
    return render_template('profil/profil_admin.html',utilisateurs=utilisateurs)
 
    

@app.route('/accueilAdmin', methods=['GET', 'POST'])
def accueiladmin():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))

    utilisateurs = cursor.fetchone()
    
    return render_template('accueilAdmin/dashboard/dashboard-crm.html',utilisateurs=utilisateurs )





@app.route('/Rapport', methods=['GET', 'POST'])
def Rapport():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))

    utilisateurs = cursor.fetchone()
    return render_template('accueilAdmin/Rapport.html', utilisateurs=utilisateurs)



@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))

    utilisateurs = cursor.fetchone()
    return render_template('accueilAdmin/prediction.html', utilisateurs=utilisateurs)




@app.route('/accueilGestion', methods=['GET', 'POST'])
def accueilGestion():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))

    utilisateurs = cursor.fetchone()
    return render_template('accueilGestion/dashboard_gestion.html', utilisateurs=utilisateurs)





@app.route('/accueilVendeur', methods=['GET', 'POST'])
def accueilVendeur():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))

    utilisateurs = cursor.fetchone()
    return render_template('accueilVendeur/dashboard_vendeur.html',utilisateurs=utilisateurs)


# **************** fin_connexion(authentification) *********************



@app.route("/Superadmin", methods=['GET', 'POST'])
def Superadmin():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))

    utilisateurs = cursor.fetchone()
    return render_template('Utilisateurs/Super_admin.html',utilisateurs=utilisateurs)




@app.route("/recuperationpassword", methods=['GET', 'POST'])
def recuperationpassword():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))

    utilisateurs = cursor.fetchone()
    return render_template('Utilisateurs/recuperation_password.html',utilisateurs=utilisateurs)




@app.route("/coderecuperation", methods=['GET', 'POST'])
def coderecuperation():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))

    utilisateurs = cursor.fetchone()
    return render_template('Utilisateurs/code_recuperation.html',utilisateurs=utilisateurs)

# ***********************fin-Utilisateurs***********************



@app.route("/dashboardcrm.", methods=['GET', 'POST'])
def dashboardcrm():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))

    utilisateurs = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*) FROM Clients")
    total_clients_row = cursor.fetchone()  
    total_clients = total_clients_row[0] if total_clients_row else 0  
    print(total_clients_row)
    
    
    cursor.execute("SELECT COUNT(*) FROM Fournisseurs")
    total_Fournisseurs_row = cursor.fetchone()  
    total_Fournisseurs = total_Fournisseurs_row[0] if total_Fournisseurs_row else 0  
    print(total_Fournisseurs_row)
    
    cursor.execute("SELECT COUNT(*) FROM Produits")
    total_produits_row = cursor.fetchone()  
    total_produits = total_produits_row[0] if total_produits_row else 0  
    print(total_produits_row)
    
    
    cursor.execute("SELECT COUNT(*) FROM Vente")
    total_Vente_row = cursor.fetchone()  
    total_Vente = total_Vente_row[0] if total_Vente_row else 0  
    print(total_Vente_row)
    

    # Meilleur produit vendu
    cursor.execute("SELECT TOP 1 IdProduits, SUM(Quantite) AS total_sold FROM Vente GROUP BY IdProduits ORDER BY total_sold DESC")
    best_product = cursor.fetchone()

    # Meilleur employé
    # cursor.execute("SELECT TOP 1 Utilisateurs.Nom, Utilisateurs.Prenoms,SUM(Vente.Montant_Total) AS total_sales FROM Vente JOIN Utilisateurs ON Vente.IdUtilisateurs = Utilisateurs.IdUtilisateurs GROUP BY Utilisateurs.Nom,Utilisateurs.Prenoms ORDER BY total_sales DESC")
    # best_employee = cursor.fetchone()

    # Nombre total de ventes par mois/année
    cursor.execute("SELECT YEAR(Dates_vente) AS year, MONTH(Dates_vente) AS month, COUNT(IdVente) AS total_sales FROM Vente GROUP BY YEAR(Dates_vente), MONTH(Dates_vente) ORDER BY year, month")
    sales_by_date = cursor.fetchall()

    # Chiffre d'affaires total par mois/année
    
    cursor.execute("SELECT SUM(Montant_Total) AS chiffre_affaires FROM Vente")
    chiffre_affaires = cursor.fetchall()
    print(chiffre_affaires)
    
    
    cursor.execute("SELECT YEAR(Dates_vente) AS year, MONTH(Dates_vente) AS month,SUM(Montant_Total) AS chiffre_affaires FROM Vente GROUP BY YEAR(Dates_vente),MONTH(Dates_vente) ORDER BY year, month")
    CA_temporel = cursor.fetchall()
    
    
    cursor.execute("SELECT DISTINCT categories FROM Produits")
    categories = cursor.fetchall()
    
    # cursor.execute("SELECT categories FROM Produits JOIN Vente ON Produits.IdProduits = Vente.IdProduits GROUP BY categories ORDER BY SUM(Quantite) DESC LIMIT 5")
    # categories_vendues= cursor.fetchall()


    


# Exécuter la requête pour obtenir le total des ventes par année et les ventes par mois
    # Exécuter la requête pour obtenir le total des ventes par année et les ventes par mois
    cursor.execute('''
    SELECT FORMAT(Dates_vente, 'yyyy-MM') AS year, COUNT(IdVente) AS count 
    FROM vente 
    GROUP BY FORMAT(Dates_vente, 'yyyy-MM')
    ORDER BY year
''')


# Récupérer le total des ventes
    total_ventes_row = cursor.fetchone()
    total_ventes = total_ventes_row[0] if total_ventes_row else 0  

# Récupérer les ventes par mois
    ventes_par_mois = cursor.fetchall()
    year = []  
    data = []  

# Parcourir les résultats pour extraire les années et les ventes
    for item in ventes_par_mois:
         year.append(item[0])  # 
         data.append(item[1])  # 
# Créer le graphique à l'aide de Plotly
    fig = px.line(
        x=year,
        y=data,
        template='plotly_dark')

# Convertir le graphique en HTML
    chart1 = fig.to_html()
    
    
    # Exécuter la requête SQL pour obtenir le chiffre d'affaires par année et par mois
    cursor.execute('''
    SELECT YEAR(Dates_vente) AS year, MONTH(Dates_vente) AS month,
    SUM(Montant_Total) AS chiffre_affaires 
    FROM Vente 
    GROUP BY YEAR(Dates_vente), MONTH(Dates_vente) 
    ORDER BY year, month
''')

# Récupérer les résultats de la requête
    resultats = cursor.fetchall()

# Extraire les années, les mois et les chiffres d'affaires des résultats
    annees = []
    mois = []
    chiffre_affaires = []

    for row in resultats:
        annees.append(row[0])
        mois.append(row[1])
        chiffre_affaires.append(row[2])

# Créer le graphique à l'aide de Plotly
    fig = px.line(
    x=mois,  # ou x=annees si vous souhaitez afficher les années sur l'axe x
    y=chiffre_affaires,
    labels={'x': 'Mois', 'y': 'Chiffre d\'affaires'},
    title='Chiffre d\'affaires par mois',
    template='plotly_dark'
)
# Convertir le graphique en HTML
    chart2 = fig.to_html()

# Fermer le curseur
    cursor.close()

    return render_template('accueilAdmin/dashboard/dashboard-crm.html',utilisateurs=utilisateurs,total_client=total_clients,
                           total_produit=total_produits,total_Fournisseurs=total_Fournisseurs, total_Vente=total_Vente,
                           best_product=best_product,
                           sales_by_date=sales_by_date, chiffre_affaires=chiffre_affaires, CA_temporel=CA_temporel,
                           total_ventes=total_ventes, ventes_par_mois=ventes_par_mois, chart1 = chart1, chart2=chart2, categories=categories)



 # ****** export_pdf**********
  
@app.route("/exportpdf/produits")
def export_produits_pdf():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    # Récupérer les données des utilisateurs depuis la base de données
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateur = cursor.fetchone()  # Utilisation de fetchone() car il s'agit d'une seule ligne
    
    # Récupérer les données des produits depuis la base de données
    cursor.execute("SELECT * FROM Produits")
    produits = cursor.fetchall()  # Utilisation de fetchall() pour obtenir toutes les lignes
    
    pdf_content = generate_pdf(produits, ['NomProduit', 'Descriptions', 'Categories', 'Dateajout', 'PrixUnitaire', 'Quantite', 'IdFournisseurs'])
    return send_pdf(pdf_content, "Produits.pdf")




@app.route("/exportpdf/utilisateurs")
def export_utilisateurs_pdf():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    # Récupérer les données de l'utilisateur actuel depuis la base de données
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateur = cursor.fetchone()  # Utilisation de fetchone() car il s'agit d'une seule ligne
    
    # Récupérer les données de tous les utilisateurs depuis la base de données
    cursor.execute("SELECT * FROM Utilisateurs")
    utilisateurs = cursor.fetchall()  # Utilisation de fetchall() pour obtenir toutes les lignes
    
    pdf_content = generate_pdf(utilisateurs, ['ID', 'Nom', 'Prenoms', 'Telephone', 'Adresse', 'Email', 'Roles'])
    return send_pdf(pdf_content, "Utilisateurs.pdf")


@app.route("/exportpdf/stocks")
def export_stocks_pdf():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    # Récupérer les données de l'utilisateur actuel depuis la base de données
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateur = cursor.fetchone()  # Utilisation de fetchone() car il s'agit d'une seule ligne
    
    # Récupérer les données des stocks depuis la base de données
    cursor.execute("SELECT * FROM Stocks")
    stocks = cursor.fetchall()  # Utilisation de fetchall() pour obtenir toutes les lignes
    
    pdf_content = generate_pdf(stocks, ['ID', 'NomProduit', 'Descriptions', 'Categories', 'Dateajout', 'Quantite', 'PrixUnitaire', 'Statut'])
    return send_pdf(pdf_content, "Stocks.pdf")

    
    
@app.route("/exportpdf/clients", methods=['GET', 'POST'])
def export_clients_pdf():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))
    utilisateurs = cursor.fetchone()
    # Récupérer les données des Clients depuis la base de données
    
    cursor.execute("SELECT * FROM Clients")
    Clients = cursor.fetchall()
    
    pdf_content = generate_pdf(Clients,['ID', 'Nom', 'Prenoms', 'Telephone', 'Email', 'Genre', 'Adresse', 'Dates_de_creation'])
    return send_pdf(pdf_content, "Clients.pdf")


@app.route("/exportpdf/vente")
def export_vente_pdf():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    # Récupérer les données de l'utilisateur actuel depuis la base de données
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateur = cursor.fetchone()  # Utilisation de fetchone() car il s'agit d'une seule ligne
    
    # Récupérer les données des ventes depuis la base de données
    cursor.execute("SELECT * FROM Vente")
    ventes = cursor.fetchall()  # Utilisation de fetchall() pour obtenir toutes les lignes
    
    # Noms des colonnes pour les en-têtes du PDF
    headers = ['IdVente', 'Quantité', 'PrixUnitaire', 'Montant_Total', 'Dates_vente', 'Mode_paiement', 'IdProduits', 'IdClients', 'IdUtilisateurs']

    # Générer le contenu PDF avec les données de vente
    pdf_content = generate_pdf(ventes, headers)
    return send_pdf(pdf_content, "vente.pdf")




# @app.route("/exportpdf/fournisseurs")
# def export_fournisseurs_pdf():
#     IdUser = session.get('IdUtilisateurs')
#     connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
#     cursor = connection.cursor()
#     cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))
#     utilisateurs = cursor.fetchone()
    
#     # Récupérer les données des Stocks depuis la base de données
#     cursor.execute("SELECT * FROM Fournisseurs")
#     Fournisseurs = cursor.fetchall()
#     pdf_content = generate_pdf(Fournisseurs,['ID', 'NomEntreprise', 'Nom_Contact', 'Adresse', 'Téléphone', 'Email', 'Catégories_Produit'])
#     return send_pdf(pdf_content, "fournisseurs.pdf")



@app.route("/exportpdf/fournisseurs")
def export_fournisseurs_pdf():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    # Récupérer les données de l'utilisateur actuel depuis la base de données
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateur = cursor.fetchone()  
    
    # Récupérer les données des fournisseurs depuis la base de données
    cursor.execute("SELECT * FROM Fournisseurs")
    fournisseurs = cursor.fetchall()  
    
    pdf_content = generate_pdf(fournisseurs, ['ID', 'NomEntreprise', 'Nom_Contact', 'Adresse', 'Téléphone', 'Email', 'Catégories_Produit'])
    return send_pdf(pdf_content, "fournisseurs.pdf")



# Définir d'autres routes similaires pour les autres tables

def generate_pdf(data, headers):
    doc = SimpleDocTemplate("temp.pdf", pagesize=letter)
    table_data = [headers]
    for row in data:
        table_data.append([getattr(row, header.lower().replace(' ', '_')) for header in headers])
    table = Table(table_data)
    doc.build([table])
    with open("temp.pdf", 'rb') as f:
        pdf_content = f.read()
    return pdf_content

def send_pdf(pdf_content, filename):
    response = make_response(pdf_content)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    return response
  
  
# def generate_pdf(data, headers):
#     doc = SimpleDocTemplate("temp.pdf", pagesize=letter)
#     table_data = [headers]
#     for row in data:
#         table_row = []
#         for header in headers:
#             # Convertir les espaces dans le header en underscores
#             attribute_name = header.lower().replace(' ', '_')
#             # Utiliser get() pour récupérer la valeur de l'attribut, avec une valeur par défaut si l'attribut n'existe pas
#             cell_value = getattr(row, attribute_name, '')
#             table_row.append(cell_value)
#         table_data.append(table_row)
#     table = Table(table_data)
#     doc.build([table])
#     with open("temp.pdf", 'rb') as f:
#         pdf_content = f.read()
#     return pdf_content

  
  
  

# **************** export_excel()*****************

@app.route("/exportexcel/produits")
def export_produits_excel():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateurs = cursor.fetchone()

    cursor.execute("SELECT * FROM Produits")
    produits = cursor.fetchall()

    df = pd.DataFrame(produits)
    return send_excel(df, "produits.xlsx", utilisateurs=utilisateurs)

@app.route("/exportexcel/utilisateurs")
def export_utilisateurs_excel():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))
    utilisateurs = cursor.fetchone()
    
    # Récupérer les données des utilisateurs depuis la base de données
    
    cursor.execute("SELECT * FROM Utilisateurs")
    utilisateurs = cursor.fetchall()

    df = pd.DataFrame(utilisateurs)
    return send_excel(df, "utilisateurs.xlsx")

@app.route("/exportexcel/stocks")
def export_stocks_excel():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))
    utilisateurs = cursor.fetchone()
    
    # Récupérer les données des Stocks depuis la base de données
    
    cursor.execute("SELECT * FROM Stocks")
    Stocks = cursor.fetchall()
    
    df = pd.DataFrame(Stocks)
    return send_excel(df, "stocks.xlsx",utilisateurs=utilisateurs)



@app.route("/exportexcel/clients")
def export_clients_excel():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))
    utilisateurs = cursor.fetchone()
    
    # Récupérer les données des Clients depuis la base de données
    cursor.execute("SELECT * FROM clients")
    clients = cursor.fetchall()
    
    df = pd.DataFrame(clients)
    return send_excel(df, "clients.xlsx",utilisateurs=utilisateurs)

@app.route("/exportexcel/vente")
def export_vente_excel():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))
    utilisateurs = cursor.fetchone()
    
    # Récupérer les données des Vente depuis la base de données
    cursor.execute("SELECT * FROM Vente")
    Vente = cursor.fetchall()
    
    df = pd.DataFrame(Vente)
    return send_excel(df, "Vente.xlsx",utilisateurs=utilisateurs)

@app.route("/exportexcel/fournisseurs")
def export_fournisseurs_excel():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))
    utilisateurs = cursor.fetchone()
    
    # Récupérer les données des Fournisseurs depuis la base de données
    
    cursor.execute("SELECT * FROM Fournisseurs")
    Fournisseurs = cursor.fetchall()

    df = pd.DataFrame(Fournisseurs)
    return send_excel(df, "fournisseurs.xlsx",utilisateurs=utilisateurs)

# Définir d'autres routes similaires pour les autres tables

def send_excel(df, filename):
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False)
    writer.save()
    output.seek(0)
    # return send_file(output, attachment_filename=filename, as_attachment=True)
    return send_file(output, attachment_filename=filename, as_attachment=True)





#*********** Importer depuis une liste externe *************

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))

    utilisateurs = cursor.fetchone()
    if request.method == 'POST':
        uploaded_file = request.files['file']
        # Lire le contenu binaire du fichier téléchargé
        file_data = uploaded_file.read()
        # Établir une connexion à la base de données
        connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
        cursor = connection.cursor()
        # Exécuter une requête SQL pour insérer les données du fichier dans la base de données
        cursor.execute("INSERT INTO Files (name, data) VALUES (?, ?)", (uploaded_file.filename, pyodbc.Binary(file_data)))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect(url_for('success'))
    return '''
    <!doctype html>
    <title>Upload new file</title>
    <h1>Upload new file</h1>
    <form method="post" enctype="multipart/form-data">
      <input type="file" name="file">
      <input type="submit" value="Upload">
    </form>
    '''





# *************************************Utilisateurs***********************************************


# ***********************liste_Utilisateurs***********************

# @app.route("/liste", methods=['GET', 'POST'])
# def liste():
  
#      # Vérifier si l'utilisateur est connecté
#     if 'IdUtilisateurs' not in session:
#         return redirect(url_for('login'))
    
#     IdUser = session.get('IdUtilisateurs')
#     connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
#     cursor = connection.cursor()
#     cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
#     utilisateurs = cursor.fetchone()
    
#      # Récupérer les utilisateurs paginés depuis la base de données
#     cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))    
#     images = utilisateurs.Images.split(',') if utilisateurs.Images else []

#       # Pagination
#     # page = request.args.get('page', 1, type=int)
#     # per_page = 5
#     # offset = (page - 1) * per_page
    
    
#     if request.method == "POST":
#         Nom = request.form["Nom"]
#         Prenoms = request.form["Prenoms"]
#         Telephone = request.form["Telephone"]
#         Adresse = request.form["Adresse"]
#         Email = request.form["Email"]
#         Roles = request.form["Roles"]
        
#         cursor.execute("INSERT INTO Utilisateurs (Nom, Prenoms, Telephone, Adresse, Email, Roles, IdUtilisateurs) VALUES (?, ?, ?, ?, ?, ?, ?)",
#                        (Nom, Prenoms, Telephone, Adresse, Email, Roles ))
        
#         connection.commit()

#     connection.close()
#     return render_template('Utilisateurs/liste.html', utilisateurs=utilisateurs, images=images)




# @app.route("/liste", methods=['GET', 'POST'])
# def liste():
#     # Check if the user is authenticated
#     if 'IdUtilisateurs' not in session:
#         return redirect(url_for('login'))
    
#     connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
#     cursor = connection.cursor()
    
#     IdUser = session.get('IdUtilisateurs')
    
#     if request.method == "POST":
#         # Retrieve form data
#         Nom = request.form["Nom"]
#         Prenoms = request.form["Prenoms"]
#         Telephone = request.form["Telephone"]
#         Adresse = request.form["Adresse"]
#         Email = request.form["Email"]
#         Roles = request.form["Roles"]
        
#         # Insert new user into database
#         cursor.execute("INSERT INTO Utilisateurs (Nom, Prenoms, Telephone, Adresse, Email, Roles, IdUtilisateurs) VALUES (?, ?, ?, ?, ?, ?, ?)",
#                        (Nom, Prenoms, Telephone, Adresse, Email, Roles, IdUser))
#         connection.commit()
        
#         # Redirect to avoid form resubmission
#         return redirect(url_for('liste'))

#     # Fetch user details
#     cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
#     utilisateurs = cursor.fetchone()
#     # images = utilisateurs.Images.split(',') if utilisateurs.Images else []
    
#     cursor.execute("SELECT * FROM Utilisateurs")
#     users = cursor.fetchall()
#     images = users.Images.split(',') if users.Images else []
    
#     connection.close()
    
#     return render_template('Utilisateurs/liste.html', utilisateurs=utilisateurs, users=users, images=images)




@app.route("/liste", methods=['GET', 'POST'])
def liste():
    # Check if the user is authenticated
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    IdUser = session.get('IdUtilisateurs')
    
    if request.method == "POST":
        # Retrieve form data
        Nom = request.form["Nom"]
        Prenoms = request.form["Prenoms"]
        Telephone = request.form["Telephone"]
        Adresse = request.form["Adresse"]
        Email = request.form["Email"]
        Roles = request.form["Roles"]
        
        # Insert new user into database
        cursor.execute("INSERT INTO Utilisateurs (Nom, Prenoms, Telephone, Adresse, Email, Roles, IdUtilisateurs) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (Nom, Prenoms, Telephone, Adresse, Email, Roles, IdUser))
        connection.commit()
        
        # Redirect to avoid form resubmission
        return redirect(url_for('liste'))

    # Fetch current user details
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateurs = cursor.fetchone()
    
    # Fetch all users
    cursor.execute("SELECT * FROM Utilisateurs")
    users = cursor.fetchall()
    
    # Extract images for each user
    images = [user.Images.split(',') if user.Images else [] for user in users]
    
    connection.close()
    
    return render_template('Utilisateurs/liste.html', utilisateurs=utilisateurs, users=users, images=images)





# ******************************************* debut-clients***************************************


@app.route("/client", methods=["GET", "POST"])
def client():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    # Récupérer les informations de l'utilisateur
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateurs = cursor.fetchone()
    
    # Récupérer la liste des Clients depuis la base de données
    cursor.execute("SELECT * FROM Clients")
    info_clients = cursor.fetchall()
    print(f"info_clients: {info_clients}")
    # print(info_clients[0][0])
    
    # Fermer la connexion à la base de données
    cursor.close()
    connection.close()

    return render_template('client/client.html', utilisateurs=utilisateurs, clients = info_clients)

    
    


@app.route("/ajoutclient", methods=["GET", "POST"])
def ajoutclient():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()

    try:
        # Récupérer les informations de l'utilisateur
        cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
        utilisateurs = cursor.fetchone()

        if request.method == "POST":
            # Récupérer les données du formulaire
            Nom = request.form["Nom"]
            Prenoms = request.form["Prenoms"]
            Telephone = request.form["Telephone"]
            Email = request.form["Email"]
            Genre = request.form["Genre"]
            Adresse = request.form["Adresse"]
            DatesCreation = request.form["DatesCreation"]
            

            # Insérer les données dans la base de données
            cursor.execute("INSERT INTO Clients (Nom, Prenoms, Telephone, Email,  Genre, Adresse,  DatesCreation) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (Nom, Prenoms, Telephone, Email, Genre, Adresse,  DatesCreation))
            connection.commit()
            return redirect(url_for("ajoutclient"))

    except Exception as e:
        # Gérer l'erreur et afficher un message d'erreur approprié
        flash(f'Une erreur est survenue lors de l\'ajout du client : {str(e)}', 'danger')

    finally:
        # Fermer la connexion à la base de données
        cursor.close()
        connection.close()

    return render_template('client/ajout-client.html', utilisateurs=utilisateurs)


  


@app.route("/modifierclient/<int:IdClients>", methods=["GET", "POST"])
def modifierclient(IdClients):

    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateurs = cursor.fetchone()

    # Récupérer les détails du produit à modifier
    cursor.execute("SELECT * FROM Clients WHERE IdClients = ?", (IdClients,))
    info_clients = cursor.fetchone()
    print(f"info_clients: {info_clients}")


    if request.method == "POST":
        # Récupérer les nouvelles données du formulaire
        Nom = request.form["Nom"]
        Prenoms = request.form["Prenoms"]
        Telephone = request.form["Telephone"]
        Email = request.form["Email"]
        Genre = request.form["Genre"]
        Adresse = request.form["Adresse"]
        DatesCreation = request.form["DatesCreation"]
        
        # print(Nom)
        
        cursor.execute("UPDATE Clients  SET Nom = ?, Prenoms = ? , Telephone = ?, Email = ?, Genre = ?, Adresse = ?, DatesCreation = ? WHERE IdClients = ?",
                       (Nom, Prenoms , Telephone , Email , Genre , Adresse, DatesCreation, IdClients))
        
        connection.commit()
        
        return redirect(url_for("client", IdClients=IdClients))
    
    cursor.close()
    connection.close()
    return render_template('client/modifier-client.html',utilisateurs=utilisateurs,info_clients=info_clients)

    

@app.route("/supprimerclient/<int:IdClients>", methods=["GET", "POST"])
def supprimerclient(IdClients):

    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
   
    # # Récupérer les détails du client à Supprimer
    cursor.execute("SELECT * FROM Clients WHERE IdClients = ?", (IdClients,))

    flash(f'Le client a été supprimé avec succès !', 'success')
    
    # Supprimer le Clients de la table Clients
    cursor.execute("DELETE FROM Clients WHERE IdClients = ?", (IdClients,))
    cursor.commit()
    cursor.close()
    return redirect(url_for('client'))



# *****************************************fin-clients***********************************************




# ******************************************** debut-vente**************************************************

@app.route("/vente", methods=["GET", "POST"])
def vente():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateurs = cursor.fetchone()
    
    ventes = []
    
    try:
        cursor.execute("""
            SELECT Vente.IdVente, Produits.NomProduit, Clients.Nom as NomClients, Clients.Prenoms as PrenomsClients, Utilisateurs.Nom as NomUtilisateurs, Utilisateurs.Prenoms as PrenomsUtilisateurs, Vente.Quantite, Produits.PrixUnitaire, Vente.Montant_Total, Vente.Dates_vente, Vente.Mode_paiement
            FROM Vente
            INNER JOIN Produits ON Vente.IdProduits = Produits.IdProduits
            INNER JOIN Clients ON Vente.IdClients = Clients.IdClients
            INNER JOIN Utilisateurs ON Vente.IdUtilisateurs = Utilisateurs.IdUtilisateurs
        """)
        ventes = cursor.fetchall()
        # print(f"ventes: {ventes}")

    except pyodbc.Error as e:
        flash(f'Une erreur est survenue lors de la récupération des données : {str(e)}', 'danger')
        # return redirect(url_for('vente'))  # Rediriger en cas d'erreur

    finally:
        # Fermer la connexion à la base de données
        cursor.close()
        connection.close()
    
    return render_template('vente/vente.html', ventes=ventes, utilisateurs=utilisateurs)





@app.route("/venteclientexistant", methods=["GET", "POST"])
def venteclientexistant():
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUtilisateurs = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUtilisateurs,))
    utilisateurs = cursor.fetchone()
    


    if request.method == "POST":
        # try:
            NomProduit = request.form.get("NomProduit")  
            Quantite = request.form.get("Quantite")  
            Mode_paiement = request.form.get("Mode_paiement")
            IdClients = request.form.get("IdClients")
            cursor = connection.cursor()
        # Récupération de l'identifiant numérique (IdProduits) du produit sélectionné
            cursor.execute("SELECT PrixUnitaire FROM Produits WHERE IdProduits = ?", (NomProduit,))
            row = cursor.fetchone()
            
            print(row)
            print(NomProduit)
            if row:
                 PrixUnitaire = row[0]
            else:
                flash('Le produit sélectionné n\'a pas d\'identifiant correspondant.', 'danger')
                return redirect(url_for("venteclientexistant"))
            
            Montant_Total = int(Quantite) * PrixUnitaire
            Dates_vente = datetime.now()

            cursor.execute("""
                INSERT INTO Vente (Quantite,PrixUnitaire, Montant_Total, Dates_vente, Mode_paiement, IdProduits, IdClients, IdUtilisateurs) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (Quantite, PrixUnitaire, Montant_Total, Dates_vente, Mode_paiement, NomProduit, IdClients, IdUtilisateurs))
            connection.commit()

            cursor.execute("UPDATE Stocks SET Quantite = Quantite - ? WHERE IdProduits = ?", (Quantite, NomProduit))
            connection.commit()

            return redirect(url_for("vente"))
        # except Exception as e:
        #     flash(f'Une erreur est survenue lors de l\'ajout de la vente : {str(e)}', 'danger')

    cursor.execute("SELECT IdProduits, NomProduit FROM Produits")  
    produits = cursor.fetchall()

    cursor.execute("SELECT IdClients, Nom, Prenoms FROM Clients")
    clients = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("vente/venteclientexistant.html", produits=produits, clients=clients, utilisateurs=utilisateurs)



@app.route("/vente-nv_client", methods=["GET", "POST"])
def ventenvclient():
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUtilisateurs = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUtilisateurs,))
    utilisateurs = cursor.fetchone()

    if request.method == "POST":
        try:
            Nom = request.form.get("Nom")
            Prenoms = request.form.get("Prenoms")
            Telephone = request.form.get("Telephone")
            Email = request.form.get("Email")
            Genre = request.form.get("Genre")
            Adresse = request.form.get("Adresse")
            DatesCreation = request.form.get("DatesCreation")
            Mode_paiement = request.form.get("Mode_paiement")

            cursor.execute("INSERT INTO Clients (Nom, Prenoms, Telephone, Email, Genre, Adresse, DatesCreation) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (Nom, Prenoms, Telephone, Email, Genre, Adresse, DatesCreation))
            connection.commit()

            cursor.execute("SELECT SCOPE_IDENTITY()")
            IdClients = cursor.fetchone()[0]

            NomProduit = request.form.get("NomProduit")
            IdProduits = request.form.get("IdProduits")
            Quantite = request.form.get("Quantite")

            cursor.execute("""
                SELECT Produits.NomProduit, Produits.PrixUnitaire
                FROM Produits
                WHERE Produits.IdProduits = ?
            """, (IdProduits,))
            row = cursor.fetchone()
            if row:
                NomProduit, PrixUnitaire = row
            else:
                flash('Le produit sélectionné n\'a pas de prix unitaire défini.', 'danger')
                return redirect(url_for("ventenvclient"))

            MontantTotal = int(Quantite) * PrixUnitaire

            cursor.execute("INSERT INTO Vente (Quantite, PrixUnitaire, Montant_Total, Dates_vente, Mode_paiement, IdProduits, IdClients, IdUtilisateurs) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                           (Quantite, PrixUnitaire, MontantTotal, datetime.now(), Mode_paiement, IdProduits, IdClients, IdUtilisateurs))
            connection.commit()

            cursor.execute("UPDATE Produits SET Quantite = Quantite - ? WHERE IdProduits = ?", (Quantite, IdProduits))
            connection.commit()

            flash('Nouveau client ajouté et vente enregistrée avec succès!', 'success')
            return redirect(url_for("vente"))

        except Exception as e:
            flash(f'Une erreur est survenue lors de l\'ajout du client et de l\'enregistrement de la vente : {str(e)}', 'danger')

    cursor.execute("SELECT IdProduits, NomProduit FROM Produits")
    produits = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template("vente/vente-nv_client.html", produits=produits, utilisateurs=utilisateurs)







#*******************une route pour gérer la demande AJAX et renvoyer les données des produits***************
 
@app.route('/get_Produits', methods=["GET", "POST"])
def get_Produits():
        # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateurs = cursor.fetchone()
    # Récupérer les données des produits depuis la base de données
    cursor.execute("SELECT IdProduits, NomProduit FROM Produits")
    produits = cursor.fetchall()
    # Convertir les données des produits en une liste de dictionnaires
    list_produits = [{'IdProduits': produit[0], 'NomProduit': produit[1]} for produit in produits]
    return jsonify(list_produits)



@app.route("/modifiervente")
def modifiervente():
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))

    utilisateurs = cursor.fetchone()
    return render_template('vente/modifier-vente.html',utilisateurs=utilisateurs)
# ******************************************fin-vente***************************************





# ********************************** debut-produits ***************************************

@app.route("/produit", methods=["GET", "POST"])
def produit():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateurs = cursor.fetchone()
    
    # Récupérer la liste des produits avec les informations sur les fournisseurs
    # cursor.execute("""
    #     SELECT P.*, F.NomEntreprise 
    #     FROM Produits P 
    #     INNER JOIN Fournisseurs F ON P.IdFournisseurs = F.IdFournisseurs
    # """)
    # produits = cursor.fetchall()
    cursor.execute("""
        SELECT * 
        FROM Produits 
    """)
    produits = cursor.fetchall()
    
    # Fermer la connexion à la base de données
    cursor.close()
    connection.close()
    
    return render_template('produit/produit.html', utilisateurs=utilisateurs, produits=produits)



    
@app.route("/ajoutproduit", methods=["GET", "POST"])
def ajoutproduit():
    utilisateurs = None

    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' in session:
        IdUser = session.get('IdUtilisateurs')
        connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
        utilisateurs = cursor.fetchone()

        # Récupérer tous les noms des fournisseurs
        cursor.execute("SELECT IdFournisseurs, NomEntreprise FROM Fournisseurs")
        fournisseurs = cursor.fetchall()
        
        print(fournisseurs)

    if request.method == "POST":
        try:
            # Récupérer les données du formulaire
            NomProduit = request.form["NomProduit"]
            Descriptions = request.form["Descriptions"]
            Categories = request.form["Categories"]
            DateAjout = request.form["DateAjout"]
            PrixUnitaire = request.form["PrixUnitaire"]
            Quantite = request.form["Quantite"]
            IdFournisseurs = request.form["IdFournisseurs"]  # Récupérer l'ID du fournisseur à partir du formulaire
            Statut = "plein"  # Par défaut pour l'instant

            print(NomProduit, Descriptions, IdFournisseurs)
            
            # Insérer les données dans la table Produits
            cursor.execute("""
                INSERT INTO Produits (NomProduit, Descriptions, Categories, DateAjout, PrixUnitaire, IdFournisseurs)
                OUTPUT INSERTED.IdProduits
                VALUES (?, ?, ?, ?, ?, ?)
            """, (NomProduit, Descriptions, Categories, DateAjout, PrixUnitaire, IdFournisseurs))
            IdProduits = cursor.fetchone()[0]  # Récupérer l'Id du produit ajouté

            # Insérer les données dans la table Stocks
            
            cursor.execute("""
                INSERT INTO Stocks (DateMiseAjout, Quantite, Statut, IdProduits)
                VALUES (?, ?, ?, ?)
            """, (DateAjout, Quantite, Statut, IdProduits))
            
            
            

            connection.commit()  # Valider les changements

            flash('Le stock a été ajouté avec succès !', 'success')
            return redirect(url_for("produit"))
        except Exception as e:
            flash(f'Une erreur est survenue lors de l\'ajout du produit : {str(e)}', 'danger')

    cursor.close()
    connection.close()

    return render_template('produit/ajout_produit.html', utilisateurs=utilisateurs, fournisseurs=fournisseurs)

    


@app.route("/modifierproduit/<int:IdProduits>", methods=["GET", "POST"])
def modifierproduit(IdProduits):
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateurs = cursor.fetchone()

    # Récupérer les détails du produit à modifier
    cursor.execute("SELECT * FROM Produits WHERE IdProduits = ?", (IdProduits,))
    produit = cursor.fetchone()
    print(f"produit: {produit}")

    if request.method == "POST":
        # Récupérer les nouvelles données du formulaire
        NomProduit = request.form["NomProduit"]
        Descriptions = request.form["Descriptions"]
        Categories = request.form["Categories"]
        DateAjout = request.form["DateAjout"]
        PrixUnitaire = request.form["PrixUnitaire"]
        IdFournisseurs = request.form["IdFournisseurs"]
        
        print(NomProduit)
        
        cursor.execute("UPDATE Produits  SET NomProduit = ?, Descriptions = ? , Categories = ?, DateAjout = ?, PrixUnitaire = ?, IdFournisseurs = ? WHERE IdProduits = ?",
                       (NomProduit, Descriptions , Categories , DateAjout , PrixUnitaire , IdFournisseurs, IdProduits))
        
        connection.commit()
        
        return redirect(url_for("produit", IdProduits=IdProduits))
    
    cursor.close()
    connection.close()
    return render_template('produit/modifier-produit.html',IdProduits=IdProduits, utilisateurs=utilisateurs, produit=produit)


    

@app.route('/supprimerproduit/<int:IdProduits>', methods=['GET', 'POST'])
def supprimerproduit(IdProduits):
    IdProduits = int(IdProduits)
    #Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    # IdProduits = int(IdProduits)
   
    # Connexion à la base de données
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
  
    cursor.execute("SELECT * FROM Produits WHERE IdProduits = ?", (IdProduits,))
    # produit = cursor.fetchone()
    flash(f'Le produit a été supprimé avec succès !', 'success')
    
   
    cursor.execute("DELETE FROM Stocks WHERE IdProduits = ?", (IdProduits,))
    
    cursor.execute("DELETE FROM Produits WHERE IdProduits = ?", (IdProduits,))
    cursor.commit()
    cursor.close()
    return redirect(url_for('produit'))

# ****************************************fin-produits************************************






# ***************************** ********debut-stock*******************************************

@app.route("/stock")
def stock():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateurs = cursor.fetchone()

    try:
       cursor = connection.cursor()
       cursor.execute("SELECT *, NomProduit  FROM Stocks s INNER JOIN Produits p ON s.IdProduits = p.IdProduits")
       infos_stock = cursor.fetchall()
    #    print(infos_stock)
       print(f"Infos Stock: {infos_stock}")

    except pyodbc.Error as e:
        flash(f'Une erreur est survenue lors de la récupération des données : {str(e)}', 'danger')
        return redirect(url_for('login'))

    finally:
        # Fermer la connexion à la base de données
        cursor.close()
        connection.close()

    return render_template('stock/stock.html', infos_stock=infos_stock, utilisateurs=utilisateurs )


@app.route("/ajoutstock", methods=["GET", "POST"])
def ajoutstock():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateurs = cursor.fetchone()

    # Récupérer tous les noms de produits
    cursor.execute("SELECT IdProduits,NomProduit FROM Produits")
    produits = cursor.fetchall()

    if request.method == "POST":
        try:
            # Récupérer les données du formulaire
            DateMiseAjout = request.form["DateMiseAjout"]
            NomProduit = request.form["NomProduit"]
            Quantite = request.form["Quantite"]
            Statut = request.form["Statut"]
            

            # Insérer les données dans la base de données
            cursor.execute("INSERT INTO Stocks (DateMiseAjout, Quantite, Statut, IdProduits) VALUES (?, ?, ?, ?)",
                           (DateMiseAjout, Quantite, Statut, NomProduit))
            connection.commit()
            flash('Le stock a été ajouté avec succès !', 'success')

            # Mettre à jour la quantité en stock dans la table Produits
            cursor.execute("UPDATE Produits SET Quantite = Quantite + ? WHERE NomProduit = ?", (Quantite, NomProduit))
            connection.commit()

            # Rediriger vers la page du stock après l'ajout
            return redirect(url_for("stock"))
        except Exception as e:
            # En cas d'erreur, afficher un message d'erreur et imprimer l'exception pour le débogage
            flash(f'Une erreur est survenue lors de l\'ajout du stock : {str(e)}', 'danger')

    # Fermer la connexion à la base de données
    cursor.close()
    connection.close()

    return render_template('stock/ajout-stock.html', utilisateurs=utilisateurs, produits=produits)



@app.route("/modifierstock/<int:id>", methods=["GET", "POST"])
def modifierstock(id):
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateurs = cursor.fetchone()

    # Récupérer les détails du produit à modifier
    cursor.execute("SELECT *, NomProduit  FROM Stocks s INNER JOIN Produits p ON s.IdProduits = p.IdProduits AND s.IdStocks = ?",  (id))
    infos_stock = cursor.fetchone()
    # print(f"Infos Stock: {infos_stock}")
    stock_details = cursor.fetchone()

    if request.method == "POST":
        # Récupérer les nouvelles données du formulaire
        DateMiseAjout = request.form["DateMiseAjout"]
        Quantite = request.form["Quantite"]
        
        NouvelleQuantite = infos_stock[2] + int(Quantite)
        print(NouvelleQuantite)
    
        print(DateMiseAjout, Quantite)
        
        cursor.execute("UPDATE Stocks  SET DateMiseAjout = ?, Quantite = ? WHERE IdStocks = ?", (DateMiseAjout, NouvelleQuantite, id))
        
        # Valider les modifications
        connection.commit()
       
        # Rediriger vers la page du stock après la modification
        return redirect(url_for("stock"))
    
    cursor.close()
    connection.close()
    return render_template('stock/modifier-stock.html', utilisateurs=utilisateurs, infos_stock=infos_stock)


@app.route("/suprimestock/<int:IdProduits>", methods=["GET", "POST"])
def suprimestock(IdProduits):
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    
    utilisateurs = cursor.fetchone()
    cursor.execute('DELETE FROM Stocks WHERE IdProduits = ?', (IdProduits,))
    connection.commit()  
    cursor.close()

    return redirect(url_for("dashbord", utilisateurs=utilisateurs))






# ***********************fin-stock***********************





# ***********************debut-fournisseur***********************

@app.route("/fournisseur")
def fournisseur():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    
    # Récupérer les informations de l'utilisateur
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateurs = cursor.fetchone()
    
    # Récupérer la liste des fournisseurs depuis la base de données
    cursor.execute("SELECT * FROM Fournisseurs")
    fournisseurs = cursor.fetchall()
    
    # Fermer la connexion à la base de données
    cursor.close()
    connection.close()
    
    return render_template('fournisseur/fournisseur.html', utilisateurs=utilisateurs, fournisseurs=fournisseurs)





@app.route("/ajoutfournisseur", methods=["GET", "POST"])
def ajoutfournisseur():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateurs = cursor.fetchone()

    if request.method == "POST":
        try:
            # Récupérer les données du formulaire
            NomEntreprise = request.form["NomEntreprise"]
            Nom_Contact = request.form["Nom_Contact"]
            Adresse = request.form["Adresse"]
            Telephone = request.form["Telephone"]
            Email = request.form["Email"]
            Mode_paiement = request.form["Mode_paiement"]
            
            
            print(f"NomEntreprise: { NomEntreprise}")
            print(f"Nom_Contact: { Nom_Contact}")
            print(f"Adresse: { Adresse}")
            print(f"Telephone: { Telephone}")
            print(f"Email: { Email}")
            print(f"Mode_paiement: { Mode_paiement}")
            
        
            
            # Insérer les données dans la base de données
            cursor.execute("INSERT INTO Fournisseurs (NomEntreprise, Nom_Contact, Adresse, Telephone, Email,  Mode_paiement) VALUES (?, ?, ?, ?, ?, ?)",
                           (NomEntreprise, Nom_Contact, Adresse, Telephone, Email, Mode_paiement))
            connection.commit()
            return redirect(url_for("fournisseur"))
        except Exception as e:
            # Gérer l'erreur et afficher un message d'erreur approprié
            error_message = "Une erreur s'est produite lors de l'ajout du fournisseur : " + str(e)
            return render_template('fournisseur/ajout-fournisseur.html', utilisateurs=utilisateurs, error_message=error_message)
        finally:
            cursor.close()
            connection.close()
    
    cursor.close()
    connection.close()
    return render_template('fournisseur/ajout-fournisseur.html', utilisateurs=utilisateurs)




@app.route("/modifierfournisseur/<int:IdFournisseurs>", methods=["GET", "POST"])
def modifierfournisseur(IdFournisseurs):
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateurs = cursor.fetchone()

    # Récupérer les informations du fournisseur à modifier
    cursor.execute("SELECT * FROM Fournisseurs WHERE IdFournisseurs = ?", (IdFournisseurs,))
    Fournisseur = cursor.fetchone()
    print(f"Fournisseur: {Fournisseur}")

    if request.method == "POST":
        try:
            # Récupérer les données modifiées du formulaire
            NomEntreprise = request.form["NomEntreprise"]
            Nom_Contact = request.form["Nom_Contact"]
            Adresse = request.form["Adresse"]
            Telephone = request.form["Telephone"]
            Email = request.form["Email"]
            Mode_paiement = request.form["Mode_paiement"]
            
            # Mettre à jour les informations du fournisseur dans la base de données
            cursor.execute("UPDATE Fournisseurs SET NomEntreprise=?, Nom_Contact=?, Adresse=?, Telephone=?, Email=?, Mode_paiement=? WHERE IdFournisseurs=?",
                           (NomEntreprise, Nom_Contact, Adresse, Telephone, Email,  Mode_paiement, IdFournisseurs))
            connection.commit()
            
            # Rediriger vers la page des fournisseurs après la modification
            return redirect(url_for("fournisseur"))
        except Exception as e:
            # Gérer l'erreur et afficher un message d'erreur approprié
            error_message = "Une erreur s'est produite lors de la modification du fournisseur : " + str(e)
            return render_template('fournisseur/modifier-fournisseur.html', utilisateurs=utilisateurs, Fournisseur=Fournisseur, error_message=error_message)
        finally:
            cursor.close()
            connection.close()

    cursor.close()
    connection.close()
    
    return render_template('fournisseur/modifier-fournisseur.html', utilisateurs=utilisateurs, Fournisseur=Fournisseur)




@app.route('/supprimerfournisseur/<int:IdFournisseurs>', methods=['GET', 'POST'])
def supprimerfournisseur(IdFournisseurs):
    IdFournisseurs = int(IdFournisseurs)
    #Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    
    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateurs = cursor.fetchone()
   
    # Connexion à la base de données
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
   
    cursor.execute("SELECT * FROM Fournisseurs WHERE IdFournisseurs = ?", (IdFournisseurs,))
    
    flash(f'Le fournisseurs a été supprimé avec succès !', 'success')
    cursor.execute("DELETE FROM Stocks WHERE IdProduits IN (SELECT IdProduits FROM Produits WHERE IdFournisseurs = ?)", (IdFournisseurs,) )


    cursor.execute("DELETE FROM Produits WHERE IdFournisseurs = ?", (IdFournisseurs,) )
    cursor.execute("DELETE FROM Fournisseurs WHERE IdFournisseurs = ?", (IdFournisseurs,))

    cursor.commit()
    cursor.close()
    return redirect(url_for('fournisseur'))



# ***********************fin-fournisseur***********************


# @app.route('/emailing', methods=['POST'])
# def emailing():
#     # Vérifier si l'utilisateur est connecté
#     if 'IdUtilisateurs' not in session:
#         return redirect(url_for('login'))

#     IdUser = session.get('IdUtilisateurs')
#     connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
#     cursor = connection.cursor()
#     cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
#     utilisateurs = cursor.fetchone()
#     # Récupérer le message depuis le formulaire
#     message = request.form['message']

#     # Récupérer les numéros de téléphone depuis la base de données SQLSERVER
#     # Assurez-vous d'avoir une connexion à votre base de données et de récupérer les numéros

#     # Envoyer le message à chaque numéro de téléphone
#     # Utilisez votre service d'envoi de SMS préféré (Twilio, Nexmo, etc.)

#     # Exemple avec Twilio (vous devez installer twilio-python via pip)

#     account_sid = 'VOTRE_ACCOUNT_SID'
#     auth_token = 'VOTRE_AUTH_TOKEN'
#     client = Clients(account_sid, auth_token)

#     # Exemple d'envoi de SMS à un numéro
#     # Remplacez 'from_' par votre numéro Twilio et 'to' par le numéro de téléphone de votre client
#     # client.messages.create(
#     #     body=message,
#     #     from_='VOTRE_NUMERO_TWILIO',
#     #     to='NUMERO_DU_CLIENT'
#     # )

#     return "Messages envoyés avec succès !"





@app.route('/email', methods=['POST'])
def email():
    # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))
    
    
        # Vérifier si l'utilisateur est connecté
    if 'IdUtilisateurs' not in session:
        return redirect(url_for('login'))

    IdUser = session.get('IdUtilisateurs')
    connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser,))
    utilisateurs = cursor.fetchone()
    # Récupérer le message depuis le formulaire
    message = request.form['message']

    # Récupérer les adresses e-mail de tous les utilisateurs depuis la base de données
    cursor.execute("SELECT email FROM Utilisateurs")
    emails = cursor.fetchall()


    # # Configurer les informations de connexion au serveur SMTP
    # smtp_server = 'smtp.example.com'  # Remplacez par l'adresse du serveur SMTP
    # smtp_port = 587  # Port SMTP (peut varier selon le fournisseur de messagerie)
    # smtp_username = 'your_username'  # Nom d'utilisateur pour l'authentification SMTP
    # smtp_password = 'your_password'  # Mot de passe pour l'authentification SMTP

    # # Créer un objet MIMEMultipart pour le message
    # msg = MIMEMultipart()
    # msg['From'] = 'your_email@example.com'  # Adresse e-mail de l'expéditeur
    # msg['Subject'] = 'Subject of the Email'  # Sujet de l'e-mail

    # # Ajouter le corps du message
    # msg.attach(MIMEText(message, 'plain'))

    # # Établir une connexion au serveur SMTP
    # server = smtplib.SMTP(smtp_server, smtp_port)
    # server.starttls()  # Activer le mode TLS (Transport Layer Security)

    # # Se connecter au serveur SMTP avec les informations d'identification
    # server.login(smtp_username, smtp_password)

    # # Envoyer l'e-mail à chaque adresse e-mail récupérée
    # for email in emails:
    #     msg['To'] = email[0]  # Adresse e-mail du destinataire
    #     server.sendmail(msg['From'], msg['To'], msg.as_string())

    # # Fermer la connexion au serveur SMTP
    # server.quit()

    return "Email envoyé à tous les utilisateurs avec succès !"




# *********************** Visualisation IA ***********************



# Fonction de connexion à la base de données SQL Server
# def connect_to_database():
#     conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};'
#                           'SERVER=your_server;'
#                           'DATABASE=your_database;'
#                           'UID=your_username;'
#                           'PWD=your_password')
#     return conn.cursor()

# # Définissez vos routes
# @app.route('/')
# def visuels():
#     IdUser = session.get('IdUtilisateurs')
#     connection = pyodbc.connect(app.config['SQL_SERVER_CONNECTION_STRING'])
#     cursor = connection.cursor()
#     cursor.execute("SELECT * FROM Utilisateurs WHERE IdUtilisateurs = ?", (IdUser))

#     utilisateurs = cursor.fetchone()
#     # Connexion à la base de données
#     cursor = BD_GOUA()

#     # Requête pour obtenir le meilleur produit vendu
#     cursor.execute("SELECT TOP 1 NomProduit, SUM(Quantite) AS total_sold FROM Vente GROUP BY NomProduit ORDER BY total_sold DESC")
#     best_product = cursor.fetchone()

#     # Requête pour obtenir le meilleur employé
#     cursor.execute("SELECT TOP 1 Utilisateurs, SUM(Montant_Total) AS total_sales FROM Vente GROUP BY Utilisateurs ORDER BY total_sales DESC")
#     best_employee = cursor.fetchone()

#     # Requête pour obtenir le nombre total de ventes par mois/année
#     cursor.execute("SELECT YEAR(Dates_vente) AS year, MONTH(Dates_vente) AS month, COUNT(id) AS total_sales FROM Vente GROUP BY YEAR(Dates_vente), MONTH(Dates_vente) ORDER BY year, month")
#     sales_by_date = cursor.fetchall()

#     # Requête pour obtenir le chiffre d'affaires total par mois/année
#     cursor.execute("SELECT YEAR(Dates_vente) AS year, MONTH(Dates_vente) AS month, SUM(Montant_Total) AS chiffre_affaires FROM Vente GROUP BY YEAR(Dates_vente), MONTH(date_vente) ORDER BY year, month")
#     ventes = cursor.fetchall()

#     # Fermeture de la connexion à la base de données
#     cursor.close()

#     return render_template('visuels.html', best_product=best_product, best_employee=best_employee,
#                            sales_by_date=sales_by_date, ventes=ventes , utilisateurs=utilisateurs)
    
    












    # Convertir DateVente en DateField
    # Vente.objects.update(DateVente=Cast('DateVente', output_field=DateField()))

    # Récupérer l'utilisateur connecté
    utilisateur = get_object_or_404(User, id=request.user.id)

    # Utiliser la clé étrangère pour récupérer l'administrateur associé
   # administrateur = get_object_or_404(Adminitrateur, IdUtilisateur=utilisateur)
    # Meilleur produit vendu
    best_product = Vente.objects.values('produit__nom').annotate(total_sold=Sum('quantite')).order_by(
        '-total_sold').first()

    # Meilleur employé
    best_employee = Vente.objects.values('personnel__username').annotate(
        total_sales=Sum('montant_total')).order_by('-total_sales').first()

    # Top 5 des meilleurs clients
    #top_clients = Vente.objects.values('IdClient_nom', 'IdClient_prenoms').annotate(
     #total_purchases=Count('IdClient')).order_by('-total_purchases')[:5]

  

if __name__ == '__main__':
    app.run(debug=True)