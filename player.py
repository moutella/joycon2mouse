import gc
from joycon import JoyCon



global cliente
cliente = None
class Player:
    def __init__(self, number, controller_type, side=None, task=None):
        self.number = number
        self.type = controller_type
        self.side = side
        self.clients = []
        # Explicit garbage collection to prevent reuse issues
        gc.collect()
        self.gamepad = None

    def __str__(self):
        print(f"Joy-Con: {self.number}, type: {self.type}, side: {self.side}, clients: {self.clients}")

    def attach_joycon(self, side):
        self.gamepad = JoyCon(side=side)  # Initialize JoyCon instance
    
    async def disconnect(self):
        for client in self.clients:
            if client.is_connected:
                await client.disconnect()
        self.clients.clear()
        # Explicit garbage collection to prevent reuse issues
        await self.task.cancel()
        gc.collect()