require('colors')
const blessed = require('blessed')
const contrib = require('blessed-contrib')
const moment = require('moment')
const stripAnsi = require('strip-ansi')
const fs = require('fs')
const path = require('path')

/// Config

const ROWS = 48
const COLS = 16

/// Dashboard Setup

const screen = blessed.screen()
const grid = new contrib.grid({ rows: ROWS, cols: COLS, screen: screen, hideBorder: true })

/// Logging

const allLoggerStreams = [] // maintain list for cleanup later

const getLogger = (name, row, col, width, height, color) => {
  const logger = grid.set(row, col, width, height, contrib.log, {
    label: `${name} Log`,
    fg: color,
    selectedFg: color,
    border: { type: 'line', fg: color },
  })

  const filepath = `${__dirname}/../logs/${name.toLowerCase().replace(/ /g, '_')}.log`
  if (!fs.existsSync(path.dirname(filepath))) {
    fs.mkdirSync(path.dirname(filepath))
  }

  fs.writeFileSync(filepath, '')

  const stream = fs.createWriteStream(filepath, { flags: 'a' })
  allLoggerStreams.push(stream)

  const log = (line) => {
    logger.log(line)
    stream.write(stripAnsi(line) + '\n')
  }

  return { name, filepath, stream, logger, log }
}

// give a process index, get a logger in the grid
const getProcessLogger = (name, index, isMain, color) => {
  return getLogger(name, ROWS / 6 + index * (ROWS / 8), 0, isMain ? 10 : ROWS / 8, COLS / 2, color)
}

const logToDashboard = (dashboardLogger, ...strings) => {
  const now = moment().format('MM-DD HH:mm:ss')
  const lines = strings.join('\n').split('\n')
  lines.forEach(l => {
    dashboardLogger.log(`${now} - ${l}`)
  })
}

const endLogWriteStreams = () => {
  return new Promise(resolve => {
    if (allLoggerStreams.length === 0) {
      return resolve()
    }

    let count = 0
    allLoggerStreams.forEach(s => {
      s.end('', () => {
        if (++count === allLoggerStreams.length) {
          resolve()
        }
      })
    })
  })
}

/// Dashboard Parts

let processStopPos = { row: ROWS / 4, height: ROWS / 3 }

const dashboardParts = {}

const resetDashboardTimer = () => {
  dashboardParts.timerLcd = grid.set(0, COLS * 0.75, ROWS / 4, COLS / 4, contrib.lcd, {
    label: 'Run Time',
    elements: 8,
    display: '00:00:00',
    segmentWidth: 0.09,
    segmentInterval: 0.2,
    strokeWidth: 0.25,
    elementPadding: 4,
    elementSpacing: 2,
    color: 'yellow',
    style: { bg: 'black' },
    border: { type: 'line', fg: 'red' },
  })
}

const resetDashboardParts = () => {
  dashboardParts.mainDashboardLogger = getLogger('Dashboard', 0, 0, ROWS / 6, COLS / 2, 'white')

  dashboardParts.commandList = grid.set(0, COLS / 2, ROWS / 4, COLS / 4, blessed.list, {
    label: 'Commands & Status',
    mouse: true,
    keys: true,
    style: {
      selected: { bg: 'gray' }
    },
    items: ['Test', 'Test 2'],
    border: { type: 'line', fg: 'blue' },
  })

  resetDashboardTimer()

  dashboardParts.processStopLineGraph = grid.set(processStopPos.row, COLS / 2, processStopPos.height, COLS / 2, contrib.line, {
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
    },
    border: { type: 'line', fg: 'white' },
  })

  dashboardParts.processStopBarGraph = grid.set(processStopPos.row + processStopPos.height, COLS / 2, ROWS / 6, COLS / 2, contrib.stackedBar, {
    label: 'Total Process Restarts',
    barWidth: 12,
    barSpacing: 20,
    xOffset: 0,
    barBgColor: ['green', 'red'],
    border: { type: 'line', fg: 'yellow' },
  })

  dashboardParts.aiStatusBox = grid.set(ROWS - ROWS / 4, COLS / 2, ROWS / 4, 3, blessed.box, {
    label: 'Current AI Status',
    content: 'Unknown at this time'.red.bold,
    border: { type: 'line', fg: 'blue' },
    style: { bg: 'black', fg: 'white' },
  })

  dashboardParts.aiActionsTable = grid.set(ROWS - ROWS / 4, COLS / 2 + 3, ROWS / 4, COLS / 2 - 3, contrib.table, {
    label: 'AI Actions',
    keys: false,
    interactive: false,
    bg: 'black', fg: 'green',
    border: { type: 'line', fg: 'green' },
    columnSpacing: 2,
    columnWidth: [50, 6],
  })
}

resetDashboardParts()

const genlog = (...strings) => logToDashboard(dashboardParts.mainDashboardLogger, ...strings)

module.exports = {
  grid, screen, ROWS, COLS, dashboardParts, resetDashboardParts, resetDashboardTimer, getProcessLogger, logToDashboard, genlog, endLogWriteStreams
}
