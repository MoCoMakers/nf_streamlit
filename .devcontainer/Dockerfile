FROM python:3.9.16-bullseye

WORKDIR /app/nf_streamlit/app
COPY ./app/requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app

COPY . .

RUN apt update && apt install -y mariadb-client entr

RUN python -m pip install --upgrade pip

WORKDIR /app/nf_streamlit/app

EXPOSE 8501

USER $USER

CMD ["systemctl", "suspend"]