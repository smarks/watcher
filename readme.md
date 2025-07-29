Usage:

  - Single check: python url_watcher.py <URL>
  - Continuous: python url_watcher.py <URL> --continuous


⏺ To start the webserver:
  python -m http.server 8080

  To stop it:
  - Press Ctrl+C in the terminal where it's running

  To run it in the background:
  python -m http.server 8080 &

  To stop a background server:
  # Find the process ID
  ps aux | grep "http.server"
  # Kill it using the PID
  kill <PID>

  Or use pkill:
  pkill -f "http.server 8080"
 



