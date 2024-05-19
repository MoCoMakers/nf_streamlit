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

# Getting Started
## Local Development (Developers Only)
Clone repo, then copy `secrets.toml.example` to `secrets.toml` and update the values.
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
```


### Get the data
<br>You will need a valid synapse.org account and approved
<br>access (portal request) to [syn5522627](https://www.synapse.org/#!Synapse:syn5522627) - which you can search for on synapse.org

```
pip install synapseclient[pandas,pysftp]
mkdir syn5522627
cd syn5522627
synapse get -r syn5522627
```

### Install depdencies and run
Change to `app/` directory<br>
Install Python requirements `pip install -r requirments.txt`<br>
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
Copy `app/.streamlit/secrets.toml.example` to be just `secrets.toml` and fill in the desired password.

Then run:<br>
```
docker run -p 8501:8501 -v ~/nf_streamlit/app:/app streamlit_app
```
<br>
The first command only needs to be run one time. To run the server using the second command, chaging `~/docker_streamlit/app` for the location of the `app` directory in this repo.
