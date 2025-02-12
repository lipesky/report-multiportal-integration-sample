FROM python:3.10 as sample-report-multiportal-sever
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
ARG PORT=80
ENV PORT=$PORT
# make sure all messages always reach console
ENV PYTHONUNBUFFERED=1
EXPOSE $PORT
CMD ["python", "main.py"]