FROM condaforge/mambaforge:latest

COPY ./cli /tmp/cli
COPY ./producer /tmp/producer

RUN mamba install --yes numpy obspy \
    && pip install -e /tmp/producer \
    && pip install -e /tmp/cli

CMD ["cava-realtime", "producer", "stream"]
