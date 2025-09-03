# Get the Paper:
See the source paper (Open Access):
[https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10742026/](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10742026/)

Zamora PO, Altay G, Santamaria U, Dwarshuis N, Donthi H, Moon CI, Bakalar D, Zamora M. Drug Responses in Plexiform Neurofibroma Type I (PNF1) Cell Lines Using High-Throughput Data and Combined Effectiveness and Potency. Cancers (Basel). 2023 Dec 12;15(24):5811. doi: 10.3390/cancers15245811. PMID: 38136356; PMCID: PMC10742026.

See the deployed version of this code at: [https://nf.mocomakers.com](https://nf.mocomakers.com)

## See the poster
[https://www.mocomakers.com/wp-content/uploads/2023/06/qHTS-NF1-Drugs-List-PosterV8-Final.pdf](https://www.mocomakers.com/wp-content/uploads/2023/06/qHTS-NF1-Drugs-List-PosterV8-Final.pdf)

# About this project:
This code hosts a web tool (DREA web tool) for exploring NF1 quantitative High Throughput Screening (qHTS) data.

Please visit this tool live here:
[http://nf.mocomakers.com](http://nf.mocomakers.com) - Use the Sign Up form on the page, and if there is an issue please contact matt@mocomakers.com

A sister repo to this project is: [https://github.com/MoCoMakers/hack4nf-2022](https://github.com/MoCoMakers/hack4nf-2022)

# 🚀 **High-Performance Database Setup with MCP Integration**

> **✅ MCP Toolbox Ready**: The project now uses PostgreSQL with MCP (Model Context Protocol) integration for significantly improved performance. See [MIGRATION_STRATEGY.md](MIGRATION_STRATEGY.md) for details.

## 🛠️ **Prerequisites**

### **Required Software**
1. **Cursor IDE** - Download from [cursor.sh](https://cursor.sh)
2. **Docker & Docker Compose** - [Install Docker](https://docs.docker.com/get-docker/)
3. **Git** - [Download Git](https://git-scm.com/downloads)
4. **Python 3.9+** - [Download Python](https://www.python.org/downloads/)

## 🏗️ **Quick Start**

### **1. Clone and Setup**
```bash
git clone https://github.com/MoCoMakers/nf_streamlit.git
cd nf_streamlit
```

### **2. Launch Streamlit Application**
```bash
# Run Streamlit locally
cd app
pip install -r requirements.txt
streamlit run Home.py
```

### **3. Access the Applications**
- **Streamlit App**: http://localhost:8501

### **4. MCP Integration (Optional)**
For MCP (Model Context Protocol) setup and database integration using HTTP mode, see [MCP_INTEGRATION.md](MCP_INTEGRATION.md)

## 📊 **Performance Comparison**

| Metric | File-Based (Old) | Database + MCP (New) | Improvement |
|--------|------------------|---------------------|-------------|
| Initial Load Time | 2+ minutes | <10 seconds | **90%+ faster** |
| Memory Usage | 2-4GB | <500MB | **75%+ reduction** |
| UI Responsiveness | Freezes during load | Always responsive | **Seamless UX** |
| Data Filtering | Slow, reloads entire dataset | Instant, server-side | **Real-time** |

## 🔧 **Advanced Configuration**

### **Database Schema**
The application connects to a PostgreSQL database with the following key tables:

- **`im_dep_raw_secondary_dose_curve`** - Main drug response data
- **`fnl_sprime_pooled_delta_sprime`** - Final delta S' calculations
- **`im_dep_sprime_damaging_mutations`** - Mutation data
- **`im_omics_genes`** - Gene information

For detailed schema information and MCP integration, see **[MCP_INTEGRATION.md](MCP_INTEGRATION.md)**.

## 🐳 **Docker Setup**

For MCP Toolbox setup and management, see the **[MCP Integration Guide](MCP_INTEGRATION.md)** which includes:

- Docker container configuration
- Management scripts for Linux/macOS and Windows
- Troubleshooting and monitoring

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Database Connection Issues**:
   ```bash
   # Test remote database connection
   psql -h your-remote-postgres-host.com -U compbio_dw_readonly -d data_warehouse -c "SELECT 1;"
   
   # Check tools.yaml configuration
   cat tools.yaml
   ```

2. **Streamlit Application Issues**:
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version compatibility (3.9+)
   - Verify database credentials in `tools.yaml`

For MCP-specific troubleshooting, see the **[MCP Integration Guide](MCP_INTEGRATION.md)**.

## 📚 **Legacy Setup (File-based)**

> **Note**: The legacy file-based setup is still available but not recommended due to performance issues. See the original README content below for reference.

### Local Development (Developers Only)
### Quick Start with `devcontainers`
You can setup the project on your browser using your GitHub account by clicking [this Codespaces deeplink](https://codespaces.new/MoCoMakers/nf_streamlit/tree/developer%2Fenvironment).<br/>

Alternatively, install and setup the software listed in the [Tech Stack section](#tech-stack) on your computer. Then take the following steps:

Using a bash terminal, clone the repository:
```bash
git clone https://github.com/MoCoMakers/nf_streamlit.git
```
Go into the cloned folder:
```bash
cd nf_streamlit
```
Open the project with Visual Studio code:
```bash
code .
```
While the project is loading in the editor, watch out for a prompt with a button asking you to "Reopen in Container":

![devcontainer prompt](app/assets/devcontainer_prompt.png)

Click the "Reopen in Container" button and the project would be opened in Devcontainers with the database running in the background.


> #### **Run the project after setup**
> After setting up the project following the instructions above, you can run the project following the following steps:
> - (Optional) Change [the values in the cookie dictionary](https://github.com/MoCoMakers/nf_streamlit/blob/03fcbce740253d72b8d88e1cb6deadec8e6dc5f6/app/.streamlit/secrets.toml.example#L19-L21) of the [`secrets.toml.example`](https://github.com/MoCoMakers/nf_streamlit/blob/03fcbce740253d72b8d88e1cb6deadec8e6dc5f6/app/.streamlit/secrets.toml.example) file.
> - Download the files the project needs (this command has to be run the the `app/` folder):
>> ```bash
>> pip install gdown
>> gdown https://drive.google.com/drive/folders/1C3z88jbjXhffHG1qc6W4ExujADiKUinN -O data --folder
>> ```
> - Make copies of the templates of configuration files ending with the extension `.example` and rename them:
>> ```bash
>> find . -name '*.example' -type f -exec bash -c 'cp "$1"  ${1%.example} ' -- {} \;
>> ```
> - To run the streamlit server, use the following command (preferably in a new terminal that you can open by using the key combination ``CTRL + SHIFT + ` `` in Windows or ``CMD (⌘) + SHIFT + ` `` in MacOS):
>> ```bash
>> streamlit run Home.py --server.fileWatcherType auto --server.headless true
>> ```
>>> Alternatively, the project can be run with hot reload where the server refreshes when the `Python` or `TOML` project files are modified:
>> ```bash
>> find . -name "*.py" -or -name "*.toml" | entr -r streamlit run Home.py --server.fileWatcherType auto --server.headless true
>> ```
>
> A default credential is setup for developers to log in:
>> Username: `example`<br/>
>> Password: `Makers`

### Local setup without `devcontainers`
Clone repo, then copy `config.toml.example` to `config.toml`, and `secrets.toml.example` to `secrets.toml` and update the values.
Note that you will need a remote database connection (MySQL is the default) configured with a users table, for example:

table drea_users;
```
+--------------+--------------+------+-----+---------+-------+
| Field        | Type         | Null | Key | Default | Extra |
+--------------+--------------+------+-----+---------+-------+
| username     | varchar(255) | NO   | PRI | NULL    |       |
| email        | text         | YES  |     | NULL    |       |
| name         | text         | YES  |     | NULL    |       |
| passwordhash | text         | YES  |     | NULL    |       |
| approved     | tinyint(1)   | YES  |     | NULL    |       |
+--------------+--------------+------+-----+---------+-------+
```


### Get the data

Put all of the data inside the folder named `app/data`.

#### Synapse data (MIPE 3.0)
<br>You will need a valid synapse.org account and approved
<br>access (portal request) to [syn5522627](https://www.synapse.org/#!Synapse:syn5522627) - which you can search for on synapse.org

Run the following inside the `app/data` folder

```
pip install synapseclient[pandas,pysftp]
mkdir syn5522627
cd syn5522627
synapse get -r syn5522627
```

#### Dep Map data

Download here (if the direct link doesn't work, navigate to Downloads > File Downloads and continue):

https://depmap.org/portal/download/all/ -> Drug Screens -> PRISM Repurposing 19Q4

Download the file:

| File | Date | Size | 
| -------- | ------- | ------- |
| secondary-screen-dose-response-curve-parameters.csv | 07/19 | 39.3 MB |

Save your csv file in `app/data/DepMap/Prism19Q4/`

And also download the latest mutation data from Downloads -> -> Current Release \(tab\) -> Mutations \(tab\) -> OmicsSomaticMutationsMatrixDamaging.csv 

Save your csv file in `app/data/DepMap/Public24Q4/`

### Install depdencies and run

Change to `app/` directory<br>
Install Python requirements `pip install -r requirements.txt`<br>
Start the app on Windows `streamlit run .\Home.py`<br>
Start the app Linux/MacOS `streamlit run ./Home.py`

Note that on first run, you may need to do a page reload two times before the site displays a consistant view, or stable error message.

## Deploying to a server

Log into the server<br>
Clone the docker repo, and change into it:<br>
[https://github.com/MocoMakers/docker_streamlit](https://github.com/MocoMakers/docker_streamlit)
<br><br>
Run the command in the docker repo:
```
docker build . -t streamlit_app
```
<br>
Clone this repo.<br>

Copy `app/.streamlit/config.toml.example` to be just `config.toml`.<br>
Copy `app/.streamlit/secrets.toml.example` to be just `secrets.toml` and fill in the desired password.

Then run:<br>
```
docker run -p 8501:8501 -v ~/nf_streamlit/app:/app streamlit_app
```
<br>
The first command only needs to be run one time. To run the server using the second command, chaging `~/docker_streamlit/app` for the location of the `app` directory in this repo.


## **Tech Stack**
This project uses the following technologies:
- **Cursor IDE** <small>([download here](https://cursor.sh))</small> - AI-powered code editor with MCP support
- **MCP Toolbox** <small>([GitHub](https://github.com/googleapis/genai-toolbox))</small> - Model Context Protocol server for database integration
- **PostgreSQL** <small>([official image](https://hub.docker.com/_/postgres))</small> - High-performance database
- **Docker & Docker Compose** <small>([install](https://docs.docker.com/get-docker/))</small> - Containerization platform
- **Streamlit** <small>([Custom container](https://github.com/MoCoMakers/nf_streamlit/blob/developer/environment/.devcontainer/Dockerfile) built from [Python base](https://hub.docker.com/_/python))</small> - Web application framework
- **Git** <small>([download here](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git))</small> - Version control

For detailed setup instructions for MCP integration, see **[MCP_INTEGRATION.md](MCP_INTEGRATION.md)**.

# Troubleshooting for Mac users
If you face errors upon running the `pip install -r requirements.txt`, the following [link](https://stackoverflow.com/questions/76876823/cannot-install-mysqlclient-on-macos) may be of help.

## 🔍 **MCP Integration for Database Introspection (Optional)**

For advanced database exploration and analysis capabilities, see the dedicated **[MCP Integration Guide](MCP_INTEGRATION.md)** which covers:

- **MCP Toolbox Setup** - Docker container configuration
- **Cursor IDE Integration** - MCP server configuration
- **Database Introspection** - Sample prompts and queries
- **Troubleshooting** - Common issues and solutions

The MCP integration provides powerful tools for exploring your data warehouse structure and validating data migrations.


## 📖 **Additional Resources**

- **[MCP_INTEGRATION.md](MCP_INTEGRATION.md)** - Complete MCP setup and usage guide
- **[MIGRATION_STRATEGY.md](MIGRATION_STRATEGY.md)** - Detailed migration plan and technical specifications
- **[MCP Toolbox Documentation](https://github.com/googleapis/genai-toolbox)** - Official MCP Toolbox documentation
- **[Cursor IDE Documentation](https://cursor.sh/docs)** - Cursor IDE setup and usage guide
- **[PostgreSQL Documentation](https://www.postgresql.org/docs/)** - Database setup and optimization