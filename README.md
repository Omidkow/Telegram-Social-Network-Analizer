# Telegram Social Network Analyzer (Offline JSON)

An offline Python tool built with `NetworkX` to analyze group interaction dynamics, reply networks, gender distribution, and user influence metrics using Telegram chat history JSON exports.

## Features
- **Offline Parsing:** Reads Telegram Desktop exported `result.json` without needing live API scraping or proxies.
- **Network Metrics:** Computes directed weighted graphs, Mixing Matrices, and Assortativity coefficients.
- **Influence Ranking:** Ranks users based on customized PageRank algorithms.
- **Behavioral Analytics:** Calculates In/Out engagement ratios and cross-gender interaction shares with custom frequency filters.


## 🚀 Getting Started & Usage

### 1. Prerequisites
Make sure Python is installed on your system. Then, install the required dependencies:
```bash
pip install -r requirements.txt
(Or install directly via: pip install networkx)

2. Export Telegram Chat Data
Open Telegram Desktop.

Go to the target group's settings and select Export chat history.

Set the export format to JSON.

Place the exported file (result.json) in the root directory of this project alongside main.py.

3. Configure Identifiers (Optional)
To ensure accurate gender classification and bot filtering, update the male_identifiers and bot_identifiers lists inside main.py with your group members' user IDs:

Python
male_identifiers = [
    "user6395990624",
    # Add other IDs here...
]

bot_identifiers = [
    "user8241939804",
]
4. Run the Script
Execute the script via your terminal or IDE (such as VS Code):

Bash
python main.py
Upon execution, the tool will automatically parse the JSON file, build the network graph (caching it locally for faster subsequent runs), and output:

The conversation flow Mixing Matrix

The gender Assortativity coefficient

User influence rankings via PageRank

Filtered top rankings for Attraction Ratio (In/Out) and Cross-Gender Interaction Share