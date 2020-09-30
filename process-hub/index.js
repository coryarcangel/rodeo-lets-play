#!/usr/bin/env node

const inquirer = require('inquirer')
const childProcess = require('child_process')
const moment = require('moment')
require('colors')
const blessed = require('blessed')
const contrib = require('blessed-contrib')
const { argv } = require('yargs')
const { range } = require('lodash')
const treeKill = require('tree-kill')

/// Config

const DUMMY = argv.dummy !== undefined ? argv.dummy : false
const DELAY_BETWEEN_STARTUPS = argv.delay || 1000
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
  const lines = strings.join('\n').split('\n')
  lines.forEach(l => {
    dashboardLogger.log(`${now}: ${l}`)
  })
}

const genlog = (...strings) => logToDashboard(mainDashboardLogger, ...strings)

const delay = (ms) => new Promise(resolve => setTimeout(() => resolve(), ms))

/// Kim Process

class KimProcess {
  constructor(ops) {
    const { name, abbrev, script, index } = ops
    this.ops = ops
    this.name = name
    this.abbrev = abbrev
    this.script = DUMMY
      ? `echo ${script} && sleep ${Math.floor(Math.random() * 10)}`
      : script
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

  addStreamBufferData(type, buffer) {
    const isErr = type === 'stderr'

    const lines = buffer.toString('utf8').trimRight().split('\n')

    const logLines = isErr ? lines.map(l => l.red) : lines
    logToDashboard(this.logger, ...logLines)

    const arr = isErr ? this.errs : this.logs
    const limit = isErr ? this.errLimit : this.logLimit
    logLines.forEach(line => {
      arr.unshift({ when: moment(), line })
    })

    if (arr.length > limit) {
      arr.splice(limit, arr.length - limit)
    }
  }

  getLabel = () => this.child ? `${this.name} (PID ${this.child.pid})` : this.name

  runScript() {
    return new Promise((resolve, reject) => {
      if (this.child) {
        this.killChild()
      }

      this.running = true
      const child = this.child = childProcess.spawn(this.script, {
        // detached: true,
      })

      genlog(`Started Process - ${this.getLabel()}`.green)

      const listenToStream = (name) => {
        child[name].setEncoding('utf8')
        child[name].on('data', data => this.addStreamBufferData(name, data))
      }

      listenToStream('stdout')
      listenToStream('stderr')

      // child.on('error', err => {
      //   console.log(err)
      // })

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
          genlog(`Clean exit - ${this.getLabel()}`.yellow)
        })
        .catch(err => {
          this.stopTimes.push({ err, when: moment() })
          genlog(`${this.getLabel()} - Crash #${this.stopTimes.length} Error:`.red, err)
        })

      await delay(this.timeBetweenScriptRuns)
    }
  }

  killChild(sig = 'SIGTERM') {
    return new Promise((resolve, reject) => {
      if (this.child) {
        treeKill(this.child.pid, sig, err => {
          return err ? reject(err) : resolve()
        })
      }
    })
  }

  cancelProcess() {
    this.cancelled = true
    return this.killChild('SIGKILL')
  }
}

/// Kim Process Manager

class KimProcessManager {
  constructor() {
    const processConfigs = [
      { abbrev: 'VY', name: 'Vysor', script: 'process-hub/run_vysor.js' },
      { abbrev: 'DS', name: 'Device Server', script: 'bin/start_device_server.sh' },
      { abbrev: 'FS', name: 'Frontend Server', script: 'bin/start_frontend_server.sh' },
      { abbrev: 'PH', name: 'Phone Image Stream', script: 'bin/start_phone_stream.sh' },
      { abbrev: 'AI', name: 'AI Controller', script: 'bin/start_ai.sh', main: true },
    ]

    this.processes = processConfigs.map((o, i) => {
      const kp = new KimProcess({ ...o, index: i })
      return kp
    })
  }

  async initProcesses(startAll) {
    for (const kp of this.processes) {
      if (startAll || !kp.ops.main) {
        kp.startLoop()
        await delay(DELAY_BETWEEN_STARTUPS)
      }
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
      let hasRunFn = false
      return {
        label: `${p.name} - ${p.running ? 'Running'.green : p.cancelled || !p.started ? 'Select to Start'.yellow : 'Waiting to start'.red}`,
        fn: () => {
          if (hasRunFn) {
            return
          }

          if (p.cancelled || !p.started) {
            p.startLoop()
          } else {
            p.cancelProcess()
          }

          hasRunFn = true
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
  await Promise.all(kpManager.processes.map(async p => {
    await p.killChild()
  }))

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
  kpManager.initProcesses(START_ALL)
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
