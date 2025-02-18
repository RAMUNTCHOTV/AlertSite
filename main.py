import os
import discord
import requests
from bs4 import BeautifulSoup
import asyncio
from discord import app_commands
from discord.ext import commands
import time
import logging

# Charger les variables d'environnement
TOKEN = os.getenv("TOKEN")  # Le token Discord du bot
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))  # ID du canal où les notifications seront envoyées
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))  # ID du canal pour les logs
URL = "https://store.steampowered.com/sale/steamdeckrefurbished/"  # URL du Steam Deck reconditionné

# Ajouter les intents nécessaires pour lire le contenu des messages et gérer les commandes
intents = discord.Intents.default()
intents.message_content = True  # Autoriser le bot à lire le contenu des messages

# Configurer le bot avec les intents modifiés
bot = commands.Bot(command_prefix="!", intents=intents)

# Variables pour suivre l'uptime
last_update_time = time.time()  # Temps de la dernière mise à jour

# Créer un objet de logger
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)

# Créer un handler qui envoie les logs dans un canal Discord
class DiscordHandler(logging.Handler):
    def __init__(self, channel):
        super().__init__()
        self.channel = channel

    def emit(self, record):
        log_message = self.format(record)
        # Utiliser asyncio.create_task pour attendre la coroutine de façon asynchrone
        asyncio.create_task(self.channel.send(log_message))

# Fonction d'initialisation du logger
async def init_logging():
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if channel is not None:
        handler = DiscordHandler(channel)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
    else:
        print("Le canal de logs spécifié est introuvable.")

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
                logger.info("Aucun stock disponible pour l'instant...")

            # Mettre à jour l'uptime après chaque vérification
            global last_update_time
            last_update_time = time.time()

        except Exception as e:
            logger.error(f"Erreur pendant la vérification du stock : {e}")

        await asyncio.sleep(60)  # Vérifie toutes les 60 secondes

@bot.event
async def on_ready():
    """Synchronise les commandes slash et lance les tâches d'actualisation."""
    print(f"✅ Connecté en tant que {bot.user}")
    
    # Synchroniser les commandes
    try:
        synced = await bot.tree.sync()
        print(f"📌 Commandes synchronisées : {len(synced)}")
    except Exception as e:
        logger.error(f"Erreur de synchronisation des commandes : {e}")

    # Initialiser le système de logs
    await init_logging()

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
    try:
        channel = bot.get_channel(CHANNEL_ID)
        if channel is None:
            await interaction.response.send_message("Erreur : Le canal spécifié n'a pas pu être trouvé.")
            return

        await channel.send(f"🔥 Un Steam Deck reconditionné est DISPONIBLE ! Va vite voir : {URL}")
        await interaction.response.send_message("Test de notification effectué. Vérifie le canal!")

    except Exception as e:
        await interaction.response.send_message(f"Une erreur est survenue : {e}")

@bot.tree.command(name="clear", description="Supprime un certain nombre de messages dans le salon.")
@app_commands.describe(n="Nombre de messages à supprimer.")
async def clear(interaction: discord.Interaction, n: int):
    """Commande pour supprimer un certain nombre de messages dans le salon."""
    if interaction.user.guild_permissions.manage_messages:
        # Vérifier si l'utilisateur a la permission de gérer les messages dans le salon
        deleted = await interaction.channel.purge(limit=n)  # Supprimer les messages
        await interaction.response.send_message(f"Supprimé {len(deleted)} message(s) dans ce salon.", ephemeral=True)
    else:
        await interaction.response.send_message("Tu n'as pas la permission de gérer les messages dans ce salon.", ephemeral=True)

bot.run(TOKEN)
