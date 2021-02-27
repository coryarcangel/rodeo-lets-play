#!/usr/bin/env node

require('colors')
const moment = require('moment')
const redis = require('redis')
const { debounce } = require('lodash')
const stripAnsi = require('strip-ansi')
const { screen, grid, dashboardParts, resetDashboardTimer, genlog, endLogWriteStreams } = require('./dashboard')
const { KimProcessManager } = require('./kim-process-manager')
const { getSystemInfoObject } = require('./system-info')
const { setWindowTitle, setupVisibleWindows, setupVysorWindow } = require('./util')
const { OPTIONS, modes, mode, baseProcessConfigs } = require('./config')

const rSubscriber = redis.createClient()
const rPublisher = redis.createClient()

/// Config

const { START_ALL, WIN_TITLE, SYSTEM_INFO_PUBLISH_INTERVAL,
        SCREEN_SETUP_INTERVAL, DRAW_DASHBOARD_INTERVAL } = OPTIONS

const startTime = moment()

const getMainProcessConfig = () => {
  if (mode == modes.TF_AGENTS) return { name: 'AI Runner', script: 'bin/start_tf_ai.sh' }
  else if (mode == modes.TF_AGENTS_TRAIN) return { name: 'AI Trainer', script: 'bin/train_tf_ai.sh' }
  else return { name: 'AI Controller', script: 'bin/start_old_ai.sh' }
}

const processConfigs = [
  ...baseProcessConfigs,
  {
    ...getMainProcessConfig(),
    abbrev: 'AI',
    main: true,
    delayBefore: OPTIONS.DELAY_BEFORE_MAIN_PROCESS,
    onLog: (logLines) => {
      logLines.forEach(line => rPublisher.publish('ai-log-lines', stripAnsi(line)))
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

/// Dashboard Drawing

function getAiStatusStateLines() {
  const {
    screenIndex, mostRecentAction, imageObjects,
    stepNum, reward, recentPolicyChoice, recentActionStepNums,
  } = aiStatusState

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

  const recentActionStepKeys = Object.keys(recentActionStepNums)

  return [
    '',
    `Screen Index`.bgRed.bold + ' - ' + `${screenIndex}`.red.bold,
    `Step`.bgBlue.bold + ' - ' + `${stepNum}`.brightBlue.bold,
    `Reward`.bgGreen.bold + ' - ' + ` ${reward}`.brightGreen.bold,
    `Num Image Objects`.bgCyan.bold + ' - ' + `${imageObjects ? imageObjects.length : '?'}`.brightCyan.bold,
    `Recent Policy`.bgWhite.black.bold + ` - ` + `${recentPolicyChoice}`.white.bold,
    `Recent Action`.bgYellow.bold + ` - ` + `${recentActionLabel}`.yellow.bold,
    ...recentActionStepKeys.map(k => `Num Steps Since ${k.green.underline}`.bgMagenta.bold + ` - ` + `${stepNum - recentActionStepNums[k]}`.brightMagenta.bold),
  ]
}

function drawDashboard() {
  dashboardParts.aiStatusBox.content = getAiStatusStateLines().map(l => '  ' + l).join('\n')

  screen.render()
}

function _updateAIStatusBox() {
  dashboardParts.aiStatusBox.content = getAiStatusStateLines().map(l => '  ' + l).join('\n')
}

const updateAIStatusBox = debounce(_updateAIStatusBox, 150)

function _updateAIActionsTable() {
  dashboardParts.aiActionsTable.setData({
    headers: [' Action'.bold, ' Prob'.bold],
    data: aiStatusState.actionItems.map(({ text, probText }) => [text, probText]),
  })
}

const updateAIActionsTable = debounce(_updateAIActionsTable, 200)

function _updateProcessDependentDashboardParts() {
  commands = getCurrentCommands()
  dashboardParts.commandList.setItems(commands.map(c => c.label))

  dashboardParts.processStopLineGraph.setData(kpManager.getProcessStopLineGraphData(startTime))
  dashboardParts.processStopBarGraph.setData(kpManager.getProcessStopBarGraphData())
}

const updateProcessDependentDashboardParts = debounce(_updateProcessDependentDashboardParts, 150)

function updateTimerLCD() {
  const startDiff = moment.utc(moment().diff(startTime)).format('HH:mm:ss')
  dashboardParts.timerLcd.setDisplay(startDiff)
}

function updateTimerLCDLoop() {
  updateTimerLCD()
  setTimeout(updateTimerLCDLoop, 1000)
}

function updateAllDashboardPartsAndRender() {
  _updateAIActionsTable()
  _updateAIStatusBox()
  _updateProcessDependentDashboardParts()
  updateTimerLCD()

  screen.render()
}

function renderScreenLoop() {
  screen.render()
  setTimeout(renderScreenLoop, DRAW_DASHBOARD_INTERVAL)
}

/// Redis

const redisChannels = [
  { name: 'phone-image-states', handler: handlePhoneImageStates },
  { name: 'ai-action-stream', handler: handleAIActionStream },
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
  reward: 0,
  stepNum: 0,
  recentPolicyChoice: null,
  recentActionStepNums: {},
  actionItems: [],
}

function handlePhoneImageStates(data) {
  const { index, state: stateJSON } = data
  const state = JSON.parse(stateJSON || "")
  aiStatusState.screenIndex = index
  aiStatusState.imageObjects = state && state.image_objects || []
  updateAIStatusBox()
}

function handleAIActionStream(data) {
  if (data.type) {
    aiStatusState.mostRecentAction = data
    updateAIStatusBox()
  }
}

function handleAIStatusUpdates(data) {
  aiStatusState.reward = Number(data.reward) || 0
  aiStatusState.stepNum = data.step_num
  aiStatusState.recentPolicyChoice = data.policy_choice
  aiStatusState.recentActionStepNums = data.recent_action_step_nums

  const actionTypeNames = {
    0: 'PASS',
    1: 'RESET',
    2: 'SWIPE_LEFT',
    3: 'SWIPE_RIGHT',
    4: 'TAP',
    5: 'DOUBLE_TAP',
  }

  const actionNameColors = {
    PASS: 'white',
    RESET: 'red',
    SWIPE_LEFT: 'yellow',
    SWIPE_RIGHT: 'yellow',
    TAP: 'brightBlue',
    DOUBLE_TAP: 'brightMagenta'
  }

  const actions = data && data.actions || []
  const actionProbs = data && data.action_probs || []
  const actionItems = actions
    .map((a, i) => {
      const p = actionProbs[i] || 0
      const [type, data] = a
      return { type, data, prob: p }
    })
    .sort((a, b) => b.prob - a.prob)
    .slice(0, 12)
    .map(({ type, data, prob }, i) => {
      const name = actionTypeNames[type] || 'Unknown'
      const parts = [
        ...(name === 'TAP' || name === 'DOUBLE_TAP' ? [
          [
            (data.img_obj && data.img_obj.shape_data ? `${data.img_obj.shape_data.action_shape} ${data.img_obj.shape_data.color_label}` : data.object_type || data.type).brightCyan,
            `(${data.x}, ${data.y})`,
            ...(data.img_obj && data.img_obj.confidence ? [`- ${((data.img_obj.confidence || 0) * 100).toFixed(1)}%`.grey] : []),
          ].join(' ')
        ] : ['-']),
      ]
      const info = parts.join(' - ')
      const number = i + 1
      const color = actionNameColors[name] || 'white'
      const text = `${number < 10 ? '0' : ''}${number}. ${name[color].bold} ${info}`
      const probText =  `${(prob * 100).toFixed(1)}%`.white.bold
      return { type, data, prob, number, name, color, info, text, probText }
    })

  aiStatusState.actionItems = actionItems

  updateAIStatusBox()
  updateAIActionsTable()
}

async function systemInfoPublishLoop() {
  const data = await getSystemInfoObject()
  rPublisher.publish('system-info-updates', JSON.stringify(data))

  setTimeout(systemInfoPublishLoop, SYSTEM_INFO_PUBLISH_INTERVAL)
}

/// Main

async function quit() {
  await Promise.all(kpManager.processes.map(async p => {
    await p.killChild()
  }))

  await endLogWriteStreams()

  return process.exit(0)
}

function onResize() {
  // genlog('resizing..')
  screen.realloc()
  kpManager.processes.forEach(p => p.logger.logger.emit('attach'))
  resetDashboardTimer()
  dashboardParts.mainDashboardLogger.logger.emit('attach')
  dashboardParts.commandList.emit('attach')
  dashboardParts.processStopLineGraph.emit('attach')
  dashboardParts.processStopBarGraph.emit('attach')
  dashboardParts.aiStatusBox.emit('attach')
  dashboardParts.aiActionsTable.emit('attach')
  updateAllDashboardPartsAndRender()
}

async function setupScreenLoop() {
  await setupVisibleWindows()
  onResize()
  setTimeout(setupScreenLoop, SCREEN_SETUP_INTERVAL)
}

async function main() {
  genlog('Hello, User. Starting KIM AI processes now...')

  // setup window
  setWindowTitle(WIN_TITLE)
  await setupScreenLoop()

  dashboardParts.commandList.focus()

  // handle commands
  dashboardParts.commandList.on('select', (item, index) => {
    const command = index < commands.length ? commands[index] : null
    if (command && command.fn) {
      command.fn()
    }
  })

  // update process-dependent parts of dashboard only when process status changes
  kpManager.onProcessesChange = (kimProcess, action) => {
    updateProcessDependentDashboardParts()

    if ((kimProcess.name === 'Vysor' || kimProcess.name === 'Phone Image Stream') && action === 'start') {
      setTimeout(setupVysorWindow, 20000)
    }
  }

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

  // handle resize events
  screen.on('resize', onResize)

  // setup time-dependent loops
  updateTimerLCDLoop()
  renderScreenLoop()
  systemInfoPublishLoop()
}

main()
  .catch(err => {
    console.log(`FATAL ALL PROCESS ERROR:`, err)
    process.exit(1)
  })
