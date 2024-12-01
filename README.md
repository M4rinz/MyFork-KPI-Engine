# KPI-Engine

[![CI](https://img.shields.io/github/actions/workflow/status/Kreative-Performative-Individuals/KPI-Engine/ci.yml)](https://github.com/Kreative-Performative-Individuals/KPI-Engine/actions)
[![License](https://img.shields.io/github/license/Kreative-Performative-Individuals/KPI-Engine)](https://github.com/Kreative-Performative-Individuals/KPI-Engine/blob/dev/LICENSE)


The KPI Calculation Engine is a Python library that provides the core logic when it comes to compute requested KPIs from a given storage system.

--- 

## 📁 Repository Contents

The repository contains the following files and directories
```
📂 Project Root
├── 📂 src
│   ├── 📂 app
│   │   ├── 📂 kpi_engine
│   │   │   ├── 🔤 grammar.py 
│   │   │   ├── ⚡ dynamic_calc.py
│   │   │   ├── 🤖 kpi_engine.py
│   │   │   ├── ⛔ exceptions.py
│   │   │   ├── 📩 kpi_request.py
│   │   │   └── 📤 kpi_response.py
│   │   ├── ⛁ db.py
│   │   ├── ⊞ models.py
│   │   └── 🌐 main.py
│   ├── 📂 tests
│   │   └── 🧪 test_dynamic_calc.py
├── 🔄 .github
├── 📜 LICENSE
├── 📖 README.md
├── 🐳 Dockerfile
├── 🛠 pyproject.toml
└── 🛠 poetry.lock
```
In order the contents are
- **`src`**
   A directory containing the source code.
   - **`app`**
      A directory containing the api logic.
      - **`kpi_engine`**
         A directory containing the core logic of the KPI Engine.
         - **`grammar.py`**
            A Python module that defines the accepted grammar for KPI calculation.
         - **`dynamic_calc.py`**
            A Python module that contains the logic for dynamic KPI calculation.
         - **`exceptions.py`**
            A Python module that defines custom exceptions for the KPI Engine.
         - **`kpi_engine.py`**
            A Python module that contains the engine itself.
         - **`kpi_request.py`**
            A Python module that defines the structure of the KPI requests.
         - **`kpi_response.py`**
            A Python module that defines the structure of the KPI responses.
      - **`db.py`**
         A Python module that contains the database connection logic.
      - **`models.py`**
         A Python module that defines the database models.
      - **`main.py`**
         A Python module that contains the main entry point of the application.
   - **`tests`**
      A directory containing the unit tests for the KPI Engine.
     - **`test_dynamic_calc.py`**
         A Python script that contains unit tests for the dynamic KPI calculation.
- **`.github`**
   A directory containing the GitHub Actions workflows, including CODEOWNERS.
- **`LICENSE`**
   A standard MIT license file.
- **`README.md`**
   A detailed README file containing information about the project, setup instructions, and other relevant details.
- **`Dockerfile`**
   A Dockerfile that contains that can be executed following the instructions as below.
- **`pyproject.toml`**
   Project configuration file with all libraries and tools.
- **`poetry.lock`**
   Poetry-generated lock file.


---

## 🚀 Getting Started

### Prerequisites

- Docker should be installed on your machine.
- Git should be installed on your machine.
- The [database](https://github.com/Kreative-Performative-Individuals/smart-industrial-database) and [KB](https://github.com/Kreative-Performative-Individuals/KB) containers should be running

---

### Cloning the Repository

Clone this repository to your local machine running

```bash
git clone https://github.com/Kreative-Performative-Individuals/KPI-Engine.git
cd KPI-Engine
```

This will create a new directory named `KPI-Engine` in your current working directory and navigate you into it.

### Docker Instructions

Build and run the container using the following commands

```bash
docker build --tag kpi-engine .
```

```bash
 docker run --rm --name KPI-Engine -p 8008:8008 kpi-engine 
```

This command will start a new Docker container named `KPI-Engine` and expose the application on port `8000`.

You can now access the KPI Engine API by visiting `http://localhost:8000` in your web browser or using tools like Postman.

To stop the running container, run 

```bash
docker stop KPI-Engine
```

Since once stopped, the container is automatically deleted by `--rm`, we can just delete its image

```bash
docker rmi kpi-engine
```



---

