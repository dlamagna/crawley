#!/bin/bash

MAX_PROCESSES=10

set -a
source .env
set +a

echo "[INFO] Recupero lista scraping task da $TASK_URL..."
TASKS=$(curl -sL -H "User-Agent: Mozilla/5.0" "$TASK_URL")

# Controllo: se la e' vuota o contiene "error"
if [ -z "$TASKS" ] || echo "$TASKS" | jq 'has("error")' | grep -q true; then
  echo "[ERROR] Risposta vuota o contiene errore:"
  echo "$TASKS"
  exit 1
fi

# Dipendenza: jq
if ! command -v jq &> /dev/null; then
    echo "[ERROR] 'jq' non installato. Usa: sudo apt install jq"
    exit 1
fi

# Continua il parsing
# Controlla se la risposta è vuota o non è un array JSON valido
if [ -z "$TASKS" ] || ! echo "$TASKS" | jq -e 'type == "array"' > /dev/null; then
  echo "[ERRORE] JSON non valido o lista dei task vuota"
  echo "$TASKS"
  exit 1
fi

# Itera su ogni task ricevuto
echo "$TASKS" | jq -c '.[]' | while read -r task; do
  ID=$(echo "$task" | jq '.id')
  URL=$(echo "$task" | jq -r '.url')
  DEEP=$(echo "$task" | jq '.deep')

  # Attendi finché il numero di processi attivi è inferiore a MAX_PROCESSES
  while true; do
    ACTIVE=$(pgrep -cf "crawl_with_sleep.py")

    if [ "$ACTIVE" -lt "$MAX_PROCESSES" ]; then
      echo "[INFO] Avvio crawl_with_sleep per Task ID $ID"
      echo "[CMD] crawl_with_sleep.py -u \"$URL\" -d $DEEP"
      python3 crawl_with_sleep.py -u "$URL" -d "$DEEP" -s 1 --ext ".md" &
      sleep 1
      break
    else
      echo "[ATTESA] Troppi processi attivi ($ACTIVE). Attendo..."
      sleep 5
    fi
  done
done

# Attendi la fine di tutti i crawl
wait
echo "[DONE] Tutti i crawl completati."
