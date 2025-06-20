# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for SQLite and GLPK
# For pyodbc (if you switch to Azure SQL), you'd need additional ODBC drivers here.
# Example for pyodbc: RUN apt-get update && apt-get install -y unixodbc-dev
RUN apt-get update && apt-get install -y \
    build-essential \
    glpk-utils \
    libglpk-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the working directory
# This includes app.py, db_manager.py, optimizer.py
# and the data directory which will contain your .db and .csv files
COPY . .

# Expose the port that Streamlit runs on
EXPOSE 8501

# Command to run the Streamlit application
# The `streamlit run` command will serve the app.py file
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
