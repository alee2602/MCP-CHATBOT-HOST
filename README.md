# **MCP-CHATBOT-HOST**

This project implements a customizable chatbot that integrates with MCP (Model Context Protocol) servers to extend its functionality. The chatbot is designed to interact not only with users but also with multiple local and remote MCP servers, enabling features such as music playlist generation, file system interaction, Git integration, and more.

The implementation is based on Python 3, with support for FastMCP, HTTP, and stdio transports. The project demonstrates how MCP servers can be orchestrated within a single chatbot environment, providing flexible and modular tools for different scenarios.

## **Project Structure**

```bash
MCP-CHATBOT-HOST
│   .env.example
│   .gitignore
│   conversation_history.json    
│   demo.txt
│   main.py
│   mcp_interactions.log
│   README.md
│   render.yaml
│   requirements.txt
│   servers.yaml
│
├───anthropic
│       client.py
│
├───clients
│   │   base.py
│   │   fastmcp.py
│   │   http.py
│   │   stdio.py
│
├───color-mcp
│       color_server.py
│       mcp_proxy.py
│       test_server.py
│
├───configs
│       color_tools.py
│       eclipse_tools.py
│       filesystem_tools.py
│       git_tools.py
│       kitchen_tools.py
│
├───core
│       chatbot.py
│       config.py
│
├───data
│       All_Diets.json
│       ingredientes_unificados.json
│       ingredient_substitutions.json
│       recetas_unificadas.json
│       spotify_songs.csv
│
├───externalservers
│       eclipse_mcp_server.py
│       mcp-server.js
│       utils.js
│
├───mymcpserver
│       engine.py
│       main.py
│       music_tools.py
│
├───utils
│       helpers.py
│       logger.py

```

### Folder description 

- core/ -> Main chatbot logic and configuration.

- clients/ -> Transport clients (FastMCP, HTTP, stdio).

- anthropic/ -> Integration with Anthropic’s client library.

- mymcpserver/ -> Custom Music MCP server, handling playlist generation and music tools.

- color-mcp/ -> Example MCP server for testing with color-based tools.

- configs/ -> Tool definitions for MCP servers (filesystem, Git, kitchen, eclipse, etc.).

- externalservers/ -> External MCP servers (e.g., Eclipse, Node.js servers).

- data/ -> Datasets for recipes, ingredients, diets, and Spotify songs.

- utils/ -> Helper functions and logging utilities.

## **Requirements**

- **Python**: 3.10 or higher
- **Dependencies**: Listed in `requirements.txt`

##  **Installation**

### 1. Clone Repository
```bash
git clone https://github.com/alee2602/MCP-CHATBOT-HOST
```
### 2. Environment Setup

```bash
# Using Anaconda (recommended)
conda create -n mcp-playlist python=3.11
conda activate mcp-playlist

# Or using venv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

## **Run the chatbot**

```bash
python main.py
```

## **Configuration**

### 1. Copy the environment file:
```bash
cp .env.example .env
```
Fill in the required variables (API keys, tokens, etc.).

### 2. servers.yaml – Defines which MCP servers are available to the chatbot.

### 3. render.yaml – Configuration for deployment or runtime environment.

## **Implemented MCP Servers**

This project integrates several MCP servers, both custom-built and external, to showcase how the chatbot can dynamically extend its functionality. Each server provides a specific set of tools that the chatbot can call during a conversation.

### **Music MCP Server (mymcpserver/)**

The Music MCP server is the main custom server developed for this project. It is built using FastMCP, running in standard stdio mode. The server exposes tools to generate music playlists based on different parameters such as:

- Mood (happy, sad, energetic, calm, party, chill).

- Genre (e.g., pop, rock, EDM, rap, Latin).

- Popularity filter (0–100).

- Playlist size (default: 10 songs).

The playlists are generated using the dataset spotify_songs.csv, which contains audio features and metadata from a wide range of tracks.

Internally, the logic is handled by:

- engine.py: core playlist engine.

- music_tools.py: MCP tools for playlist creation and filtering.

- main.py: entry point of the Music MCP server.

This server was designed to demonstrate how a chatbot can provide personalized recommendations by combining natural language queries with structured dataset filtering.

### **Remote MCP Server**

The Remote MCP server was implemented to simulate how the chatbot can communicate with services running on a different host. Instead of interacting only with local servers, the chatbot can:

- Connect through a custom proxy that forwards requests from the chatbot to the remote server.

- Handle responses and errors transparently, so the end user only experiences the result of the operation.

### **Color MCP Server (color-mcp/)**

As an additional proof-of-concept, a Color MCP server was developed.

- Provides simple color-related tools such as returning RGB/hex values or generating color palettes.

- Includes a proxy component (mcp_proxy.py) to test how the server behaves when accessed indirectly.

- Useful for validating the chatbot’s ability to call lightweight servers without requiring complex datasets.

### **External Servers (externalservers/ and configs/)**

Several experimental or third-party MCP servers were also integrated to expand the chatbot’s capabilities:

- Eclipse MCP Server: an example of connecting to development tools.

You can check the following server here:
[**Eclipse MCP Server**](https://github.com/BiancaCalderon/REDES_PRY1/blob/main/chatbot/src/eclipse_mcp_server.py)

- Filesystem MCP Server: allows the chatbot to create, read, or manipulate files.

- Git MCP Server: supports repository initialization, commits, and file management.

- Kitchen MCP Server: built to test recipe and ingredient-based queries (connected with the JSON datasets in data/).

You can check the following server here:
[**Kitchen MCP Server**](https://github.com/paulabaal12/kitchen-mcp)

Each of these servers demonstrates how MCP can modularize functionality, instead of hardcoding everything into the chatbot, features are exposed as independent services.

## **Examples**

Example queries supported by the chatbot:

1. “Create a chill playlist with 10 songs.”

2. “Find songs similar to Bohemian Rhapsody.”

3. “Analyze the audio features of a song.”

4. “Initialize a Git repository and add a README file.”