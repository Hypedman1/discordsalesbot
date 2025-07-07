from web3 import Web3
import json
import discord
import asyncio
from collections import deque
import os
import threading
from flask import Flask

app = Flask(__name__)
@app.route('/')
def index():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask).start()

token = os.getenv("DISCORD_BOT_TOKEN")
channel_id = os.getenv("CHANNEL_ID")
intents = discord.Intents.default()
client = discord.Client(intents=intents)

async def send_msg(txt, imgurl):
    await client.wait_until_ready()  
    channel = client.get_channel(channel_id)
    if channel:
        embed = discord.Embed(
            title="HYPEMAN #" + str(txt[0]) + " was bought for " + str(txt[1]) + " $HYPE",
            description=txt[2],
            color=0x00ff00
        )
        embed.set_image(url=imgurl)
        await channel.send(embed=embed)

RPC_URL = "https://rpc.hyperliquid.xyz/evm"
w3 = Web3(Web3.HTTPProvider(RPC_URL))
with open("abi.json") as f:
    abi = json.load(f)

contract_address = w3.to_checksum_address("0x7be8f48894d9ec0528ca70d9151cf2831c377be0")
contract = w3.eth.contract(address=contract_address, abi=abi)
item_sold_event = contract.events.ItemSold
bid_accepted_event = contract.events.BidAccepted
target_nft_address = "0x03a64a8f28d73d47682b69b9ea69635aa9886956"


async def check_sales():
    latest_checked = w3.eth.block_number
    posts = deque()
    while True:
        try:
            current_block = w3.eth.block_number
            print(current_block)
            if current_block > latest_checked:
                for block_num in range(latest_checked + 1, current_block + 1):

                    item_logs = item_sold_event.get_logs(from_block=block_num, to_block=block_num)
                    for ev in item_logs:
                        args = ev["args"]
                        if args["nftAddress"].lower() != target_nft_address:
                            continue
                        tx = "https://purrsec.com/tx/" + ev['transactionHash'].hex()
                        tokenid = int(args['tokenId']) + 1
                        buyer = args['buyer']
                        buyer = buyer[:6] + "..." + buyer[-4:]
                        seller = args['seller']
                        seller = seller[:6] + "..." + seller[-4:]
                        price = w3.from_wei(args['pricePerItem'], 'ether')
                        sale_info = (
                            f"Buyer: {buyer}\n"
                            f"Seller: {seller}\n"
                            f"Tx: {tx}\n\n"
                            f"https://drip.trade/collections/hypeman"
                        )
                        if tokenid < 100:
                            t = "00" + str(tokenid)
                        elif 100 <= tokenid < 1000:
                            t = "0" + str(tokenid)
                        else:
                            t = str(tokenid)
                        url = "https://s2x436rizqikgxbauhaxlpg3yszvowsnuug4rarkre7ajba5t4za.arweave.net/lq_N-ijMEKNcIKHBdbzbxLNXWk2lDciCKok-BIQdnzI/" + t + ".jpg"
                        posts.append([[tokenid, price, sale_info], url])

                    bid_logs = bid_accepted_event.get_logs(from_block=block_num, to_block=block_num)
                    for ev in bid_logs:
                        args = ev["args"]
                        if args["nftAddress"].lower() != target_nft_address:
                            continue
                        tx = "https://purrsec.com/tx/" + ev['transactionHash'].hex()
                        tokenid = int(args['tokenId']) + 1
                        buyer = args['bidder']
                        buyer = buyer[:6] + "..." + buyer[-4:]
                        seller = args['seller']
                        seller = seller[:6] + "..." + seller[-4:]
                        price = w3.from_wei(args['pricePerItem'], 'ether')
                        sale_info = (
                            f"Buyer: {buyer}\n"
                            f"Seller: {seller}\n"
                            f"Tx: {tx}\n\n"
                            f"https://drip.trade/collections/hypeman"
                        )
                        if tokenid < 100:
                            t = "00" + str(tokenid)
                        elif 100 <= tokenid < 1000:
                            t = "0" + str(tokenid)
                        else:
                            t = str(tokenid)
                        url = "https://s2x436rizqikgxbauhaxlpg3yszvowsnuug4rarkre7ajba5t4za.arweave.net/lq_N-ijMEKNcIKHBdbzbxLNXWk2lDciCKok-BIQdnzI/" + t + ".jpg"
                        posts.append([[tokenid, price, sale_info], url])
                latest_checked = current_block
            if posts:
                t1, t2 = posts.popleft()
                await send_msg(t1, t2)
            await asyncio.sleep(3)

        except Exception as e:
            print("⚠️ Error:", e)
            await asyncio.sleep(10)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(check_sales())

client.run(token)
