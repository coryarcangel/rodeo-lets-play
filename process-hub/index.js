#!/usr/bin/env node

const moment = require('moment')
const redis = require('redis')
const { argv } = require('yargs')
const { chunk } = require('lodash')
const { screen, dashboardParts, genlog, endLogWriteStreams } = require('./dashboard')
const { KimProcessManager } = require('./kim-process-manager')
const { getSystemInfoObject } = require('./system-info')
const { setWindowTitle, setupProcessHubScreen } = require('./util')

/// Config

const DUMMY = argv.dummy !== undefined ? argv.dummy : false
const START_ALL = argv.startAll != 'f' && argv.startAll != 'false'
const WIN_TITLE = 'AI Dashboard'

const startTime = moment()

const processConfigs = [
  { abbrev: 'VY', name: 'Vysor', script: 'process-hub/run_vysor.js' },
  { abbrev: 'DS', name: 'Device Server', script: 'bin/start_device_server.sh', maxTimeBetweenLogs: 30000 },
  { abbrev: 'FS', name: 'Frontend Server', script: 'bin/start_frontend_server.sh' },
  { abbrev: 'FC', name: 'Frontend Client', script: 'bin/start_frontend_client.sh' },
  { abbrev: 'PH', name: 'Phone Image Stream', script: 'bin/start_phone_stream.sh' },
  { abbrev: 'AI', name: 'AI Controller', script: 'bin/start_ai.sh', main: true, delayBefore: 10000 },
]

/// Current State

const kpManager = new KimProcessManager({ processConfigs, dummy: DUMMY })

let commands = []
let phoneImageStateLines = []
let aiStatusUpdateLines = []

const getCurrentCommands = () => [
  { label: 'Rest', fn: () => { } },
  ...kpManager.getProcessCommands(),
  { label: 'Xx Abort xX'.bgRed.white, fn: () => quit() },
]

/// Redis

const redisChannels = [
  { name: 'phone-image-states', handler: handlePhoneImageStates },
  { name: 'ai-status-updates', handler: handleAIStatusUpdates },
]

const rSubscriber = redis.createClient()
const rPublisher = redis.createClient()

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
  phoneImageStateLines = [
    `Screen Index: ${index}`.red,
    `Recent Touch: ${recent_touch ? recent_touch.label : 'None'}`,
    `# Image Objects: ${state && state.image_objects ? state.image_objects.length : '?'}`,
  ]
}

function handleAIStatusUpdates(data) {
  const actionTypeNames = {
    0: 'PASS',
    1: 'RESET',
    2: 'SWIPE_LEFT',
    3: 'SWIPE_RIGHT',
    4: 'TAP',
    5: 'DOUBLE_TAP',
  }

  const actions = data && data.actions || []
  const actionProbs = data && data.action_probs || []
  const actionTextList = actions
    .map((a, i) => {
      const p = actionProbs[i] || 0
      const [type, data] = a
      return { type, data, prob: p }
    })
    .sort((a, b) => b.prob - a.prob)
    .map(({ type, data, prob }, i) => {
      const name = actionTypeNames[type] || 'Unknown'
      const parts = [
        `#${i + 1}. ${name}`,
        ...(name === 'TAP' || name === 'DOUBLE_TAP' ? [
          [
            name === 'TAP' ? 'Tap' : 'Double Tap',
            data.object_type || data.type,
            `(${data.x}, ${data.y})`,
            ...(data.img_obj ? [`- ${((data.img_obj.confidence || 0) * 100).toFixed(1)}%`] : []),
          ].join(' ')
        ] : []),
        `${(prob * 100).toFixed(2)}%`
      ]
      return parts.join(' - ')
    })

  aiStatusUpdateLines = [
    `Actions:`,
    ...chunk(actionTextList, 2).map(items => items.join('\t')),
  ]
}

async function systemInfoPublishLoop() {
  const data = await getSystemInfoObject()
  rPublisher.publish('system-info-updates', JSON.stringify(data))

  setTimeout(systemInfoPublishLoop, 15000)
}

/// Dashboard Drawing

function drawDashboard() {
  commands = getCurrentCommands()
  dashboardParts.commandList.setItems(commands.map(c => c.label))

  dashboardParts.processStopLineGraph.setData(kpManager.getProcessStopLineGraphData(startTime))
  dashboardParts.processStopBarGraph.setData(kpManager.getProcessStopBarGraphData())

  const startDiff = moment.utc(moment().diff(startTime)).format('HH:mm:ss')
  dashboardParts.timerLcd.setDisplay(startDiff)

  dashboardParts.aiStatusBox.content = [
    '',
    ...phoneImageStateLines,
    '',
    ...aiStatusUpdateLines,
  ].map(l => '  ' + l).join('\n')

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

  await endLogWriteStreams()

  return process.exit(0)
}

async function main() {
  genlog('Hello, User. Starting KIM AI processes now...')

  setWindowTitle(WIN_TITLE)
  setupProcessHubScreen(WIN_TITLE)

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
  systemInfoPublishLoop()
}

main()
  .catch(err => {
    console.log(`FATAL ALL PROCESS ERROR:`, err)
    process.exit(1)
  })
