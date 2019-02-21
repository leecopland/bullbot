PID=`cat /srv/admiralbullbot/your_relay.pid`

if ! ps -p $PID > /dev/null
then
  rm /srv/admiralbullbot/your_relay.pid
  rm /srv/admiralbullbot/nohup_relay.out
  nohup /srv/relaybroker/relaybroker > /srv/admiralbullbot/nohup_relay.out &
  echo $! > /srv/admiralbullbot/your_relay.pid
fi