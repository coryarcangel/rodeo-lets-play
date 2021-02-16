const childProcess = require('child_process')

const delay = (ms) => new Promise(resolve => setTimeout(() => resolve(), ms))

// https://stackoverflow.com/questions/29548477/how-do-you-set-the-terminal-tab-title-from-node-js
const setWindowTitle = (title) => {
  process.stdout.write(
    String.fromCharCode(27) + "]0;" + title + String.fromCharCode(7)
  )
}

const setupProcessHubScreen = async (title) => {
  const filepath = `${__dirname}/../src/set_process_hub_screen.py`
  childProcess.execSync(`python3 ${filepath} ${title}`)
  // await delay(100)
}

module.exports = { delay, setWindowTitle, setupProcessHubScreen }
