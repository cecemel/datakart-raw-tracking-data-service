FROM tiangolo/uwsgi-nginx-flask:flask-python3.5
COPY requirements.txt /app/
RUN pip install -q -v -r /app/requirements.txt
COPY . /app
