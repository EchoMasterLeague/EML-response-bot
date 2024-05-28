Echo Master league Discord Bot
==============================
This discord bot provides an interface for League data to Players in Echo Master League.

- For fast-iteration development, it is easiest to run the code locally in a docker machine, building it each restart. This ensures that all development environments are the same between developers. 
- For beta hosting (where changes are less frequent and waiting for updates are not as critical), it is best to use GitHub workflows and [Watchtower](github.com/containrrr/watchtowner) to automatically update the build.
- For production hosting (where uptime is more critical than new features, and k8s is out of scope), it is best to use GitHub workflows and Watchtower in notification-only mode to alert you when the build needs to be updated. This prevents any downtime from occurring if the build fails to run on the production server when no developers are online to fix/revert the change. 

## Docker Setup:
### All systems:
1. Create a .env file in the root directory of the project. It should be formatted as below, with each value filled in:
```env
DOCKER_REPO=
DISCORD_TOKEN=
SECRETS_FOLDER=
```
2. Run `set -a` then `source .env` to initialize and setup the environment variables.
3. Add the Google Credentials file of a Service Account with access to the Google Sheet being used for the database to `{PROJECT}/Xena/.secrets`.

### Local:
For developers setting up their local environments for quickly iterating and testing, using [Docker Desktop](https://www.docker.com/products/docker-desktop/) locally.
4. Start the bot building the image `docker build -t eml-discord-bot .` then running it `docker run -e ${DISCORD_TOKEN}`. Repeat on each change to restart the bot with your new changes.

### Beta/Early Version Setup
For hosting versions for a beta testing group. A balance between quick iteration and organization using [GitHub Actions](https://github.com/features/actions), [Docker Hub](https://hub.docker.com), and [Watchtower](https://github.com/containrrr/watchtowner)
4. Get the Watchtower image by running `docker pull containrrr/watchtower`
5. Add `WATCHTOWER_ARGS=--interval 86400` to the `.env` file, replacing `86400` value with how often Watchtower should check for updates (in seconds).
5. Start the bot using `docker compose up`. Everything needed should start with this command.

### Production Setup
For final hosting, where high uptime is critical and there are long times between updates. Using the same stack as the beta, but with monitor-only Watchtower. *Ideally this would use Kubernetes for redundancy, increasing uptime. However, this solution still has good uptime, plenty for a project of this scale.*
4. Get the Watchtower image by running `docker pull containrrr/watchtower`
5. Add `WATCHTOWER_ARGS=--interval 86400 --notification-url "discord://**TOKEN**@**CHANNEL ID**" --monitor-only` to the `.env` file, replacing `86400` value with how often Watchtower should check for updates (in seconds) and the values in ** with their respective values.
5. Start the bot using `docker compose up`. Everything needed should start with this command.
###
***This code is created by the Echo Master League, found at https://echomasterleague.com/. Other use cases are not supported and will not receive assistance. Use at own risk.***