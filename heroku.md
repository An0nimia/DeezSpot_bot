## Deploying This bot using HEROKU-CLI
Heroku cli is the method which you can remotely your app via any terminal like windows-linux-android(Termux)

## Pre-requisites
- [`Heroku`](https://heroku.com) accounts
- Node js + npm (android just nodejs)
- Python 3.9
- [`Heroku cli`](https://devcenter.heroku.com/articles/heroku-cli) on android use `npm i -g heroku` use [`TERMUX`](https://play.google.com/store/apps/details?id=com.termux)

## Tutorial
- Setup everything needed read [`This`](https://github.com/An0nimia/DeezloaderBIB_bot/tree/heroku#set-up)
- Running it until completely fixed like [`This`](https://telegra.ph/file/41da7712f38693958c497.jpg)
- Now delete & edit some code
  1. [`Delete This`](https://github.com/An0nimia/DeezloaderBIB_bot/blob/0cf46001bf8676293cf3b643d8d3f7678da4b408/deez_bot.py#L42) `, show_menu, create_tmux`
  2. [`Edit This`](https://github.com/An0nimia/DeezloaderBIB_bot/blob/0cf46001bf8676293cf3b643d8d3f7678da4b408/deez_bot.py#L59) `mode_bot = show_menu()` TO `mode_bot = 2`
  3. [`Delete this line`](https://github.com/An0nimia/DeezloaderBIB_bot/blob/0cf46001bf8676293cf3b643d8d3f7678da4b408/deez_bot.py#L798) `tmux_session = create_tmux()`
- Delete folder `.git` because it will be replaced to git from heroku
- Login into your heroku account with command:
```
heroku login
```
- Create a new heroku app
```
heroku create appname
```
- Init the repo
```
git init
```
- Select app for remote
```
heroku git:remote -a appname
```
- Add all for push
```
git add .
git add * -f
```
- Commit all that you have added
```
git commit -m "First push"
```
- Now push it
```
git push heroku master
```
- All done

**Notes** You can turn on and off your app from Heroku-cli
- Turn on
```
heroku ps:scale worker=1 -a appname
```
- Turn off
```
heroku ps:scale worker=0 -a appname
```

Thanks to [`An0nimia`](https://github.com/An0nimia) Has allowed to use this method to share
