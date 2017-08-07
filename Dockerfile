FROM tiangolo/uwsgi-nginx-flask:flask-python3.5
COPY big_query_nginx.conf /etc/nginx/conf.d/
COPY requirements.txt /app/
RUN pip install -q -v -r /app/requirements.txt
COPY . /app
