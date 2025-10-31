#======================================================================================#
#     Importation des Libraires                                                        #
#======================================================================================#

from flask import Flask, redirect, render_template, request, jsonify, send_from_directory, send_file, flash, url_for
import requests
from playhouse.sqlite_ext import JSONField
from datetime import date
from decimal import Decimal
import os
from peewee import Model, IntegerField, CharField, BooleanField, DecimalField, AutoField, ForeignKeyField, Check, SqliteDatabase
from sqlalchemy import null
import pytest
import json

#import base64

#======================================================================================#
#      ( MVC )        ~ ~ ~ ~ ~  Modèle des données  ~ ~ ~ ~ ~                         #
#======================================================================================#

#======================================================================================#
#     Extraction des données de l'API du prof                                          #
#======================================================================================#

def extraction_des_donnees_JSON():
    # Récupération des données JSON
    url = "http://dimensweb.uqac.ca/~jgnault/shops/products/"
    response = requests.get(url)

    # Récupération des propriétés de la réponse HTTP
    reponse_properties = {
        "status_code": response.status_code,
        "reason": response.reason,
        "url": response.url,
        "headers": dict(response.headers)
    }

    # Affichage de l'objet JSON formaté avec toutes ses propriétés
    print("Propriétés de la réponse HTTP : ")
    print(json.dumps(reponse_properties, indent=4))

    # Conversion de la réponse en objet Python (liste ou dictionnaire)
    data = response.json()
    #print("+------------------------------------------------------------+")
    #print("|       Récupation du JSON  { products = [ {}{}{}{} ] }      |")
    #print("+------------------------------------------------------------+")
    #print(data)
    return data

def affichage_List_des_noms(data):
    # Extraction des noms de produits
    # Supposons que data est une liste de dictionnaires représentant les produits
    # Affichage de la liste des noms de produits
    produits = data["products"]
    names = []
    for produit in produits:
        names.append(produit["name"])
        #print(produit["name"])
    return names

print(" - Extraction des données de l'API dès l'ouverture de l'application")
data = extraction_des_donnees_JSON()
print(" - Affichage de la liste des noms des produits.                    ")
names = affichage_List_des_noms(data)
    
#=========================================================================================#
#     Instanciation de la base de données ( Le Modèle ) [ blue_blerry_ice_cream.sqlite ]  #
#=========================================================================================#
#     Création des classes [ Products, Persons, Cartes_Credits, Shipping_Informations,    #
#                            Product_Orders, Transactions, Orders ]                       #
#=========================================================================================#
# Si ma Base de Données SQLite existe et n'est pas vide, je n'ai plus besoin de la créer.
# Sinon, je la recrée, en y injectant les données de Product de l'API, ainsi que quelques 
# petites données simulées.

if os.path.exists("blue_berry_ice_cream.db"):
    print(" - Plus besoin de charger l'API recupérée car la BD est dejà créee avec les données intégrés.")
else:
    print(" - Instanciation de la base de données [ blue_blerry_ice_cream.db ]")
    db = SqliteDatabase('blue_blerry_ice_cream.db')

    #-----------------------------------------------------------------------------------------
    class Products(Model):
        #id = IntegerField()
        name = CharField(default="Nom inconnu")
        type = CharField(default="Nom inconnu")
        description = CharField(default="Aucune description pour ce produit")
        image = CharField(default="X.jpg")
        height = DecimalField(default=0.0)
        weight = DecimalField(default=0.0)
        price = DecimalField(default=0.0)
        in_stock = BooleanField(default=False)

        class Meta:
            database = db

    #-------------------------------------------------------------------------------------------
    class Persons(Model):
        email = CharField()
        nom_complet = CharField(default="Nom inconnu")
        
        class Meta:
            database = db

    #-----------------------------------------------------------------------------------------
    class Cartes_Credits(Model):
        name = CharField(null=True)
        number = CharField(null=True, constraints=[Check("LENGTH(number) = 19")])  # y compris tous les espaces entres les 16 DIGITS
        #first_digits = CharField(null=True, constraints=[Check("LENGTH(first_digits)=4")])
        #last_digits = CharField(null=True, constraints=[Check("LENGTH(last_digits)=4")])
        cvv = CharField(null=True, constraints=[Check("LENGTH(cvv) = 3")])
        expiration_year = IntegerField(null=True, constraints=[Check('expiration_year >= 2024 AND expiration_year <= 2040')])
        expiration_month = IntegerField(null=True, constraints=[Check('expiration_month > 0 AND expiration_month <= 12')])
        
        class Meta:
            database = db

    #-----------------------------------------------------------------------------------------
    class Shipping_Informations(Model):
        country = CharField()
        address = CharField()
        postal_code = CharField()
        city = CharField()
        province = CharField()
        
        class Meta:
            database = db

    #----------------------------------------------------------------------------------------
    class Produits(Model):
        product_id = IntegerField(null=False)
        quantity = IntegerField(constraints=[Check('quantity > 0')])
        
        class Meta:
            database = db

    #-----------------------------------------------------------------------------------------
    class Transactions(Model):
        #id = AutoField()
        string_id = CharField(max_length=200)
        succes = BooleanField(default=False)
        amount_charged = IntegerField(null=True)
        
        class Meta:
            database = db

    #-----------------------------------------------------------------------------------------
    class Orders(Model):
        #id = AutoField()
        produit = JSONField(null=False)
        email = CharField(null=True)
        credit_card = JSONField(null=True)
        shipping_information = JSONField(null=True)
        total_price = DecimalField(max_digits=10, decimal_places=2, default=0.0)
        total_price_tax = DecimalField(max_digits=10, decimal_places=2, default=0.0)
        paid = BooleanField(default=False)
        transaction = JSONField(null=True)
        shipping_price = DecimalField(max_digits=10, decimal_places=2, default=0.0)
        
        class Meta:
            database = db

#==================================================================================================#
#     Connection du modèle avec la Base de donnée [ blue_blerry_ice_cream.sqlite ]                 #
#==================================================================================================#
    
    print(" - Connection du modèle avec la Base de donnée [ blue_blerry_ice_cream.db ]")
    db.connect()
    db.create_tables([Persons, Cartes_Credits, Shipping_Informations, Products, Transactions, Produits, Orders])

    def inserer_des_donnees_simulees_ds_la_BD():
        print("  Quelques insertions simulees et Mises-à-jour de données ")
        
        # Insertion du product order en liant le produit créé
        produit = Produits.create(product_id=8, quantity=5)
        produit.save()

        # Création initiale de la commande avec le product order
        commande = Orders.create(produit=produit)

        # Ajout ultérieur de l'email
        commande.email = "jgnault@uqac.ca"
        commande.save()

        # Création d'une personne associée à l'email de la commande
        person = Persons.create(
            email=commande.email,
            nom_complet="Jimmy Girald-Nault"
        )
        person.save()

        # Insertion de la carte de crédit (ajout du champ cvv)
        carte = Cartes_Credits.create(
            name = "John Doe",
            number = "4242 4242 4242 4242",
            cvv = "123",
            expiration_year = 2024,
            expiration_month = 9
        )
        commande.credit_card = carte
        commande.save()

        # Insertion des informations d'expédition
        expedition = Shipping_Informations.create(
            country="Canada",
            address="201, rue Président-Kennedy",
            postal_code="G7X 3Y7",
            city="Chicoutimi",
            province="QC"
        )
        commande.shipping_information = expedition
        commande.save()
        return

    def inserer_le_JSON_du_Prof_ds_la_BD():
        
        print("  Insertion du JSON du Prof dans la BD SQLite             ")
        produits = data["products"]
        
        for prod in produits :
            # Insertion d'un produit dans la table Products
            produit = Products.create(
                #id = prod["id"],
                name = prod["name"],
                type = prod["type"],
                description = prod["description"],
                image = prod["image"],
                height = prod["height"],
                weight = prod["weight"],
                price = prod["price"],
                in_stock = prod["in_stock"]
            )
            produit.save()
        return

#======================================================================================================#
#     Insertion de données dans la BD [ blue_blerry_ice_cream.sqlite ]                                 #
#======================================================================================================#

    # Si cette donnée existe dejà dans la BD, alors ça veut dire que le TOUTE LES DONNÉES SIMULÉES SIMULÉES Y SONT
try:
    produit_simule = Produits.get(Produits.product_id==8, Produits.quantity==5)
except:
    print("Le produit SIMULÉ recherché n'existe pas")
    print(" - Quelques insertions simulées et Mises-à-jour de données                ")
    inserer_des_donnees_simulees_ds_la_BD()
else:
    print(" - Le produit SIMULÉ recherché existe déjà")

    #==================================================================================================#

    # Si cette donnée existe dejà dans la BD, alors ça veut dire que toutes les données de l'API Y SONT
try:    
    produit_venant_de_API = Products.get(Products.id==3, Products.height==450)
except:
    print(" - Le produit venant de l'API n'existe pas")
    print(" - Quelques insertions et Mises-à-jour de données depuis l'API            ")
    inserer_le_JSON_du_Prof_ds_la_BD()  
else:
    print(" - Le produit venant de l'API existe déjà")
        
#=============== FIN DE l'INSERTION DES DONNÉES ======================================================#

#=====================================================================================================#
#      ( MVC )        ~ ~ ~ ~ ~  CONTROLEUR ( flask )  ~ ~ ~ ~ ~                                      #
#=====================================================================================================#

products_local = Flask(__name__)   # Remarque : Dans ce travail, on n'a pas bvesoin de Vues

#======================================================================================#
#     Quelques FONCTIONS UTILES                                                        #
#======================================================================================#

# Fonction utile pour sécurité les entrées de l'utilisateur
def sanitize_input(input_str):
    import re
    """
    Nettoie l'input en supprimant certains caractères spéciaux pouvant être utilisés pour une injection SQL.
    Attention : cette approche ne remplace pas l'utilisation de requêtes paramétrées.
    """
    # Assurez-vous de travailler avec une chaîne
    safe_str = str(input_str)
    # Supprimer d'abord les séquences potentiellement dangereuses
    safe_str = safe_str.replace("--", "")
    # Supprimer ensuite les caractères simples, doubles quotes, point-virgule et chevrons
    safe_str = re.sub(r"[\'\";<>]", "", safe_str)
    return safe_str

def verifions_si_produit_existe(id):
    try :
        prod_id = Products.get(Products.id == id)   # En provenance de ls BD SQLite
    except :
        print("Le produit n'existe pas du TOUT :( ")
        return False
    else :
        print("Le produit existe Bel et Bien :) ")
        return True

def verifions_si_produit_en_inventaire(id):
    prod = Products.get(Products.id == id)      # En provenance de ls BD SQLite
    if prod.in_stock:
        return True
    else :
        return False

# Jusqu'à 500 grammes : 5$
# De 500 grammes à 2kg : 10$
# À partir de 2kg (2kg et plus) : 25$
#
# En supposant que les masses stockées sont en Grammes
def calcul_shipping_price(masse_produit, quantity):
    masse_totale = int(masse_produit) * int(quantity)
    if masse_totale <= 500:
        price = 5
    elif masse_totale > 500 and masse_totale < 2000:
        price = 10
    else : 
        price = 25
    return price

def calcul_des_taxes(commande, province):
    prix_sans_taxes = commande.total_price
    
    if province == 'QC':
        taxes = 0.15
    elif province == 'ON':
        taxes = 0.13
    elif province == 'AB':
        taxes = 0.5
    elif province == 'BC':
        taxes = 0.12
    elif province == 'NS':
        taxes = 0.14
    else :
        taxes = 0.0  # pas de taxes si on ne sait pas dans quelle province on est.
    
    prix_avec_taxes = float(prix_sans_taxes) * (1 + taxes)
    
    return prix_avec_taxes

def reponse_http(response):
    json_reponse ={}
    #======================================================================================#
    #     Quelques cas de reponses de succès                                               #
    #======================================================================================#
    
    #======================================================================================#
    #     Quelques cas de reponses d'erreur                                                #
    #======================================================================================#
    
    # Affichage de l'objet JSON formaté
    print(json.dumps(succes_commande_cree_avec_succes, indent=4))

    return json_reponse
    
#======================================================================================#
#     Quelques cas de reponses de succès                                               #
#======================================================================================#
succes_donnees_recuperees = {"succes": {"donnees": {"codehttp": 200, "code": "donnees recupérées","name": "Les données été récupéreés de l'API avec succes"}}}
succes_commande_cree_avec_succes = {"succes": {"commande": {"codehttp": 200, "code": "commande cree","name": "La commande a été créee avec succes"}}}
succes_commande_mis_a_jour_avec_succes = {"succes": {"commande": {"codehttp": 200, "code": "commande mise à jour","name": "La commande a été mise-à-jour avec succes"}}}
succes_produit_demande_existe = {"succes": {"product": {"codehttp": 200,"code": "produit-existe","name": "Le produit demandé existe et n'est pas en rupture de stocks"}}}
succes_carte_valide = {"succes": {"carte_de_credit": {"codehttp": 200,"code": "carte-valide","name": "La carte rentrée est valide"}}}
succes_facturation = {"succes": {"facture_reçue": {"codehttp": 200,"code": "facture_reçue","name": "Les details de la facturew sont retournés"}}}
#======================================================================================#
#     Quelques cas de reponses d'erreur                                                #
#======================================================================================#
erreur_commande_non_existante = {"errors": {"commande": {"codehttp": 404, "code": "commande-inexistante","name": "La commande demandée à cet ID n'existe pas."}}}
erreur_champs_manquant_creation_commande = {"errors": {"product": {"code": "Champs manquant","name": "La création d'une commande nécessite un produit et une quantité"}}}
erreur_commande_non_trouvee = {"errors": {"order": {"code": "not-found", "name": "Order not found"}}}
erreur_produit_pas_en_inventaire = {"errors": {"product": {"codehttp": 422, "code": "out-of-inventory", "name": "Le produit demandé n'est pas en inventaire"}}}
erreur_commande_deja_payee = {"errors": {"order": { "code": "already-paid", "name": "La commande a déjà été payée."}}}
erreur_nom_sur_la_carte_de_credit = {"errors": {"carte_de_credit": {"code": "missing-fields","name": "Il doit y avoir un nom sur la carte de crédit"}}}
erreur_numero_carte_invalide = {"errors": {"carte_de_credit": {"code": "carte-invalide","name": "Le numéro sur la carte de crédit est invalide"}}}

#-----------------------------------------------------------------------------------------------------------------------------------------
# Remarque sur ce qui précède :
# On écrit :    erreur_commande_non_trouvee = {"errors": {"order": {"code": "not-found", "name": "Order not found"}}} 
#                                             quand il s'agit de la déclaration d'une variable objet
#
#    mais       erreur_commande_non_trouvee = jsonify({"errors": {"order": {"code": "not-found", "name": "Order not found"}}}) 
#                                                      quand il s'agit de la sortie d'une ROUTE Flask

#==================================================================================================================#
#     Les différentes ROUTES de notre controleur FLASK                                                             #
#==================================================================================================================#
# https://en.wikipedia.org/wiki/List_of_HTTP_status_codes

#============= 1rst principale Page for the application
@products_local.route("/", methods=["GET"])
def index():
    data = extraction_des_donnees_JSON()
    code = succes_donnees_recuperees
    return render_template("index_1.html", json_data=data, status_code=code)
    

#============= 2nd principale Page for the application
@products_local.route("/index_1", methods=["GET", "POST"])
def index_1():
    if request.method == 'POST':
        data_str = request.form.get("json_data")
        try:
            data = json.loads(data_str)
        except Exception as e:
            print("Erreur lors de la conversion JSON :", e)
            data = extraction_des_donnees_JSON()  # on retombe sur la fonction d'extraction
    else:
        data = extraction_des_donnees_JSON()
    print("+----------------------+")
    print("|        Index 1       |")
    print("+----------------------+")
    print(data) 
    products = data['products']   
    code = succes_donnees_recuperees
    return render_template("index_1.html", json_data=products, status_code=code)
    

#============= 3e principale Page for the application
@products_local.route("/index_2", methods=["GET", "POST"])
def index_2():
    if request.method == 'POST':
        data_str = request.form.get("json_data")
        try:
            data = json.loads(data_str)
        except Exception as e:
            print("Erreur lors de la conversion JSON :", e)
            data = extraction_des_donnees_JSON()  # on retombe sur la fonction d'extraction
    else:
        data = extraction_des_donnees_JSON()
    print("+----------------------+")
    print("|        Index 2       |")
    print("+----------------------+")
    print(data)    
    #products = data['products']
    code = succes_donnees_recuperees
    return render_template("index_2.html", json_data=data, status_code=code)


#============= 4e principale Page for the application
@products_local.route("/index_3", methods=["GET", "POST"])
def index_3():
    if request.method == 'POST':
        data_str = request.form.get("json_data")
        try:
            data = json.loads(data_str)
        except Exception as e:
            print("Erreur lors de la conversion JSON :", e)
            data = extraction_des_donnees_JSON()  # on retombe sur la fonction d'extraction
    else:
        data = extraction_des_donnees_JSON() 
    print("+----------------------+")
    print("|        Index 3       |")
    print("+----------------------+")
    print(data)   
    #products = data['products']
    code = succes_donnees_recuperees   
    return render_template("index_3.html", json_data=data, status_code=code)
    

#============= Order Page
@products_local.route("/order", methods=["GET", "POST"]) 
def order():
    if request.method == "POST":
        # sanitize_input() permet d'éviter toute intrusion de malveillant en supprimant tous les caractères spéciaux
        id       = sanitize_input(request.form.get("id"))
        quantity = sanitize_input(request.form.get("quantity"))
        
        print("produit_id       = ", id)
        print("produit_quantity = ", quantity)

        # validons l'id et la quantity
        if not id or not quantity: # Ne sera jamais le cas parce que j'ai deja validé cette contrainte dans le formulaire
           status_code = erreur_produit_pas_en_inventaire
           return render_template("index_1.html", json_data=data, status_code=status_code)
        
        # verifions si ce produit existe
        existe = verifions_si_produit_existe(id)

        # SI OUI, verifions s'il y a en stock (in_stock == true )
        if existe :
            present = verifions_si_produit_en_inventaire(id)

            if present :
                status_code = succes_commande_cree_avec_succes

                # Je cree le produit en premier, à l'aide du id récupéré du formulaire.                                                                                                                                                                                              
                produit_quantite = Produits.create(product_id=int(id), quantity=int(quantity))
                
                # Je le cherche dans la BD SQLite à laide de ce même id.
                informations_produit = Products.get(Products.id==id)
                masse_produit = int(informations_produit.weight)
                
                # À ce stade, on peut Très Bien calculer le :
                
                # Total Price : prix du produit X quantité 
                print("quantity qui boguait = ", str(quantity))
                total_price = informations_produit.price * Decimal(int(quantity))
                
                # Shipping Price : depends de la masse unitaire et de la quantity commandée.
                shipping_price = calcul_shipping_price(masse_produit, int(quantity))

                # Création initiale de la commande avec le product order
                commande = Orders.create(produit=produit_quantite, 
                                         total_price=total_price, 
                                         shipping_price=shipping_price)  # !!!!  ON VIENT AINSI DE CRÉER LA COMMAMDE   !!!!!
                commande.save()
                print("La commande qu'on vient de créer à la sortie de la route '/order' est : ", commande)

                status_code = succes_commande_cree_avec_succes
                return render_template("afficher_commande.html", json_data=data, 
                                                                 commande=commande, 
                                                                 product=informations_produit, 
                                                                 produit=produit_quantite, 
                                                                 status_code=status_code)
            else :
                erreur = erreur_produit_pas_en_inventaire
                return render_template("out_of_inventory.html", json_data=data, erreur=erreur)   
        else :
            erreur = erreur_produit_pas_en_inventaire
            return render_template("out_of_inventory.html", json_data=data, erreur=erreur)
    else :    
        return render_template("index_1.html", json_data=data)


#============= Order ( shipping informations ) Page. cette ROUTE a été la plus difficile à implémenter, 
@products_local.route("/order/<int:order_id>/shipping", methods=["GET", "POST", "PUT"])
def update_shipping(order_id):
    commande = Orders.get(Orders.id == order_id)
    if request.method == "POST":
        # On vérifie la méthode simulée
        if request.form.get("_method", "").upper() == "PUT":

            product_id = sanitize_input(request.form.get("produit_id"))
            product_quantity = sanitize_input(request.form.get("produit_quantity"))
            email = sanitize_input(request.form.get("email"))
            
            country = sanitize_input(request.form.get("country"))
            address = sanitize_input(request.form.get("adresse"))
            postal_code = sanitize_input(request.form.get("postale_code"))
            city = sanitize_input(request.form.get("city"))
            province = sanitize_input(request.form.get("province"))
            
            shipping_information = Shipping_Informations.create(     # CECI NE FONCTIONNE PAS, DONC JE ME CREE UN 2e
                country=country,
                address=address,
                postal_code=postal_code,
                city=city,
                province=province
            )
            shipping_information_2 = {
                "country"    :country,
                "address"    :address,
                "postal_code":postal_code,
                "city"       :city,
                "province"   :province
            }

            # Je cree le produit en premier, à l'aide du product_id récupéré du formulaire.   
            p_id  = int(product_id) 
            p_qty = int(product_quantity)                                                                                                                                                                                          
            produit_quantite = Produits.create(product_id=p_id, quantity=p_qty)  # MAIS POURQUOI EST_CE QUE CECI NE FONCTIONNE PAS ??? 
                                                                                 # D'OÙ LA LIGNE SUIVANTE
            produit_data = {
                "product_id": int(product_id),
                "quantity": int(product_quantity)
            }
            commande.email = email
            commande.produit = produit_data
            commande.shipping_information = shipping_information_2
            commande.save()

            total_price_tax = calcul_des_taxes(commande, province)
            commande.total_price_tax = total_price_tax
            commande.save()
            print("La commande qu'on vient de créer à la sortie de la route '/order/order_id/shipping' est : ", commande)

            informations_produit = Products.get(Products.id==product_id)
            return render_template('proceder_au_paiement.html', commande=commande, 
                                                                product=informations_produit, 
                                                                produit=produit_quantite,
                                                                json_data=data, 
                                                                order_id=commande.id)
        # ce truc ne sera jamais utilisé.
    return render_template("afficher_commande.html", commande=commande, 
                                                     product=informations_produit, 
                                                     json_data=data, 
                                                     order_id=commande.id)


@products_local.route("/order/<int:order_id>/credit_card", methods=["GET", "POST", "PUT"])
def update_credit_card(order_id):
    commande = Orders.get(Orders.id == order_id)
    if request.method == "POST":
        if request.form.get("_method", "").upper() == "PUT":

            product_id = sanitize_input(request.form.get("produit_id"))
            product_quantity = sanitize_input(request.form.get("produit_quantity"))
            name = sanitize_input(request.form.get("name"))
            number = sanitize_input(request.form.get("number"))
            cvv = sanitize_input(request.form.get("cvv"))
            expiration_year = sanitize_input(request.form.get("expiration_year"))
            expiration_month = sanitize_input(request.form.get("expiration_month"))
            
            if number != "4242 4242 4242 4242" :
                #erreur_nom = erreur_nom_sur_la_carte_de_credit         pas necessaire 
                status_code = erreur_numero_carte_invalide

                return render_template("carte_invalide.html", commande=commande,
                                                              json_data=data,
                                                              status_code=status_code)
            else:
                credit_card = Cartes_Credits.create(
                    name             = name,
                    number           = number,
                    cvv              = cvv,
                    expiration_year  = int(expiration_year),
                    expiration_month = int(expiration_month)
                )
                credit_card_2 = {
                    "name"             : name,
                    "number"           : number,
                    "cvv"              : cvv,
                    "expiration_year"  : int(expiration_year),
                    "expiration_month" : int(expiration_month)
                }
                commande.credit_card = credit_card_2
                commande.save()

                # print("La commande qu'on vient de créer à la sortie de la route '/order/order_id/credit_card' sera réglée avec la carte de: ", commande.credit_card.name)
                
                status_code = succes_carte_valide
                informations_produit = Products.get(Products.id==product_id)
                
                return render_template("soumettre_pour_API_professeur.html", commande=commande, 
                                                                             product=informations_produit, 
                                                                             json_data=data, 
                                                                             status_code=status_code)
    return render_template("proceder_au_paiement.html", commande=commande, 
                                                        product=informations_produit, 
                                                        json_data=data)


#============= Order Sent ( reception de la reponse de la Transaction ) Page
# Étape décisive
@products_local.route("/order/<int:order_id>/facturation", methods=["GET", "POST", "PUT"]) 
def facturation(order_id):
    commande = Orders.get(Orders.id == order_id)
    paiement = {
        "credit_card": {
            "name":commande.credit_card['name'],
            "number":commande.credit_card['number'],
            "expiration_year":commande.credit_card['expiration_year'],
            "expiration_month":commande.credit_card['expiration_month'],
            "cvv":commande.credit_card['cvv']
        },
        "amount_charged": float(commande.total_price_tax + commande.shipping_price)
    }

    # Effectuer la requête POST vers l'URL
    reponse_paiement = requests.post("https://dimensweb.uqac.ca/~jgnault/shops/pay/", json=paiement)
    commande.paid = True   # Paie passe à TRUE
    status_code = succes_facturation

    # Vérifier que la requête s'est bien passée
    print("Status response du Paiement est :", reponse_paiement.status_code)
    
    # Conversion de la réponse en objet Python (liste ou dictionnaire)
    facture = reponse_paiement.json()
    print("Données reçues du paiment :", facture)

    image_0 = int(commande.produit['product_id']) - 1      # Remarque : lorsque l'id est 7, l'image est 6.jpg
    image = str(image_0)                                                     #            donc image = id-1
    return render_template("facturation.html", facture_data=facture, json_data=data, commande=commande, image=image, status_code=status_code)


#============ Chemin du vers l'API des Products du prof
@products_local.route("/origine_des_donnees")                                          
def formulaire_de_satisfaction():                                       
    url = "https://dimensweb.uqac.ca/%7Ejgnault/shops/products/"
    return redirect(url) 


#=========== Video description de la partie 1
@products_local.route("/apercus_video")                                          
def apercus_video():               
    return render_template("apercus_video.html")


if __name__ == "__main__":
    products_local.run(debug=True)

# RESTfull api  route exemples  https://www.youtube.com/watch?v=Jl9XzSPXSe4
# Site permettant de vérifier si un objet JSON est valide
# https://jsonformatter.org/

#====================================================================================#
#   FIN du Modèle, FIN du programme                                                  #
#====================================================================================#

