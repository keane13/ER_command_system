FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all python files into the container
COPY . .

# Run the FastAPI app
CMD ["python", "main.py"]