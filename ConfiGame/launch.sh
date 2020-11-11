sudo killall python
nohup python discordserver.py &
sudo -E nohup python flaskserver.py &
echo "OK"
