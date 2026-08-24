FROM python:3.11.16-slim-bookworm@sha256:2e32f7d302adc1c37428355c1e646897c0c53f4fd60b6a551245fb90ee129f91

WORKDIR /opt/soveraeign

COPY --chown=65532:65532 scripts/custody_activation.py /opt/soveraeign/scripts/custody_activation.py
COPY --chown=65532:65532 scripts/node_runtime.py /opt/soveraeign/scripts/node_runtime.py

USER 65532:65532
EXPOSE 8080

ENTRYPOINT ["python", "/opt/soveraeign/scripts/node_runtime.py"]
