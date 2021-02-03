#!/usr/bin/env node

const childProcess = require('child_process')
const treeKill = require('tree-kill')

const VYSOR_APP_PATH = __dirname + '/../bin/Vysor-linux-3.1.4.AppImage' //  '/home/cory/Downloads/Vysor-linux-3.1.4.AppImage'

const delay = (ms) => new Promise(resolve => setTimeout(() => resolve(), ms))

const getWindowId = (name) =>
  Number(childProcess.execSync(`xdotool search --limit 1 --onlyvisible --name ${name}`).toString('utf-8'))

const activateWinId = (windowId) => childProcess.execSync(`xdotool windowactivate ${windowId}`)

function clickPosInWindow(name, x, y) {
  const windowId = getWindowId(name)
  activateWinId(windowId)
  childProcess.execSync(`xdotool mousemove --window ${windowId} ${x} ${y}`)
  childProcess.execSync('xdotool click 1')
}

function clickPosInMainVysor(x, y) {
  clickPosInWindow('VYSOR', x, y)
}

function activateFrontend() {
  const windowId = getWindowId('KIM_FRONTEND')
  if (windowId) {
    activateWinId(windowId)
  }
}

let vysor

async function main() {
  // kill existing vysor process if it exists
  try {
    childProcess.execSync('pkill vysor')
  } catch (err) {}
  await delay(200)

  // start new vysor process
  console.log('starting vysor')
  vysor = childProcess.spawn(VYSOR_APP_PATH, {
    stdio: 'inherit'
  })
  await delay(3500)

  // set up phone window
  try {
    console.log('setting up phone window')
    clickPosInMainVysor(750, 135)
    activateFrontend()
  } catch (err) {
    console.log('error controlling vysor window', err)
  }

  return new Promise((resolve, reject) => {
    vysor.on('exit', exitCode => {
      return exitCode ? reject(` Error: exited with code: ${exitCode}`) : resolve()
    })
  })
}

if (!module.parent) {
  main()
    .catch(err => console.log('vysor error', err))
    .then(() => {
      console.log('exiting vysor')

      if (vysor) {
        treeKill(vysor.pid, 'SIGTERM', err => {
          if (err) {
            console.log('error killing vysor', err)
          }
        })
      }
    })
}

  /**
    COPIED HERE IS THE OLD start_vysor.sh script for posterity

    #!/bin/bash

    # Start Vysor
    #~/electron-chrome/node_modules/electron/dist/electron --enable-logging ~/electron-chrome --app-id=gidgenkbbabolejbgbpnhbimgjbffefm

    # Start Vysor in PWA
    # Hinted from https://stackoverflow.com/questions/62364515/open-up-multiple-pwa-using-the-google-chrome-cli-option
    # App Ids available here: ~/.config/google-chrome/Default/Extensions/
    # google-chrome --profile-directory=Default --app-id=gfknjhjpnhcfadibcopidfknmoennjmd

    # Start Vysor the Linux 3.2.0 Version on god
    ~/Downloads/Vysor-linux-3.1.4.AppImage
    # kill with "pkill vysor"
  */
