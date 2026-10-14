FROM python:3.13-alpine
LABEL org.opencontainers.image.source="https://github.com/ATOMNFT/Pokemon-Card-Totals"
WORKDIR /app
RUN addgroup -S widget && adduser -S widget -G widget && mkdir /data && chown widget:widget /data
COPY --chown=widget:widget app.py /app/app.py
COPY --chown=widget:widget static /app/static
USER widget
ENV PYTHONUNBUFFERED=1 DATA_DIR=/data PORT=8080
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3)" || exit 1
CMD ["python", "app.py"]
