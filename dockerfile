FROM python:3.10-alpine
ARG UID=1000
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser
COPY requirements.txt .
RUN pip install -r requirements.txt
EXPOSE 8080
USER appuser
WORKDIR /API
COPY API.py .
CMD [ "python", "API.py"]