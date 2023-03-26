1. Markdown \
   https://www.markdownguide.org/basic-syntax/

2. FLASK - youtube \
   https://www.youtube.com/watch?v=4nzI4RKwb5I&list=PLzMcBGfZo4-n4vJJybUVV3Un_NFS5EOgX&index=3

3. GIT \
   Von der folgenden Seite habe ich nur bis einschließlich Punkt 5 gemacht und den REST über VS Code. \
   Denke aber, dass Punkt 5 nicht gemacht werden muss. \
   https://sites.google.com/site/cartwrightraspberrypiprojects/home/ramblings/tutorials/using-github?pli=1

   Installation der GitLens Extension in VS Code und diese mit dem GitHub-Konto verbunden. \
   Dazu ist der folgende Link auch interessant: \
   https://www.digitalocean.com/community/tutorials/how-to-use-git-integration-in-visual-studio-code-de

5. Docker \

   ```console
   # Show the IP Address
   hostname -I

   # List all docker images
   docker images

   # List all currently running containers
   docker ps

   # Build the docker image
   docker build -t keypad .
   docker build -t flasktest2 .

   # Run the docker image
   docker run --device /dev/gpiomem -p 8000:8000 flasktest2
   ```

   Other commands
   ```console
   # Stop a currently running container
   docker stop <container-name>

   # Delete unused Docker objects (containers, images, networks, volumes)
   docker container prune

   # To delete all containers including its volumes use
   docker rm -vf $(docker ps -aq)

   # To delete all volumes
   docker volume rm $(docker volume ls -q)

   # To delete all the images
   docker rmi -f $(docker images -aq)

   # Command to clean all containers, images, volumes, networks, and undefined containers created with docker-compose
   docker-compose down --rmi all -v --remove-orphans

   # Builds, (re)creates, starts containers
   docker-compose up --build
   # Stop all containers
   docker-compose down

   # Connect to SQL container
   docker-compose exec db psql -h localhost -U supermario --dbname=keypad

   # Reset Masterpassword
   UPDATE parameter SET password = NULL, initialized = FALSE;

   # See table content
   SELECT * FROM parameter;
   ```

   Probleme \
   Folgendes musste in die Docker Compose Datei eingebaut werden. Ansonsten geht der Zugriff auf die GPIO nicht. \
   https://www.gerbenvanadrichem.com/infrastructure/accessing-gpio-pins-inside-a-docker-container-on-a-raspberry-pi/

6. THREAD \
   https://unbiased-coder.com/python-flask-multithreading/ \
   https://www.section.io/engineering-education/how-to-perform-threading-timer-in-python/

7. DIVERS \
   Die Session kann komplett geleert werden mit:
   ```
   session.clear
   ```

   Man kann auch ein Objekt in der Session entfernen mit:
   ```
   session.pop('Name', None)
   ```

   Arbeiten mit einer ENV-Datei \
   Es kommt kein SECRET Code in den Source-Code und auch nicht nach GIT \
   Zu Beginn mit python-dotenv gearbeitet und dann aber nach python-decouple gewechselt. \
   Der große Vorteil ist die CAST Methode. \
   Im folgenden Artikel steht unter anderem: \
   The casting and the ability to specify defaults are really convenient and something I miss when using python-dotenv! \
   https://pybit.es/articles/how-to-handle-environment-variables-in-python/

   bcrypt \
   https://stackabuse.com/hashing-passwords-in-python-with-bcrypt/

8. Postgres \
   https://medium.com/free-code-camp/docker-development-workflow-a-guide-with-flask-and-postgres-db1a1843044a

8. ToDo \
    https://stavshamir.github.io/python/dockerizing-a-flask-mysql-app-with-docker-compose/

    https://pypi.org/project/flask-swagger/

    https://auth0.com/blog/developing-restful-apis-with-python-and-flask/

    WSGI HTTP Server - gunicorn
    https://www.donskytech.com/create-flask-web-application-in-raspberry-pi/


    https://testdriven.io/blog/dockerizing-flask-with-postgres-gunicorn-and-nginx/

    https://flask-socketio.readthedocs.io/en/latest/


9. GIO Notes

    https://jinja.palletsprojects.com/en/3.1.x/templates/#jinja-filters.map





https://www.askpython.com/python-modules/flask/flask-postgresql
https://github.com/vsupalov/big-album-art/blob/79bdaba51717b62e0fe4dac59e85ec21e2e035df/baa/main.py#L40
https://stackabuse.com/using-sqlalchemy-with-flask-and-postgresql/
https://dev.to/blankgodd/working-with-postgresql-and-flasksqlalchemy-3c38
https://pythonbasics.org/flask-sqlalchemy/

ich habe den Folder __pycache__ versteckt -> https://paulnelson.ca/posts/hiding-pycache-files-in-vscode

Session are cookie based... \
https://medium.com/thedevproject/flask-sessions-what-are-they-for-how-it-works-what-options-i-have-to-persist-this-data-4ca48a34d3


- den user nicht in der flask session speichern sondern an pincode übtragen und wiedergeben
- die Variable softKeypad in der Auswertung einbauen - wenn nicht dann sie später löschen
- email Validator noch etwas genauer testen (mit DNS Option)
- email automatisch versenden
- account seite kleiner machen (mobil machen)
- schreiben wir noch in eine LOG Tabelle? Wenn nicht dann löschen von Tabelle loginfo
- testen: session gültigkeit auf 2 minuten und in account jedesmal die Varibale neu in die sessions schreiben. Wird sie damit verlängert?