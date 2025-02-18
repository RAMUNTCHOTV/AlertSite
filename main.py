import os
import discord
import requests
from bs4 import BeautifulSoup
import asyncio
from discord import app_commands
from discord.ext import commands
import time

# Charger les variables d'environnement
TOKEN = os.getenv("TOKEN")  # Le token Discord du bot
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # ID du canal où les notifications seront envoyées
URL = "https://store.steampowered.com/sale/steamdeckrefurbished/"  # URL du Steam Deck reconditionné

# Ajouter les intents nécessaires pour lire le contenu des messages et gérer les commandes
intents = discord.Intents.default()
intents.message_content = True  # Autoriser le bot à lire le contenu des messages

# Configurer le bot avec les intents modifiés
bot = commands.Bot(command_prefix="!", intents=intents)

# Variables pour suivre l'uptime
last_update_time = time.time()  # Temps de la dernière mise à jour

async def update_status():
    """Met à jour le statut du bot toutes les 60 secondes."""
    await bot.wait_until_ready()
    while not bot.is_closed():
        # Calcule le temps écoulé depuis la dernière vérification
        elapsed_time = int(time.time() - last_update_time)
        minutes_elapsed = elapsed_time // 60

        # Met à jour le statut du bot pour informer les utilisateurs
        await bot.change_presence(activity=discord.Game(f"Vérifie /stock | Uptime: {minutes_elapsed}min"))
        
        await asyncio.sleep(60)  # Répète toutes les 60 secondes

async def check_stock():
    """Vérifie la disponibilité des Steam Deck reconditionnés."""
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)

    while not bot.is_closed():
        try:
            response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.text, "html.parser")

            # Trouver les boutons d'achat
            buttons = soup.find_all("div", class_="btn_add_to_cart")

            # Vérifier si au moins un Steam Deck est dispo
            in_stock = any("Épuisé" not in btn.text for btn in buttons)

            if in_stock:
                await channel.send(f"🔥 Un Steam Deck reconditionné est DISPONIBLE ! Va vite voir : {URL}")
            else:
                print("Aucun stock disponible pour l'instant...")

            # Mettre à jour l'uptime après chaque vérification
            global last_update_time
            last_update_time = time.time()

        except Exception as e:
            print(f"Erreur : {e}")

        await asyncio.sleep(60)  # Vérifie toutes les 60 secondes

@bot.event
async def on_ready():
    """Synchronise les commandes slash et lance les tâches d'actualisation."""
    print(f"✅ Connecté en tant que {bot.user}")
    
    try:
        synced = await bot.tree.sync()
        print(f"📌 Commandes synchronisées : {len(synced)}")
    except Exception as e:
        print(f"Erreur de synchronisation : {e}")

    # Démarrer les tâches d'actualisation
    bot.loop.create_task(check_stock())
    bot.loop.create_task(update_status())  # Tâche pour mettre à jour le statut

@bot.tree.command(name="stock", description="Vérifie si un Steam Deck reconditionné est disponible.")
async def stock(interaction: discord.Interaction):
    """Commande /stock pour vérifier la disponibilité manuellement."""
    response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, "html.parser")
    buttons = soup.find_all("div", class_="btn_add_to_cart")

    in_stock = any("Épuisé" not in btn.text for btn in buttons)

    if in_stock:
        await interaction.response.send_message(f"🔥 Un Steam Deck reconditionné est DISPONIBLE ! Va vite voir : {URL}")
    else:
        await interaction.response.send_message("❌ Aucun Steam Deck reconditionné n'est dispo pour le moment.")

@bot.tree.command(name="test_notify", description="Test de la notification de disponibilité d'un Steam Deck.")
async def test_notify(interaction: discord.Interaction):
    """Commande /test_notify pour simuler la notification d'un Steam Deck disponible."""
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send(f"🔥 Un Steam Deck reconditionné est DISPONIBLE ! Va vite voir : {URL}")
    await interaction.response.send_message("Test de notification effectué. Vérifie le canal!")

bot.run(TOKEN)
