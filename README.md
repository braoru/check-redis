# check-elasticsearch

#Install

##Install check
```Bash
git clone git@github.com:braoru/check-redis.git
virtualenv check-redis
cd check-redis
source bin/activate
pip install --upgrade pip
pip install -r requirement.txt

```

##Redis check connection with echo
```Bash
python check_redis_connection.py -H XXX
OK: Redis connection successful | 'connection_delay'=18[ms];50;100;;; 

```

##Redis check ping
```Bash
python check_redis_ping.py -H XXX
OK: Success to ping-pong 

```
