import os

def get_completed():
    logsdir = os.path.join(os.path.dirname(__file__), 'logs')
    timesteps_completed = 0
    timesteps_count = None
    for lf in os.listdir(logsdir):
        lfpath = os.path.join(logsdir, lf)
        with open(lfpath, 'rb') as f:
            lastline = f.readlines()[-1]
        progress = lastline.split('[')[-1].split(']')[0]
        parts = progress.split('/')
        if len(parts) == 2:
            timesteps_completed += int(parts[0])
            timesteps_count = int(parts[1])
            
    return {'timesteps_completed': timesteps_completed, 'timesteps_count':timesteps_count}