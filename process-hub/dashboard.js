require('colors')
const blessed = require('blessed')
const contrib = require('blessed-contrib')
const moment = require('moment')

/// Config

const ROWS = 24
const COLS = 4

/// Dashboard Setup

const screen = blessed.screen()
const grid = new contrib.grid({ rows: ROWS, cols: COLS, screen: screen })

const dashboardParts = {
  mainDashboardLogger: grid.set(0, 0, ROWS / 4, COLS / 2, contrib.log, {
    label: 'Dashboard Log',
    fg: 'white',
    selectedFg: 'white',
  }),

  commandList: grid.set(0, COLS / 2, ROWS / 4, 1, blessed.list, {
    label: 'Commands & Status',
    mouse: true,
    keys: true,
    style: {
      selected: { bg: 'gray' }
    },
    items: ['Test', 'Test 2']
  }),

  timerLcd: grid.set(0, 3, ROWS / 4, 1, contrib.lcd, {
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
  }),

  processStopLineGraph: grid.set(ROWS / 4, COLS / 2, 8, COLS / 2, contrib.line, {
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
  }),

  processStopBarGraph: grid.set(14, COLS / 2, 4, COLS / 2, contrib.stackedBar, {
    label: 'Total Process Restarts',
    barWidth: 12,
    barSpacing: 20,
    xOffset: 0,
    barBgColor: ['green', 'red']
  }),

  aiStatusBox: grid.set(ROWS / 4 * 3, COLS / 2, ROWS / 4, COLS / 2, blessed.box, {
    label: 'Current AI Status',
    content: 'Unknown at this time'.red.bold,
    style: { bg: 'blue', fg: 'white' },
  }),
}

/// Logging

// give a process index, get a logger in the grid
const getProcessLogger = (name, index, isMain, color) => grid.set(6 + index * 3, 0, isMain ? ROWS / 4 : 3, COLS / 2, contrib.log, {
  label: `${name} Log`,
  fg: color,
  selectedFg: color,
})

const logToDashboard = (dashboardLogger, ...strings) => {
  const now = moment().format('YY-MM-DD HH:mm:ss')
  const lines = strings.join('\n').split('\n')
  lines.forEach(l => {
    dashboardLogger.log(`${now}: ${l}`)
  })
}

const genlog = (...strings) => logToDashboard(dashboardParts.mainDashboardLogger, ...strings)

module.exports = {
  grid, screen, ROWS, COLS, dashboardParts, getProcessLogger, logToDashboard, genlog
}
