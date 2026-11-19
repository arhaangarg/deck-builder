# Google sign in, once

Only the Google Slides build needs this.
PowerPoint and PDF need no account.

There are two ways in.
Use the first if it applies.

## Option 1: the gws CLI

If the user already has the `gws` CLI installed and signed in, there is nothing to set up.
Check with:

```
gws drive files list --params '{"pageSize": 1}'
```

If that prints a file, pass `--via gws` to `build_gslides.py`.

## Option 2: the user's own OAuth client

The user does these steps themselves, in their own Google account.
Walk them through it.
It takes about five minutes.

1. Open [console.cloud.google.com](https://console.cloud.google.com) and create a project, for example "deck-builder".
2. In **APIs & Services > Library**, enable the **Google Drive API** and the **Google Slides API**.
3. In **APIs & Services > OAuth consent screen**, choose **External**, fill in the app name and their email, and add their own address under **Test users**.
4. In **APIs & Services > Credentials**, choose **Create credentials > OAuth client ID**, with application type **Desktop app**.
5. Download the JSON file and save it as:

```
~/.config/deck-builder/client_secret.json
```

The first build opens a browser window that asks the user to allow access.
After that the sign in is remembered in `~/.config/deck-builder/token.json`.
To keep the client file somewhere else, pass `--client-secret <path>`.

## What the skill can reach

The sign in asks for one permission, `drive.file`.
It lets the skill see and change only the files it created itself.
It cannot read anything else in the user's Drive.

## Trouble

| Message | Fix |
| --- | --- |
| "No Google sign-in yet" | The client file is not at the path above. |
| "Access blocked" in the browser | The user's address is not listed under Test users (step 3). |
| "API has not been used in project" | One of the two APIs is not enabled (step 2). |
| The sign in expires every week | Normal for an app in testing. Delete `token.json` and sign in again, or publish the app in the consent screen. |

Never ask the user to paste a token or a client secret into the chat.
The files stay on their machine.
