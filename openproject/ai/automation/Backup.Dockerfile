ARG CORE_IMAGE=qldapm-openproject:dates-final-20261015
FROM ${CORE_IMAGE}
USER root
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
USER app
ENTRYPOINT ["python3", "-u", "/trusted/local_backup.py"]
CMD ["watch"]
LABEL org.qldapm.operator="local-backup"
