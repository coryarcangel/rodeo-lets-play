#!/usr/bin/env node

const inquirer = require('inquirer')
const spawnCommand = require('spawn-command')
const moment = require('moment')
require('colors')
const blessed = require('blessed')
const contrib = require('blessed-contrib')
const { argv } = require('yargs')
const { range } = require('lodash')
const treeKill = require('tree-kill')

/// Config

const DUMMY = argv.dummy !== undefined ? argv.dummy : false
const DELAY_BETWEEN_STARTUPS = argv.delay || 200
const ROWS = 24
const COLS = 4
const START_ALL = !!argv.startAll

const startTime = moment()

/// Dashboard Setup

const screen = blessed.screen()
const grid = new contrib.grid({ rows: ROWS, cols: COLS, screen: screen })

const mainDashboardLogger = grid.set(0, 0, ROWS / 4, COLS / 2, contrib.log, {
  label: 'Dashboard Log',
  fg: 'white',
  selectedFg: 'white',
})

const commandList = grid.set(0, COLS / 2, ROWS / 4, 1, blessed.list, {
  label: 'Commands & Status',
  mouse: true,
  keys: true,
  style: {
    selected: { bg: 'gray' }
  },
  items: ['Test', 'Test 2']
})

const timerLcd = grid.set(0, 3, ROWS / 4, 1, contrib.lcd, {
  label: 'Run Time',
  elements: 8,
  display: '00:00:00',
  segmentWidth: 0.09,
  segmentInterval: 0.2,
  strokeWidth: 0.25,
  elementPadding: 4,
  elementSpacing: 2,
  color: 'yellow',
  style: { bg: 'black' }
})

const processStopLineGraph = grid.set(ROWS / 4, COLS / 2, 8, COLS / 2, contrib.line, {
  label: 'Restarts Over Time',
  wholeNumbersOnly: true,
  showLegend: true,
  xLabelPadding: 3,
  xPadding: 3,
  yLabelPadding: 3,
  yPadding: 3,
  style: {
    line: 'yellow',
    text: 'green',
    baseline: 'black'
  }
})

const processStopBarGraph = grid.set(14, COLS / 2, 4, COLS / 2, contrib.stackedBar, {
  label: 'Total Process Restarts',
  barWidth: 12,
  barSpacing: 20,
  xOffset: 0,
  barBgColor: ['green', 'red']
})

const aiStatusBox = grid.set(ROWS / 4 * 3, COLS / 2, ROWS / 4, COLS / 2, blessed.box, {
  label: 'Current AI Status',
  content: 'Unknown at this time'.red.bold,
  style: { bg: 'blue', fg: 'white' },
})

/// Util

const logToDashboard = (dashboardLogger, ...strings) => {
  const now = moment().format('YY-MM-DD HH:mm:ss')
  dashboardLogger.log(`${now}: ${strings.join(' ')}`)
}

const genlog = (...strings) => logToDashboard(mainDashboardLogger, ...strings)

const delay = (ms) => new Promise(resolve =>
  setTimeout(() => resolve(), ms)
)

/// Kim Process

class KimProcess {
  constructor(ops) {
    const { name, abbrev, script, bg, index } = ops
    this.name = name
    this.abbrev = abbrev
    this.script = DUMMY
      ? `echo ${script} && sleep ${Math.floor(Math.random() * 10)}`
      : script
    this.background = bg
    this.index = index

    const colors = ['blue', 'yellow', 'magenta', 'cyan', 'white']
    const logColors = ['#8282ff', 'yellow', 'magenta', 'cyan', '#ff8a00']
    this.color = colors[index] || colors[0]
    this.logColor = logColors[index] || logColors[0]

    const isAI = abbrev === 'AI'
    this.logger = grid.set(6 + index * 3, 0, isAI ? ROWS / 4 : 3, COLS / 2, contrib.log, {
      label: `${this.name} Log`,
      fg: this.logColor,
      selectedFg: this.logColor,
    })

    this.started = false
    this.running = false
    this.cancelled = false
    this.logs = []
    this.errs = []
    this.stopTimes = []

    this.logLimit = 1000
    this.errLimit = 1000
    this.timeBetweenScriptRuns = 3000
  }

  addStreamBufferLine(type, buffer) {
    const isErr = type === 'stderr'

    const line = buffer.toString('utf8').trimRight()

    const logLine = isErr ? line.red : line
    logToDashboard(this.logger, logLine)

    const arr = isErr ? this.errs : this.logs
    const limit = isErr ? this.errLimit : this.logLimit
    arr.unshift({ when: moment(), line })
    if (arr.length > limit) {
      arr.splice(limit, arr.length - limit)
    }
  }

  runScript() {
    genlog(`Starting Process - ${this.name}`.green)
    return new Promise((resolve, reject) => {
      this.running = true
      const child = this.child = spawnCommand(this.script)

      child.stdout.on('data', data => {
        this.addStreamBufferLine('stdout', data)
      })

      child.stderr.on('data', data => {
        this.addStreamBufferLine('stderr', data)
      })

      child.on('exit', exitCode => {
        this.running = false

        if (!exitCode) {
          resolve()
        } else {
          reject(`${this.name} Error: exited with code: ${exitCode}`)
        }
      })
    })
  }

  async startLoop() {
    if (this.started && !this.cancelled) {
      return
    }

    this.started = true
    this.cancelled = false

    while (!this.cancelled) {
      await this.runScript()
        .then(() => {
          this.stopTimes.push({ err: null, when: moment() })
          genlog(`Clean exit - ${this.name}`.yellow)
        })
        .catch(err => {
          this.stopTimes.push({ err, when: moment() })
          genlog(`${this.name} - Crash #${this.stopTimes.length} Error:`.red, err)
        })

      await delay(this.timeBetweenScriptRuns)
    }
  }

  cancelProcess() {
    this.cancelled = true

    if (this.child) {
      treeKill(this.child.pid, 'SIGKILL')
    }
  }
}

/// Kim Process Manager

class KimProcessManager {
  constructor() {
    const processConfigs = [
      { abbrev: 'VY', name: 'Vysor', script: 'bin/start_vysor.sh', bg: true },
      { abbrev: 'DS', name: 'Device Server', script: 'bin/start_device_server.sh', bg: true },
      { abbrev: 'FS', name: 'Frontend Server', script: 'bin/start_frontend.sh', bg: true },
      { abbrev: 'PH', name: 'Phone Image Stream', script: 'bin/start_phone_stream.sh', bg: true },
      { abbrev: 'AI', name: 'AI Controller', script: 'bin/start_ai.sh', bg: false },
    ]

    this.processes = processConfigs.map((o, i) => {
      const kp = new KimProcess({ ...o, index: i })
      return kp
    })
  }

  async initBackgroundProcesses() {
    const bgProcesses = this.processes.filter(p => p.background)
    for (const kp of bgProcesses) {
      kp.startLoop()
      await delay(DELAY_BETWEEN_STARTUPS)
    }
  }

  async initForegroundProcesses() {
    const fgProcesses = this.processes.filter(p => !p.background)
    for (const kp of fgProcesses) {
      kp.startLoop()
      await delay(DELAY_BETWEEN_STARTUPS)
    }
  }
}

const kpManager = new KimProcessManager()

/// Current State

let commands = []

const getCurrentCommands = () => {
  return [
    { label: 'Rest', fn: () => { } },

    ...kpManager.processes.map((p, i) => {
      return {
        label: `${p.name} - ${p.running ? 'Running'.green : p.cancelled || !p.started ? 'Select to Start'.yellow : 'Waiting to start'.red}`,
        fn: () => {
          if (p.cancelled || !p.started) {
            p.startLoop()
          } else {
            p.cancelProcess()
          }
        }
      }
    }),

    { label: 'Xx Abort xX'.bgRed.white, fn: () => quit() }
  ]
}

const getCurProcessStopLineGraphData = () => {
  let now = moment()
  const hoursDiff = now.diff(startTime, 'hours')
  let times = [now]
  let timeLabels = ['']
  const n = 6
  if (hoursDiff < 1) {
    const minutesDiff = Math.max(now.diff(startTime, 'minutes'), 6)
    times = range(n).map(i => startTime.clone().add(i * minutesDiff / n, 'minutes'))
    timeLabels = times.map(t => `${Math.ceil(t.diff(startTime, 'minutes'))}m`)
  } else if (hoursDiff < 6) {
    times = range(n).map(i => startTime.clone().add(i * hoursDiff / n, 'hours'))
    timeLabels = range(n).map(i => `${i}h`)
  } else if (hoursDiff < 24) {
    times = range(n).map(i => startTime.clone().add(i * hoursDiff / n, 'hours'))
    timeLabels = times.map(t => t.format('HH:mm'))
  } else {
    times = range(n).map(i => startTime.clone().add(i * hoursDiff / n, 'hours'))
    timeLabels = times.map(t => t.format('M/D HH:mm'))
  }

  return [
    ...kpManager.processes.map((p, pi) => {
      let yData = times.map((t, ti) => p.stopTimes.filter(s => {
        const next = times[ti + 1]
        return next ? s.when.isBefore(next) : true
      }).length)

      return {
        title: `${p.abbrev}`,
        style: { line: p.color },
        x: timeLabels,
        y: yData
      }
    })
  ]
}

const getCurProcessStopBarGraphData = () => {
  const processData = kpManager.processes.map(p => {
    const clean = p.stopTimes.filter(s => !s.err).length
    const crash = p.stopTimes.length - clean
    return { name: p.name, clean, crash }
  })

  return {
    barCategory: processData.map(d => d.name),
    stackedCategory: ['Clean', 'Crash'],
    data: processData.map(d => [d.clean, d.crash])
  }
}

/// Dashboard Drawing

function drawDashboard() {
  commands = getCurrentCommands()
  commandList.setItems(commands.map(c => c.label))

  processStopLineGraph.setData(getCurProcessStopLineGraphData())
  processStopBarGraph.setData(getCurProcessStopBarGraphData())

  const startDiff = moment.utc(moment().diff(startTime)).format('HH:mm:ss')
  timerLcd.setDisplay(startDiff)

  screen.render()
}

function drawDashboardLoop() {
  drawDashboard()
  setTimeout(drawDashboardLoop, 100)
}

/// Main

async function quit() {
  kpManager.processes.forEach(p => {
    // p.cancelProcess()
    if (p.child) {
      treeKill(p.child.pid)
    }
  })

  return process.exit(0)
}

async function main() {
  genlog('Hello, User. Starting KIM AI processes now...')

  commandList.focus()

  // handle commands
  commandList.on('select', (item, index) => {
    const command = index < commands.length ? commands[index] : null
    if (command && command.fn) {
      command.fn()
    }
  })

  // start all necessary background processes
  kpManager.initBackgroundProcesses()
    .then(() => {
      return START_ALL ? kpManager.initForegroundProcesses() : null
    })
    .catch(err => {
      genlog(`Process Running Error:`.red, err)
      throw err
    })

  // allow quit on control C
  screen.key(['C-c'], function(ch, key) {
    return quit()
  })

  drawDashboardLoop()
}

main()
  .catch(err => {
    console.log(`FATAL ALL PROCESS ERROR:`, err)
    process.exit(1)
  })
