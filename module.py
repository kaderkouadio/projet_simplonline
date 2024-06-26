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
    # produit = cursor.fetchone()
    flash(f'Le fournisseurs a été supprimé avec succès !', 'success')
    cursor.execute("DELETE FROM Stocks WHERE IdProduits IN (SELECT IdProduits FROM Produits WHERE IdFournisseurs = ?)", (IdFournisseurs,) )


    cursor.execute("DELETE FROM Produits WHERE IdFournisseurs = ?", (IdFournisseurs,) )
    cursor.execute("DELETE FROM Fournisseurs WHERE IdFournisseurs = ?", (IdFournisseurs,))

    cursor.commit()
    cursor.close()
    return redirect(url_for('fournisseur'))