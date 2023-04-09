# mailit
**Repo:** [https://github.com/JohnMasinter/mailit](https://github.com/JohnMasinter/mailit)  
**Access:** Public  
**License:** MIT

**Description:**  
mailit.py is a command line python utility to send mail messages or files to a MX'er server via SMTP. It is a flexible, and you may easily modify or extend it. This is great for testing software that handles email, or for use by any admin scripts that want to send email notifications.

The mailt utility is contained in one .py file. The dirs will contain many source files numbered as mailit-01.py, mailit-02.py, ..., which repreent the evolution from the simplest smtp test to the full featured version. Python provides a nice smtp lib to make this easy. But this utility uses only sockets and implements its own SMTP. This is great for learning smtp, or modifing to test variations of smtp.

If you want to fetch the latest most functional version, then pick the highest numbered py file.

**Directories:**  
```
src          - All source is under this dir
   /python2  - python2 versions, mailit-01.py - mailit-11.py
   /python3  - python3 versions, mailit-01.py - mailit-11.py
   /bash     - bash scripts using mailit to demonstrate various uses
      /mailit-test.sh    - simple example to send a string as a mail message
      /mailit-uptime.sh  - monitor list of mail servers, report any down-time
      /mailit-volume.sh  - mung email address in a text file to protect from spam
```

**Past:**  
These are incremental versions starting from the very first tiny test program. These are included as they maybe helpful for a learning activity.

- mailit-01.py
- mailit-02.py
- mailit-03.py
- mailit-04.py
- mailit-05.py
- mailit-06.py
- mailit-07.py
- mailit-08.py
- mailit-09.py
- mailit-10.py

**Examples:**

- To make it easy, perhaps put "alias mailit=mailit-11.py" or similar in your `~/.bashrc`
- blah
