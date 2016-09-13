import os

def get_completed(logsdir):
    timesteps_completed = 0
    timesteps_count = None
    for lf in os.listdir(logsdir):
        lfpath = os.path.join(logsdir, lf)
        with open(lfpath, 'rb') as f:
            lastline = f.readlines()[-1]
        parts = lastline.split('|')
        if len(parts) > 1:
            completed, count = parts[-1].split('/')
            timesteps_completed += int(completed)
            timesteps_count = int(count)
            
    return {'timesteps_completed': timesteps_completed,
            'timesteps_count': timesteps_count}