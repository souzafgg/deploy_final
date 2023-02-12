FROM python:slim

WORKDIR /app

COPY ./deploy_final/requirements.txt .

RUN pip install -r requirements.txt

COPY ./deploy_final .

CMD ["streamlit", "run", "grids_oficial.py"]
