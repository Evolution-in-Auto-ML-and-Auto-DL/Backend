pm2 stop backend
pm2 delete backend
pm2 start "python3 main.py" --name backend --watch
