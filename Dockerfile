
FROM node:22-bookworm-slim AS pot-provider

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git && update-ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /root

RUN git clone --single-branch --branch 2.0.2 https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git

WORKDIR /root/bgutil-ytdlp-pot-provider/server

RUN npm ci && npx tsc


FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

COPY --from=pot-provider /usr/local/ /usr/local/
COPY --from=pot-provider /root/bgutil-ytdlp-pot-provider /root/bgutil-ytdlp-pot-provider

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
