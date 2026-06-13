FROM python:3.12-slim

WORKDIR /app

COPY app.py /app/app.py
COPY static /app/static

ENV HOST=0.0.0.0
ENV PORT=5055
ENV PET_STATE_PATH=/config/pet_state.json

EXPOSE 5055

CMD ["python", "app.py"]
