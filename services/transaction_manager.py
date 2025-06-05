import discord
import logging
from typing import Optional, Dict
from database.operations import DatabaseManager

logger = logging.getLogger(__name__)

class TransactionView(discord.ui.View):
    """Interactive view for completing transactions between matched users"""
    
    def __init__(self, buyer_id: int, seller_id: int, item_name: str, 
                 buyer_price: float, seller_price: float, db_manager: DatabaseManager):
        super().__init__(timeout=3600)  # 1 hour timeout
        self.buyer_id = buyer_id
        self.seller_id = seller_id
        self.item_name = item_name
        self.buyer_price = buyer_price
        self.seller_price = seller_price
        self.db_manager = db_manager
        
        self.buyer_confirmed = False
        self.seller_confirmed = False
        self.transaction_completed = False
        self.final_price = None
        
    @discord.ui.button(label='Accept Trade', style=discord.ButtonStyle.green, emoji='✅')
    async def accept_trade(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Accept the trade at the agreed price"""
        user_id = interaction.user.id
        
        if user_id not in [self.buyer_id, self.seller_id]:
            await interaction.response.send_message(
                "❌ You are not part of this trade.", ephemeral=True
            )
            return
        
        if self.transaction_completed:
            await interaction.response.send_message(
                "❌ This transaction has already been completed.", ephemeral=True
            )
            return
        
        # Determine agreed price (lower of the two)
        if self.final_price is None:
            self.final_price = min(self.buyer_price, self.seller_price)
        
        if user_id == self.buyer_id:
            self.buyer_confirmed = True
            role = "buyer"
        else:
            self.seller_confirmed = True
            role = "seller"
        
        # Update the embed
        embed = self.create_transaction_embed()
        
        if self.buyer_confirmed and self.seller_confirmed:
            # Both confirmed - complete transaction
            await self.complete_transaction(interaction, embed)
        else:
            await interaction.response.edit_message(
                content=f"✅ {interaction.user.mention} has confirmed the trade at **${self.final_price:.2f}**\n"
                       f"Waiting for the other party to confirm...",
                embed=embed,
                view=self
            )
    
    @discord.ui.button(label='Negotiate Price', style=discord.ButtonStyle.blurple, emoji='💬')
    async def negotiate_price(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Open price negotiation modal"""
        user_id = interaction.user.id
        
        if user_id not in [self.buyer_id, self.seller_id]:
            await interaction.response.send_message(
                "❌ You are not part of this trade.", ephemeral=True
            )
            return
        
        if self.transaction_completed:
            await interaction.response.send_message(
                "❌ This transaction has already been completed.", ephemeral=True
            )
            return
        
        modal = PriceNegotiationModal(self, user_id)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='Cancel Trade', style=discord.ButtonStyle.red, emoji='❌')
    async def cancel_trade(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel the trade"""
        user_id = interaction.user.id
        
        if user_id not in [self.buyer_id, self.seller_id]:
            await interaction.response.send_message(
                "❌ You are not part of this trade.", ephemeral=True
            )
            return
        
        if self.transaction_completed:
            await interaction.response.send_message(
                "❌ This transaction has already been completed.", ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="❌ Trade Cancelled",
            description=f"Trade for **{self.item_name}** has been cancelled by {interaction.user.mention}",
            color=0xff0000
        )
        
        # Disable all buttons
        for button in self.children:
            button.disabled = True
        
        await interaction.response.edit_message(
            content="",
            embed=embed,
            view=self
        )
    
    def create_transaction_embed(self):
        """Create the transaction status embed"""
        embed = discord.Embed(
            title="🤝 Trade in Progress",
            description=f"**Item:** {self.item_name}",
            color=0xffaa00
        )
        
        buyer_status = "✅ Confirmed" if self.buyer_confirmed else "⏳ Pending"
        seller_status = "✅ Confirmed" if self.seller_confirmed else "⏳ Pending"
        
        embed.add_field(
            name="🛒 Buyer",
            value=f"<@{self.buyer_id}>\nOffered: ${self.buyer_price:.2f}\nStatus: {buyer_status}",
            inline=True
        )
        
        embed.add_field(
            name="🏪 Seller",
            value=f"<@{self.seller_id}>\nAsking: ${self.seller_price:.2f}\nStatus: {seller_status}",
            inline=True
        )
        
        if self.final_price is not None:
            embed.add_field(
                name="💰 Agreed Price",
                value=f"${self.final_price:.2f}",
                inline=True
            )
        
        embed.set_footer(text="Use the buttons below to complete, negotiate, or cancel the trade")
        
        return embed
    
    async def complete_transaction(self, interaction: discord.Interaction, embed: discord.Embed):
        """Complete the transaction when both parties confirm"""
        self.transaction_completed = True
        
        # Update embed for completion
        embed.title = "✅ Trade Completed!"
        embed.color = 0x00ff00
        embed.description = f"**{self.item_name}** sold for **${self.final_price:.2f}**"
        
        embed.add_field(
            name="📋 Next Steps",
            value="• Exchange the item in-game\n• Both parties should complete the trade\n• Contact admins if any issues arise",
            inline=False
        )
        
        # Disable all buttons
        for button in self.children:
            button.disabled = True
        
        await interaction.response.edit_message(
            content=f"🎉 Trade completed! <@{self.buyer_id}> <@{self.seller_id}>",
            embed=embed,
            view=self
        )
        
        # Log the completed transaction
        try:
            # You could add a completed_transactions table to track these
            logger.info(f"Transaction completed: {self.buyer_id} -> {self.seller_id}, {self.item_name}, ${self.final_price}")
        except Exception as e:
            logger.error(f"Error logging transaction completion: {e}")

class PriceNegotiationModal(discord.ui.Modal, title='Negotiate Price'):
    """Modal for price negotiation"""
    
    def __init__(self, transaction_view: TransactionView, user_id: int):
        super().__init__()
        self.transaction_view = transaction_view
        self.user_id = user_id
        
        # Determine user's role and suggested price
        if user_id == transaction_view.buyer_id:
            self.role = "buyer"
            suggested = transaction_view.seller_price
        else:
            self.role = "seller"
            suggested = transaction_view.buyer_price
        
        self.price_input = discord.ui.TextInput(
            label='Proposed Price',
            placeholder=f'Enter your proposed price (suggested: ${suggested:.2f})',
            default=str(suggested),
            min_length=1,
            max_length=10
        )
        self.add_item(self.price_input)
        
        self.message_input = discord.ui.TextInput(
            label='Message (Optional)',
            placeholder='Add a message to explain your price...',
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=200
        )
        self.add_item(self.message_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            proposed_price = float(self.price_input.value.replace('$', '').replace(',', ''))
            
            if proposed_price <= 0:
                await interaction.response.send_message(
                    "❌ Price must be greater than 0.", ephemeral=True
                )
                return
            
            # Update the final price
            self.transaction_view.final_price = proposed_price
            
            # Reset confirmations since price changed
            self.transaction_view.buyer_confirmed = False
            self.transaction_view.seller_confirmed = False
            
            # Create updated embed
            embed = self.transaction_view.create_transaction_embed()
            
            message_text = f"💬 <@{self.user_id}> proposed a new price: **${proposed_price:.2f}**"
            if self.message_input.value:
                message_text += f"\nMessage: *{self.message_input.value}*"
            
            await interaction.response.edit_message(
                content=message_text,
                embed=embed,
                view=self.transaction_view
            )
            
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid price format. Please enter a valid number.", ephemeral=True
            )

class TransactionManager:
    """Manages interactive transactions between users"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def create_interactive_transaction(self, thread, buyer_id: int, seller_id: int, 
                                           item_name: str, buyer_price: float, seller_price: float):
        """Create an interactive transaction in the match thread"""
        try:
            view = TransactionView(buyer_id, seller_id, item_name, buyer_price, seller_price, self.db_manager)
            embed = view.create_transaction_embed()
            
            await thread.send(
                content=f"🎯 **Trade Match Found!**\n<@{buyer_id}> <@{seller_id}>",
                embed=embed,
                view=view
            )
            
            logger.info(f"Created interactive transaction for {buyer_id} and {seller_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating interactive transaction: {e}")
            return False