# Building a Slack bot for Fink

## Data source

We provide two ways to get Fink data:
1. polling Fink database using the REST API
2. polling Fink live streams

Note that databases are updated only once a day at 6pm Paris Time (5pm UTC) -- so you will not have access to the nightly data before this time. On the other hand, the livestream service sends data in real-time.

## Setting up Slack

1. Channel -> Create channel
2. Get channel details -> Add an App
3. Incoming WebHooks -> Add to Slack
4. Post to channel -> <your channel you've created>
5. copy the URL given :-)

See also this [presentation](https://docs.google.com/presentation/d/1lZRPzI45T9IfAA6k5e_J6VmWnF5q6-H-oaqAj-McFH0/edit?usp=sharing) for screenshots.


## Setting up a cronjob

You can manually execute the provided scripts, but it is probably better to automatise it. If you are using a Unix machine, you can easily set a cronjob by editing the crontab

```bash
crontab -e
```

and add this line (adapt to your schedule/timezone):

```bash
0 18 * * * source /path/to/.bash_profile; /path/to/bin/python /path/to/poll_api_rest.py
```

where the URL is defined in the `/path/to/.bash_profile`:

```
export FINKWEBHOOK=<URL provided by Slack>
```

### For Macos users

With recent Mac, you have to give the Full Disk Access permissions to cron:

1. Apple Menu -> System Preferences -> Security & Privacy -> Full Disk Access
2. Click the Lock to Allow Changes
3. Click the + Sign
4. Hit `Command + Shift + G` and in type `/usr/sbin/`
5. Scroll to find `cron` in the list of binaries
6. Click `Open`

## Running the livestream in the background

Alternatively, you can get alerts as they come. For this, you need to register to the [livestream service](https://fink-broker.readthedocs.io/en/latest/fink-client/). Once you have your credentials, adapt the provided `poll_livestream.py` script, and launch it in the background using:

```bash
nohup poll_livestream.py >> poll_livestream.log 2>&1 &
```

If you want to stop listening, just kill the process:

```bash
ps aux | grep poll_livestream
# read the PID
kill $PID
```
