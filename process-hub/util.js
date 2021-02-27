const childProcess = require('child_process')

const delay = (ms) => new Promise(resolve => setTimeout(() => resolve(), ms))

// https://stackoverflow.com/questions/29548477/how-do-you-set-the-terminal-tab-title-from-node-js
const setWindowTitle = (title) => {
  process.stdout.write(
    String.fromCharCode(27) + "]0;" + title + String.fromCharCode(7)
  )
}

const runWindowSetep = async (arg) => {
  const filepath = `${__dirname}/../src/window_setup.py`
  try {
    childProcess.execSync(`python3 ${filepath} ${arg}`)
  } catch (err) {}
  // await delay(100)
}

const setupVisibleWindows = () => runWindowSetep('all')

const setupVysorWindow = () => runWindowSetep('vysor')

module.exports = { delay, setWindowTitle, setupVisibleWindows, setupVysorWindow }
