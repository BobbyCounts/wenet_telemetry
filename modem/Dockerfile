FROM python:3.14.0-slim


WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y libusb-1.0-0

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "wenet_uart.py"]