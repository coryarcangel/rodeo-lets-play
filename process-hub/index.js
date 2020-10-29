#!/usr/bin/env node

const moment = require('moment')
const redis = require('redis')
const { argv } = require('yargs')
const { screen, dashboardParts, genlog } = require('./dashboard')
const { KimProcessManager } = require('./kim-process-manager')

/// Config

const DUMMY = argv.dummy !== undefined ? argv.dummy : false
const START_ALL = argv.startAll != 'f' && argv.startAll != 'false'

const startTime = moment()

const processConfigs = [
  { abbrev: 'VY', name: 'Vysor', script: 'process-hub/run_vysor.js' },
  { abbrev: 'DS', name: 'Device Server', script: 'bin/start_device_server.sh' },
  { abbrev: 'FS', name: 'Frontend Server', script: 'bin/start_frontend_server.sh' },
  { abbrev: 'FC', name: 'Frontend Client', script: 'bin/start_frontend_client.sh' },
  { abbrev: 'PH', name: 'Phone Image Stream', script: 'bin/start_phone_stream.sh' },
  { abbrev: 'AI', name: 'AI Controller', script: 'bin/start_ai.sh', main: true, delayBefore: 10000 },
]

/// Redis

const redisChannels = [
  { name: 'phone-image-states', handler: handlePhoneImageStates },
]

const rSubscriber = redis.createClient()

rSubscriber.on('message', (channel, message) => {
  const item = redisChannels.find(rc => rc.name === channel)
  if (item) {
    let data = {}
    try {
      data = JSON.parse(message)
    } catch (err) {}

    item.handler(data)
  }
})

redisChannels.forEach(rc => rSubscriber.subscribe(rc.name))

function handlePhoneImageStates(data) {
  const { index, recent_touch, state } = data
  const lines = [
    '',
    `Screen Index: ${index}`.red,
    `Recent Touch: ${recent_touch ? recent_touch.label : 'None'}`,
    `# Image Objects: ${state && state.image_objects ? state.image_objects.length : '?'}`,
  ].map(l => '  ' + l)
  dashboardParts.aiStatusBox.content = lines.join('\n')
}

/// Current State

const kpManager = new KimProcessManager({ processConfigs, dummy: DUMMY })

let commands = []

const getCurrentCommands = () => [
  { label: 'Rest', fn: () => { } },
  ...kpManager.getProcessCommands(),
  { label: 'Xx Abort xX'.bgRed.white, fn: () => quit() },
]

/// Dashboard Drawing

function drawDashboard() {
  commands = getCurrentCommands()
  dashboardParts.commandList.setItems(commands.map(c => c.label))

  dashboardParts.processStopLineGraph.setData(kpManager.getProcessStopLineGraphData(startTime))
  dashboardParts.processStopBarGraph.setData(kpManager.getProcessStopBarGraphData())

  const startDiff = moment.utc(moment().diff(startTime)).format('HH:mm:ss')
  dashboardParts.timerLcd.setDisplay(startDiff)

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

  dashboardParts.commandList.focus()

  // handle commands
  dashboardParts.commandList.on('select', (item, index) => {
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
