FROM python:3.9
RUN pip install policyengine-uk streamlit ipython
WORKDIR /app
COPY . /app
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
ENTRYPOINT ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
