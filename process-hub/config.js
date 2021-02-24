const { argv } = require('yargs')

const OPTIONS = {
  IS_PROD: process.env.NODE_ENV === 'production' || argv.prod == 't' || argv.prod == 'true',
  START_ALL: argv.startAll != 'f' && argv.startAll != 'false',
  WIN_TITLE: 'AI_DASHBOARD',
  KILL_ADB_ON_DEVICE_SERVER_EXIT: false,
  SYSTEM_INFO_PUBLISH_INTERVAL: 15000,
  SCREEN_SETUP_INTERVAL: 5 * 60000,
  DEVICE_SERVER_MAX_TIME_BETWEEN_LOGS: 30000,
  DELAY_BEFORE_MAIN_PROCESS: 10000,
  DRAW_DASHBOARD_INTERVAL: 500,
  DASHBOARD_LOG_BUFFER_LENGTH: 15,
  DEFAULT_PROCESS_DELAY_BEFORE: 3000,
  DEFAULT_DELAY_BEFORE_CHAIN_PROCESS_RESTART: 2000,
}

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

const baseProcessConfigs = [
  { abbrev: 'VY', name: 'Vysor', script: 'process-hub/run_vysor.js' },
  {
    abbrev: 'DS',
    name: 'Device Server',
    script: 'bin/start_device_server.sh',
    maxTimeBetweenLogs: OPTIONS.DEVICE_SERVER_MAX_TIME_BETWEEN_LOGS,
    chainedRestarts: OPTIONS.KILL_ADB_ON_DEVICE_SERVER_EXIT ? ['Vysor'] : []
  },
  {
    abbrev: 'FS',
    name: 'Frontend Server',
    script: 'bin/start_frontend_server.sh',
    chainedRestarts: ['Frontend Client']
  },
  { abbrev: 'FC', name: 'Frontend Client', script: 'bin/start_frontend_client.sh' },
  { abbrev: 'PH', name: 'Phone Image Stream', script: 'bin/start_phone_stream.sh' },
]

module.exports = { OPTIONS, modes, mode, baseProcessConfigs }
