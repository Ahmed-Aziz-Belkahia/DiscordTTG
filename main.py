import asyncio
import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
import os
from dotenv import load_dotenv
import requests

# Define the URL
url = "https://tunisiantopgs.com/add-member"

# Load environment variables
load_dotenv()

# Set up the bot and intents
intents = discord.Intents.default()
intents.message_content = True  # Make sure to enable this to access message content
intents.members = True  # Optional, if you want member information
intents.reactions = True  # Make sure to enable reactions

bot = commands.Bot(command_prefix='!', intents=intents)

# Define the channel IDs (replace with actual channel IDs)
CHANNEL_ID = 1169909937703497728
REACTION_CHANNEL_ID = 1298549678610190397

# Global variable to store image URL
image_url = ""
check_reaction_count = 0  # Global variable to store the count of :check: reactions

# Listen for the bot's readiness
@bot.event
async def on_ready():
    global check_reaction_count  # Access the global count variable

    # Get the reaction channel object
    reaction_channel = bot.get_channel(REACTION_CHANNEL_ID)
    
    if not reaction_channel:
        print("Channel not found!")
        return
    
    # Retrieve the last 100 messages in the channel (you can change this number if needed)
    check_reaction_count = 0  # Reset count
    async for message in reaction_channel.history(limit=100):
        for reaction in message.reactions:
            if str(reaction.emoji) == "✅":
                check_reaction_count += reaction.count  # Add the count of ✅ reactions to the global count

    # Print the total number of ✅ reactions in the terminal
    print(f"Total ✅ Reactions: {check_reaction_count}")

# Define the modal for user input
class FormModal(Modal):
    def __init__(self, image_url, original_message):
        super().__init__(title="Form Submission")
        
        # Store the image URL and original message to delete the trigger message later
        self.image_url = image_url
        self.original_message = original_message

        # TextInputs for the form fields
        self.first_name_input = TextInput(
            label="First Name", placeholder="Enter your first name", required=True
        )
        self.last_name_input = TextInput(
            label="Last Name", placeholder="Enter your last name", required=True
        )
        self.email_input = TextInput(
            label="Email", placeholder="Enter your email", required=True
        )
        self.phone_input = TextInput(
            label="Phone Number", placeholder="Enter your phone number", required=True
        )
        self.image_url_input = TextInput(
            label="Image URL", placeholder="Image URL will be pre-filled", default=self.image_url, required=True
        )

        # Add the fields to the modal
        self.add_item(self.first_name_input)
        self.add_item(self.last_name_input)
        self.add_item(self.email_input)
        self.add_item(self.phone_input)
        self.add_item(self.image_url_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Collect the submitted information
        first_name = self.first_name_input.value
        last_name = self.last_name_input.value
        email = self.email_input.value
        phone = self.phone_input.value
        image_url = self.image_url_input.value

        # Create an embed with the collected information
        embed = discord.Embed(title="Form Submission Details", color=discord.Color.green())
        embed.add_field(name="First Name", value=first_name, inline=False)
        embed.add_field(name="Last Name", value=last_name, inline=False)
        embed.add_field(name="Email", value=email, inline=False)
        embed.add_field(name="Phone Number", value=phone, inline=False)

        # Add the image to the embed
        if image_url:
            try:
                # Check if the URL is valid and accessible
                embed.set_image(url=image_url)  # Display the image in the embed
                print(f"Image successfully added: {image_url}")
            except Exception as e:
                print(f"Error embedding image: {e}")
                embed.add_field(name="Image URL", value="Invalid image URL", inline=False)
        else:
            embed.add_field(name="Image URL", value="No image provided", inline=False)

        data = {
            "email": email,  # Replace with the actual email
            "image": image_url      # Replace with the actual author ID
        }


        # Send the POST request
        try:
            response = requests.post(url, data=data)
            # Check if the request was successful
            if response.status_code == 200:
                print("Request was successful.")
                print("Response:", response.json())  # or response.text if not JSON
            else:
                print(f"Request failed with status code {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred: {e}")



        # Send the embed with the submitted information
        await interaction.response.send_message(embed=embed, ephemeral=False)

        # Wait for 60 seconds after the submission and then delete the original message
        await asyncio.sleep(60)  # Wait for 60 seconds
        try:
            await self.original_message.delete()  # Delete the original message with the image
            print("Original message deleted after 60 seconds.")
        except discord.NotFound:
            print("The original message could not be found.")

# List of authorized user IDs
authorized_user_ids = [
    828195881434087444, 
    396411321983172608, 
    1176969858777354311, 
    568786899079004182, 
    1080973621993943050
]

# Listen for messages in the specific channel
@bot.event
async def on_message(message):
    global image_url  # Access the global image_url variable

    # Ignore the bot's own messages
    if message.author == bot.user:
        return

    # Check if the message author is in the list of authorized user IDs
    if message.author.id in authorized_user_ids:
        
        # Make sure the message is from the correct channel
        if message.channel.id == CHANNEL_ID:
            # Check if the message contains exactly one image attachment
            if len(message.attachments) == 1:
                attachment = message.attachments[0]
                # Check if the attachment is an image based on its MIME type
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    image_url = attachment.url  # Save the image URL
                    print(f"Image URL: {image_url}")

                    # Create a button that opens the modal
                    button = Button(label="Fill out the form", style=discord.ButtonStyle.primary)

                    # Define a callback function for the button
                    async def button_callback(interaction: discord.Interaction):
                        # Create and send the modal
                        modal = FormModal(image_url, message)
                        await interaction.response.send_modal(modal)

                    # Add the callback to the button
                    button.callback = button_callback

                    # Create a view to hold the button
                    view = View()
                    view.add_item(button)

                    # Send the message with the button to the channel, visible to everyone
                    sent_message = await message.channel.send("Please fill out the form below:", view=view)

                    # Start the timer to delete the image after 60 seconds if the button isn't pressed
                    await asyncio.sleep(60)  # Wait for 60 seconds
                    await sent_message.delete()  # Delete the message if the button wasn't pressed

                else:
                    print("No valid image attachment detected.")
                    await message.delete()  # Delete message if no valid image is detected
            else:
                print("No attachment found, deleting message.")
                await message.delete()  # Delete message if no attachment is found

    else:
        # Send an ephemeral message to the user indicating they are not authorized
        await message.channel.send(f"{message.author.mention}, you are not authorized to use this command.", delete_after=10)
        await message.delete()
        
    # Make sure the bot doesn't ignore its own messages
    await bot.process_commands(message)

# Listen for reactions in the specific reaction channel
@bot.event
async def on_reaction_add(reaction, user):
    global check_reaction_count  # Access the global count variable

    # Make sure the reaction is in the correct channel
    if reaction.message.channel.id == REACTION_CHANNEL_ID and str(reaction.emoji) == "✅":
        # Increment the count when a ✅ reaction is added
        check_reaction_count += 1
        print(f"✅ Reaction count: {check_reaction_count}")

# Run the bot with the token from the environment variable
bot.run(os.getenv("DISCORD_TOKEN"))
