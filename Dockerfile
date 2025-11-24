# Use official Python 3.13 image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy requirements.txt first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py ./

# Expose the port that Render expects
ENV PORT 10000
EXPOSE 10000

# Set environment variables if not provided via Render dashboard
# ENV TWILIO_ACCOUNT_SID=your_sid
# ENV TWILIO_AUTH_TOKEN=your_token
# ENV TWILIO_NUMBER=+1234567890
# ENV OPENAI_API_KEY=your_openai_key
# ENV RENDER_BASE_URL=https://your-app.onrender.com

# Command to run the FastAPI app using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
