#!/bin/bash

# Trap Ctrl+C (SIGINT) and exit signals to kill all child processes
trap 'kill $(jobs -p) 2>/dev/null' EXIT

echo "🚀 Starting PokemonDuel Server..."
npm run dev --prefix server &

echo "🚀 Starting PokemonDuel Frontend..."
npm run dev --prefix frontend &

# Wait for background processes to finish
wait
