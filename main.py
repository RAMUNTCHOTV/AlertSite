import os
import discord
import requests
from bs4 import BeautifulSoup
import asyncio

# Charger les variables d'environnement
TOKEN = os.getenv("TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
URL = "https://store.steampowered.com/sale/steamdeckrefurbished/"

# Configurer le bot
intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def check_stock():
    """Vérifie la disponibilité des Steam Deck reconditionnés."""
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    while not client.is_closed():
        try:
            response = requests.get(URL, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.text, "html.parser")

            # Trouver tous les boutons sur la page
            buttons = soup.find_all("div", class_="btn_add_to_cart")

            # Vérifier si au moins un bouton n'a pas "Épuisé"
            in_stock = any("Épuisé" not in btn.text for btn in buttons)

            if in_stock:
                await channel.send(f"🔥 Un Steam Deck reconditionné est DISPONIBLE ! Va vite voir : {URL}")
            else:
                print("Aucun stock disponible pour l'instant...")

        except Exception as e:
            print(f"Erreur : {e}")

        await asyncio.sleep(60)  # Vérifie toutes les 60 secondes

@client.event
async def on_ready():
    print(f"✅ Connecté en tant que {client.user}")
    client.loop.create_task(check_stock())

client.run(TOKEN)
