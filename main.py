import os
import discord
import requests
from bs4 import BeautifulSoup
import asyncio
from discord import app_commands
from discord.ext import commands

# Charger les variables d'environnement
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
URL = "https://store.steampowered.com/sale/steamdeckrefurbished/"

# Configurer les intents et le bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

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

        except Exception as e:
            print(f"Erreur : {e}")

        await asyncio.sleep(60)  # Vérifie toutes les 60 secondes

@bot.event
async def on_ready():
    """Synchronise les commandes slash et lance la vérification automatique."""
    print(f"✅ Connecté en tant que {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"📌 Commandes synchronisées : {len(synced)}")
    except Exception as e:
        print(f"Erreur de synchronisation : {e}")

    bot.loop.create_task(check_stock())

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

bot.run(TOKEN)
