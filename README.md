https://www.markdownguide.org/basic-syntax/


1. Bootstrap

    https://getbootstrap.com/docs/5.3/getting-started/introduction/
    
    Bootstrap is a powerful, feature-packed frontend toolkit.
    I have not included Popper.

2. HTML

    https://www.w3schools.com/tags/att_button_type.asp


3. FLASK - youtube

    https://www.youtube.com/watch?v=4nzI4RKwb5I&list=PLzMcBGfZo4-n4vJJybUVV3Un_NFS5EOgX&index=3


3. GIT

    Von der folgenden Seite habe ich nur bis einschließlich Punkt 5 gemacht und den REST über VS Code.
    Denke aber, dass Punkt 5 nicht gemacht werden muss.

    https://sites.google.com/site/cartwrightraspberrypiprojects/home/ramblings/tutorials/using-github?pli=1


    Installation der GitLens Extension in VS Code und diese mit dem GitHub-Konto verbunden.
    Dazu ist der folgende Link auch interessant:

    https://www.digitalocean.com/community/tutorials/how-to-use-git-integration-in-visual-studio-code-de


5. Docker

    https://www.freecodecamp.org/news/how-to-dockerize-a-flask-app/

    ```console
    # Show the IP Address
    hostnqme -I

    # List all docker images
    docker images

    # List all currently running containers
    docker ps

    # Build the docker image
    docker build -t flasktest2 .

    # Run the docker image
    docker run --device /dev/gpiomem -p 8000:8000 flasktest2
    ```

    Other commands

    ```console
    # Stop a currently running container
    docker stop <container-name>

    # Another useful command to have when working with Docker is this one
    docker container prune

    # To delete all containers including its volumes use
    docker rm -vf $(docker ps -aq)

    # To delete all the images
    docker rmi -f $(docker images -aq)
    ```


6. DIVERS

    Die Session kann komplett geleert werden mit:
    ```
    session.clear
    ```

    Man kann auch ein Objekt in der Session entfernen mit:
    ```
    session.pop('Name', None)
    ```

    Arbeiten mit einer ENV-Datei
    Es kommt kein SECRET Code in den Source-Code und auch nicht nach GIT
    https://pypi.org/project/python-dotenv/
