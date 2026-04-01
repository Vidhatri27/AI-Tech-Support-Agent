# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements (we will generate this or specify here)
RUN pip install --no-cache-dir fastapi uvicorn pydantic openai

# Copy application files
COPY . .

# Expose port (HF Spaces defaults to 7860)
EXPOSE 7860

# Set environment variables for HF
ENV HOST=0.0.0.0
ENV PORT=7860

# Command to run the FastAPI server
CMD ["python", "server.py"]
