FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies and Playwright browsers with required system libs
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m playwright install --with-deps

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
