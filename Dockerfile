FROM python:3.12-slim

# Install openssh-server
RUN apt-get update && apt-get install -y openssh-server && \
    mkdir /var/run/sshd && \
    # Create user 'dev' with password '123'
    useradd -m -s /bin/bash dev && \
    echo 'dev:123' | chpasswd && \
    # Allow password authentication
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    # Clean up
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80 22

CMD ["/app/server.py"]