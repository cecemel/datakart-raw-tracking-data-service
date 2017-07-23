FROM tiangolo/uwsgi-nginx-flask:flask-python3.5
RUN pip install -q -v -r /app/requirements.txt
COPY . /app
