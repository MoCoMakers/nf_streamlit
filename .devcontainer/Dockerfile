FROM python:3.9.16-bullseye

WORKDIR /app

COPY . .

WORKDIR /app/nf_streamlit/app

RUN apt update && apt install -y mariadb-client

RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

EXPOSE 8501

USER $USER

CMD ["systemctl", "suspend"]