PID=`cat /srv/admiralbullbot/your_main.pid`

if ! ps -p $PID > /dev/null
then
  rm /srv/admiralbullbot/your_main.pid
  rm /srv/admiralbullbot/nohup.out
  nohup python3 /srv/admiralbullbot/main.py --config /srv/admiralbullbot/configs/pajbot.ini > /srv/admiralbullbot/nohup.out &
  echo $! > /srv/admiralbullbot/your_main.pid
fi