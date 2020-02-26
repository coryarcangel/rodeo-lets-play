#!/usr/bin/env node

const inquirer = require('inquirer')
const spawnCommand = require('spawn-command')
const moment = require('moment')
require('colors')
const blessed = require('blessed')
const contrib = require('blessed-contrib')

/// Dashboard Setup

const screen = blessed.screen()
const grid = new contrib.grid({ rows: 24, cols: 2, screen: screen })

const mainDashboardLogger = grid.set(0, 0, 6, 1, contrib.log, {
  label: 'Dashboard Log',
  fg: "green",
  selectedFg: "green",
})

const commandList = grid.set(0, 1, 12, 1, blessed.list, {
  label: 'Commands',
  mouse: true,
  keys: true,
  style: {
    selected: { fg: 'green' }
  },
  items: ['Test', 'Test 2']
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
    const { name, script, bg, index } = ops
    this.name = name
    // this.script = script
    this.script = `echo ${script}`
    this.background = bg
    this.index = index

    const colors = ['blue', 'yellow', 'magenta', 'cyan', 'white']
    this.logger = grid.set(6 + index * 3, 0, 3, 1, contrib.log, {
      label: `${this.name} Log`,
      fg: colors[index] || colors[0],
      selectedFg: colors[index] || colors[0],
    })

    this.started = false
    this.running = false
    this.cancelled = false
    this.logs = []
    this.errs = []
    this.crashErrors = []

    this.logLimit = 1000
    this.errLimit = 1000
    this.timeBetweenScriptRuns = 3000
  }

  addStreamBufferLine(type, buffer) {
    const isErr = type === 'stderr'

    const line = buffer.toString('utf8').trimRight()

    const logLine = isErr ? line.red : line
    logToDashboard(this.logger, this.name, type, logLine)

    const arr = isErr ? this.errs : this.logs
    const limit = isErr ? this.errLimit : this.logLimit
    arr.unshift({ when: moment(), line })
    if (arr.length > limit) {
      arr.splice(limit, arr.length - limit)
    }
  }

  runScript() {
    genlog(`Starting Process - ${this.name}`)
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

        if (exitCode == 0) {
          resolve()
        } else {
          reject(`${this.name} Error: exited with code: ${exitCode}`)
        }
      })
    })
  }

  async startLoop() {
    this.started = true
    this.cancelled = false

    while (!this.cancelled) {
      await this.runScript()
        .catch(err => {
          this.crashErrors.push(err)
          genlog(`${this.name} Crash #${this.crashErrors.length} Error:`.red, err)
        })

      await delay(this.timeBetweenScriptRuns)
    }
  }

  cancelProcess() {
    this.cancelled = true

    if (this.child) {
      this.child.kill('SIGINT')
    }
  }
}

/// Kim Process Manager

class KimProcessManager {
  constructor() {
    const processConfigs =  [
      { name: 'Vysor', script: 'bin/start_vysor.sh', bg: true },
      { name: 'Device Server', script: 'bin/start_device_server.sh', bg: true },
      { name: 'Frontend Server', script: 'bin/start_frontend.sh', bg: true },
      { name: 'Phone Image Stream', script: 'bin/start_phone_stream.sh', bg: true },
      { name: 'AI Controller', script: 'bin/start_ai.sh', bg: false },
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
      await delay(200)
    }
  }
}

const kpManager = new KimProcessManager()

/// Dashboard Drawing

function drawDashboard() {
  const runningProcesses = kpManager.processes.filter(p => p.running)
  const pausedProcesses = kpManager.processes.filter(p => !p.running)

  commandList.setItems([
    ...runningProcesses.map(p => `Stop ${p.name}`),
    ...pausedProcesses.map(p => `Start ${p.name}`),
  ])

  screen.render()
}

function drawDashboardLoop() {
  drawDashboard()
  setTimeout(drawDashboardLoop, 100)
}

/// Main

async function main() {
  genlog('Hello, User. Starting KIM AI processes now...')

  commandList.focus()
  commandList.on('select', (item, index) => {
    genlog('selected:', JSON.stringify(item), index)
  })

  kpManager.initBackgroundProcesses()
    .catch(err => {
      genlog(`Process Running Error:`.red, err)
      throw err
    })

  screen.key(['escape', 'q', 'C-c'], function(ch, key) {
    return process.exit(0)
  })

  drawDashboardLoop()
}

main()
  // .then(() => process.exit(0))
  .catch(err => {
    console.log(`FATAL ALL PROCESS ERROR:`, err)
    process.exit(1)
  })
