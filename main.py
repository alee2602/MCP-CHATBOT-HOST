import asyncio
import sys
from pathlib import Path

# Agregar el directorio padre al path para imports
sys.path.append(str(Path(__file__).parent.parent))

from core.chatbot import ModularMCPChatbot

async def main():
    """Función principal"""
    try:
        chatbot = ModularMCPChatbot()
        await chatbot.chat()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())