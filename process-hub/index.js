#!/usr/bin/env node

const moment = require('moment')
const redis = require('redis')
const { argv } = require('yargs')
const { chunk } = require('lodash')
const { screen, dashboardParts, genlog, endLogWriteStreams } = require('./dashboard')
const { KimProcessManager } = require('./kim-process-manager')
const { getSystemInfoObject } = require('./system-info')
const { setWindowTitle, setupProcessHubScreen } = require('./util')

const rSubscriber = redis.createClient()
const rPublisher = redis.createClient()

/// Config

const modes = {
  DUMMY: 0,
  TF_AGENTS: 1,
  TF_AGENTS_TRAIN: 2,
  OLD_AI: 3,
}

let mode = modes.TF_AGENTS
if (argv.dummy !== undefined) {
  mode = mode.DUMMY
} else if (argv.train !== undefined) {
  mode = modes.TF_AGENTS_TRAIN
} else if (argv.old !== undefined) {
  mode = modes.OLD_AI
}

const START_ALL = argv.startAll != 'f' && argv.startAll != 'false'
const WIN_TITLE = 'AI Dashboard'

const startTime = moment()

const getMainProcessConfig = () => {
  if (mode == modes.TF_AGENTS) return { name: 'AI Runner', script: 'bin/start_tf_ai.sh' }
  else if (mode == modes.TF_AGENTS_TRAIN) return { name: 'AI Trainer', script: 'bin/train_tf_ai.sh' }
  else return { name: 'AI Controller', script: 'bin/start_old_ai.sh' }
}

const processConfigs = [
  { abbrev: 'VY', name: 'Vysor', script: 'process-hub/run_vysor.js' },
  { abbrev: 'DS', name: 'Device Server', script: 'bin/start_device_server.sh', maxTimeBetweenLogs: 30000 },
  { abbrev: 'FS', name: 'Frontend Server', script: 'bin/start_frontend_server.sh' },
  { abbrev: 'FC', name: 'Frontend Client', script: 'bin/start_frontend_client.sh' },
  { abbrev: 'PH', name: 'Phone Image Stream', script: 'bin/start_phone_stream.sh' },
  {
    ...getMainProcessConfig(),
    abbrev: 'AI',
    main: true,
    delayBefore: 10000,
    onLog: (logLines) => {
      logLines.forEach(line => rPublisher.publish('ai-log-lines', line))
    }
  },
]

/// Current State

const kpManager = new KimProcessManager({ processConfigs, dummy: mode === modes.DUMMY, redisPublisher: rPublisher })

let commands = []

const getCurrentCommands = () => [
  { label: 'Rest', fn: () => { } },
  ...kpManager.getProcessCommands(),
  { label: 'Xx Abort xX'.bgRed.white, fn: () => quit() },
]

/// Redis

const redisChannels = [
  { name: 'phone-image-states', handler: handlePhoneImageStates },
  { name: 'ai-action-stream', handleer: handleAIActionStream },
  { name: 'ai-status-updates', handler: handleAIStatusUpdates },
]

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

const aiStatusState = {
  screenIndex: 0,
  mostRecentAction: null,
  imageObjects: null,
  statusLines: []
}

function handlePhoneImageStates(data) {
  const { index, state } = data
  aiStatusState.screenIndex = index
  aiStatusState.imageObjects = state && state.image_objects || []
}

function handleAIActionStream(data) {
  if (data.type) {
    aiStatusState.mostRecentAction = data
  }
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

  aiStatusState.statusLines = [
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

function getAiStatusStateLines() {
  const { screenIndex, mostRecentAction, imageObjects, statusLines } = aiStatusState

  let recentActionLabel = 'None'
  if (mostRecentAction) {
    recentActionLabel = mostRecentAction.label || '?'
    if (mostRecentAction.p) {
      recentActionLabel += `: (${mostRecentAction.p[0]}, ${mostRecentAction.p[1]})`
    }
    if (mostRecentAction.prob !== undefined) {
      recentActionLabel += ` | ${(mostRecentAction.prob * 100).toFixed(1)}%`
    }
  }

  return [
    '',
    `Screen Index: ${screenIndex}`.red,
    `Most Recent Action: ${recentActionLabel}`,
    `# Image Objects: ${imageObjects ? imageObjects.length : '?'}`,
    '',
    ...statusLines,
  ]
}

function drawDashboard() {
  commands = getCurrentCommands()
  dashboardParts.commandList.setItems(commands.map(c => c.label))

  dashboardParts.processStopLineGraph.setData(kpManager.getProcessStopLineGraphData(startTime))
  dashboardParts.processStopBarGraph.setData(kpManager.getProcessStopBarGraphData())

  const startDiff = moment.utc(moment().diff(startTime)).format('HH:mm:ss')
  dashboardParts.timerLcd.setDisplay(startDiff)

  dashboardParts.aiStatusBox.content = getAiStatusStateLines().map(l => '  ' + l).join('\n')

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
