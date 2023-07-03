# Get the poster
[https://www.mocomakers.com/wp-content/uploads/2023/06/qHTS-NF1-Drugs-List-PosterV8-Final.pdf](https://www.mocomakers.com/wp-content/uploads/2023/06/qHTS-NF1-Drugs-List-PosterV8-Final.pdf)

# About this project:
This code hosts a web tool (DREA web tool) for exploring NF1 quantitative High Throughput Screening (qHTS) data.

Please visit this tool live here:
[http://nf.mocomakers.com:8501/](http://nf.mocomakers.com:8501/) - Request a password from matt@mocomakers.com

A sister repo to this project is: [https://github.com/MoCoMakers/hack4nf-2022](https://github.com/MoCoMakers/hack4nf-2022)

# Getting Started
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

## Local Development (Developers Only)
Clone repo, then copy `secrets.toml.example` to `secrets.toml` and update the values

Change to `app/` directory<br>
Install Python requirements `pip install -r requirments.txt`<br>
### Get the data
<br>You will need a valid synapse.org account and approved
<br>access (portal request) to syn5522627 - which you can search for on synapse.org   

```
pip install synapseclient[pandas,pysftp]
mkdir syn5522627
cd syn5522627
synapse get -r syn5522627
```
Start the app `streamlit run .\app.py`
