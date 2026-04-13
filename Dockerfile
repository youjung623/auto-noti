FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .

# state.json 영속성을 위한 볼륨 마운트 포인트
VOLUME ["/app/data"]

# state.json을 /app/data 에 저장하도록 심볼릭 링크 사용
# (컨테이너 시작 시 entrypoint.sh 가 처리)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "scheduler.py"]
