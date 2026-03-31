# Network Automation Forum - Autocon4 - RAG And MCP Session

Repository for NAF AC4 in Austin, Texas - RAG Session  
John Capobianco

---

## Prerequisites

### 1. Git
Ensure you have Git installed. Download it from [git-scm.com](https://git-scm.com/).

### 2. Python 3.10.14 (Required)

> ⚠️ **This project requires Python 3.10.14.** Newer versions (3.11+) are not compatible with all dependencies, particularly `pyats[full]`.

We recommend managing Python versions with **pyenv**.

#### Install pyenv (macOS/Linux)
```bash
# macOS (via Homebrew)
brew install pyenv

# Linux
curl https://pyenv.run | bash
```

#### Add pyenv to your shell (add these lines to ~/.zshrc or ~/.bashrc)
```bash
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

Then reload your shell:
```bash
source ~/.zshrc   # or source ~/.bashrc
```

#### Install and set Python 3.10.14
```bash
pyenv install 3.10.14
```

Navigate to the project directory and pin the version locally:
```bash
cd NAF_AC4
pyenv local 3.10.14
python3 --version   # should output: Python 3.10.14
```

### 3. Windows Users — WSL2 + Ubuntu
- WSL2: [Installation guide](https://docs.microsoft.com/en-us/windows/wsl/install)
- Ubuntu: [Installation guide](https://docs.microsoft.com/en-us/windows/wsl/install)

All commands below should be run inside your Ubuntu WSL2 terminal.

### 4. Visual Studio Code
Download and install from [code.visualstudio.com](https://code.visualstudio.com/).

---

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/automateyournetwork/NAF_AC4
cd NAF_AC4
```

### 2. Confirm Python version
```bash
python3 --version   # must be 3.10.14
```

If it shows a different version, revisit the pyenv setup above.

### 3. Create and activate a virtual environment
```bash
python3 -m venv venv
```

- **macOS/Linux:**
  ```bash
  source venv/bin/activate
  ```
- **Windows (WSL2):**
  ```bash
  source venv/bin/activate
  ```
- **Windows (CMD):**
  ```bash
  venv\Scripts\activate
  ```

### 4. Set your OpenAI API key
```bash
export OPENAI_API_KEY="Key Provided By John"
```

### 5. Install required packages
```bash
pip install -r requirements.txt
```

### 6. Open in VS Code
```bash
code .
```

---

## Cisco DevNet Always-On Catalyst 9k

Get credentials for the Always-On Cisco 9k sandbox:  
https://devnetsandbox.cisco.com/DevNet/catalog/Cat9k-Always-On_cat9k-always-on

Update your `testbed.yaml` files with the correct credentials and URL before running any pyATS-dependent labs.

---
## TOON Requirements

Install npm install -g @toon-format/cli to support TOON


## RAG Lab Instructions

1. Activate your venv and confirm dependencies are installed.
2. Change into the lab directory (e.g. `Lab01`, `Lab02`, `Lab03`).
3. Run the respective Python file:
   ```bash
   python3 lab.py
   ```
4. Some labs are Streamlit apps — run them with:
   ```bash
   streamlit run app.py
   ```

---

## MCP Lab Instructions

1. Change into the lab directory (e.g. `Lab01`, `Lab02`).
2. Start the MCP server:
   ```bash
   python3 server.py
   ```
3. Stop the server (`Ctrl+C`), then run the client:
   ```bash
   python3 client.py
   ```

---

## Testbed Configuration

Update your `testbed.yaml` with the correct credentials, URL, and device details before running MCP labs.

**Test SSH connectivity before running labs:**
```bash
pyats run job <your_job_file> --testbed-file testbed.yaml
```

### Optional: Advanced CML Lab Environment
For a more advanced setup, use the CML reservable lab:
1. Generate crypto keys on each of the 4 devices.
2. Update `testbed.yaml` with the correct IP addresses and credentials.