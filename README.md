# KPI-Engine

The KPI Calculation Engine is a Python library that provides the core logic when it comes to compute requested KPIs from a given storage system.

--- 

## 📁 Repository Contents

The repository contains the following files and directories
```bash
📂 Project Root
├── 📂 src
│   ├── 📂 app
│   │   ├── 📂 kpi_engine
│   │   │   ├── 🔤 grammar.py 
│   │   │   ├── 🤖 kpi_engine.py
│   │   │   ├── 📩 kpi_request.py
│   │   │   ├── 📤 kpi_response.py
│   │   ├── ⛁ db.py
│   │   ├── ⊞ models.py
│   │   ├── 🌐 main.py
│   ├── 📂 tests
│   │   ├── 🧪 test_kpi_engine.py
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
     - **`test_kpi_engine.py`**
         A Python script that contains unit tests for the KPI Engine.
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

---

### 1. Clone the Repository

Clone this repository to your local machine using the following command:

```bash
git clone https://github.com/Kreative-Performative-Individuals/KPI-Engine.git
```

This will create a new directory named `KPI-Engine` in your current working directory.

### 2. Build the Docker Image

Navigate to the project directory:

```bash
cd KPI-Engine
```

Build the Docker image using the following command:

```bash
docker build --tag kpi-engine .
```

### 3. Run the Docker Container

Run the following command to start the KPI Engine Docker container:

```bash
 docker run -d --name KPI-Engine -p 8000:8000 kpi-engine 
```

This command will start a new Docker container named `KPI-Engine` and expose the application on port `8000`.

### 4. Access the API

You can now access the KPI Engine API by visiting `http://localhost:8000` in your web browser or using tools like Postman.

### 5. Stopping the Container

To stop the running container, use the following command:

```bash
docker stop KPI-Engine
```

Check the status of the container using the following command:

```bash
docker ps -a
```

### 6. Removing the Container and the Image

To remove the container, use the following command:

```bash
docker rm KPI-Engine
```

To remove the image, use the following command:

```bash
docker rmi kpi-engine
```

---