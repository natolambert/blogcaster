# Logs for future errors / issues to debug

## ttv-generate.py
"""
Exception in thread Thread-3 (_handle_results):
Traceback (most recent call last):
  File "/Users/nato/miniconda3/envs/media/lib/python3.10/threading.py", line 1009, in _bootstrap_inner
    self.run()
  File "/Users/nato/miniconda3/envs/media/lib/python3.10/threading.py", line 946, in run
    self._target(*self._args, **self._kwargs)
  File "/Users/nato/miniconda3/envs/media/lib/python3.10/multiprocessing/pool.py", line 576, in _handle_results
    task = get()
  File "/Users/nato/miniconda3/envs/media/lib/python3.10/multiprocessing/connection.py", line 256, in recv
    return _ForkingPickler.loads(buf.getbuffer())
TypeError: APIStatusError.__init__() missing 2 required keyword-only arguments: 'response' and 'body'
"""