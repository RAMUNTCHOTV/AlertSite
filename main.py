import discord
from discord import app_commands
from discord.ext import commands
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 123456789012345678  # Remplace par l'ID de ton serveur

# Configuration du bot
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"✅ Connecté en tant que {bot.user}")
    await bot.change_presence(activity=discord.Game(name="Tape /stock pour voir le stock"))

# 🔍 Commande pour vérifier le stock avec capture d'écran
@bot.tree.command(name="stock", description="Vérifie la disponibilité des Steam Deck reconditionnés et envoie une capture d'écran.")
async def stock(interaction: discord.Interaction):
    await interaction.response.defer()  # Indique que le bot prend du temps pour répondre

    url = "https://store.steampowered.com/sale/steamdeckrefurbished/"
    
    # Configuration du navigateur headless
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Mode sans interface graphique
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        time.sleep(3)  # Attente pour le chargement de la page
        screenshot_path = "stock_screenshot.png"
        driver.save_screenshot(screenshot_path)  # Capture de la page

        # Vérification du texte "Épuisé" sur la page
        page_source = driver.page_source
        if "Épuisé" in page_source:
            stock_status = "❌ Aucun stock disponible."
        else:
            stock_status = "✅ Un Steam Deck est disponible !"

        driver.quit()  # Fermer le navigateur

        # Envoi du message avec la capture d'écran
        file = discord.File(screenshot_path, filename="stock.png")
        await interaction.followup.send(content=stock_status, file=file)

        # Suppression de la capture après envoi
        os.remove(screenshot_path)

    except Exception as e:
        driver.quit()
        await interaction.followup.send(f"🚨 Erreur lors de la vérification : {e}")

# 🧹 Commande pour nettoyer un salon
@bot.tree.command(name="clear", description="Supprime un certain nombre de messages dans le salon.")
@app_commands.describe(n="Nombre de messages à supprimer.")
async def clear(interaction: discord.Interaction, n: int):
    if interaction.user.guild_permissions.manage_messages:
        deleted = await interaction.channel.purge(limit=n)
        await interaction.response.send_message(f"✅ {len(deleted)} message(s) supprimé(s).", ephemeral=True)
    else:
        await interaction.response.send_message("⛔ Tu n'as pas la permission de gérer les messages.", ephemeral=True)

# 🚀 Lancer le bot
bot.run(TOKEN)
