# =============================================
# FX Pipeline - Dockerfile
# =============================================

FROM python:3.11-slim

WORKDIR /app

# install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy project files
COPY pipeline/ ./pipeline/
COPY orchestration/ ./orchestration/

# copy only schema and init script, NOT the sqlite file
COPY db/schema.sql ./db/schema.sql
COPY db/init_db.py ./db/init_db.py

# initialize database (creates tables and seeds dim_currency_pair)
RUN python db/init_db.py

# default command — daily mode
CMD ["python", "pipeline/run_pipeline.py", "--mode", "daily"]