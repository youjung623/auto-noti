#!/bin/sh
# state.json 을 볼륨(/app/data)에 영속 저장하도록 연결합니다.
set -e

DATA_DIR=/app/data
STATE_FILE=/app/state.json
PERSIST_FILE=$DATA_DIR/state.json

mkdir -p "$DATA_DIR"

# 볼륨에 state.json 이 없으면 기존 파일(또는 빈 객체)로 초기화
if [ ! -f "$PERSIST_FILE" ]; then
    if [ -f "$STATE_FILE" ]; then
        cp "$STATE_FILE" "$PERSIST_FILE"
    else
        echo '{}' > "$PERSIST_FILE"
    fi
fi

# state.json → /app/data/state.json 심볼릭 링크
if [ ! -L "$STATE_FILE" ]; then
    rm -f "$STATE_FILE"
    ln -s "$PERSIST_FILE" "$STATE_FILE"
fi

exec "$@"
