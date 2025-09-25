import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Configuraciones del chatbot
DEFAULT_CONFIG_FILE = "servers.yaml"
DEFAULT_LOG_FILE = "mcp_interactions.log"

# Configuraciones de Anthropic
DEFAULT_MODEL = "claude-3-5-haiku-20241022"
MAX_TOKENS = 250
MAX_CONVERSATION_HISTORY = 8

# Timeouts 
TOOL_CALL_TIMEOUT = 30
SERVER_RESPONSE_TIMEOUT = 10
HTTP_REQUEST_TIMEOUT = 30

# Configuraciones de logging
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = "INFO"

# Límites de resultados
MAX_RESULT_LENGTH = 400  # Para truncar resultados largos en logs
MAX_LOG_ENTRIES = 100    # Máximo número de entradas en el log