# Lovebox

To have the python file run automatically when connecting to power or after rebooting, after using scp to load the script to the pi, run ```sudo nano /etc/systemd/system/lovebox.service``` and copy past the lovebox.service contents into there, making sure to change the User (what you named the pi), Working Directory, and ExecStart to what you have configured. Then run the following in order:
```
sudo systemctl daemon-reload
```

```
sudo systemctl enable lovebox
```

```
sudo systemctl start lovebox
```

To check the status, run:
```
sudo systemctl status lovebox
```

To stop or restart the service, run:
```
sudo systemctl stop lovebox
sudo systemctl restart lovebox
```
