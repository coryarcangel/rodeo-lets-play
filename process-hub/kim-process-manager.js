const moment = require('moment')
const { range } = require('lodash')
const { KimProcess } = require('./kim-process')
const { delay } = require('./util')

class KimProcessManager {
  constructor({ processConfigs, dummy }) {
    // normalize process config script locations
    processConfigs.forEach(c => {
      c.script = `${__dirname}/../${c.script}`

      if (dummy) {
        c.script = `echo ${c.script} && sleep ${Math.floor(Math.random() * 10)}`
      }
    })

    this.processes = processConfigs.map((o, i) => {
      return new KimProcess({ ...o, index: i })
    })
  }

  async initProcesses(startAll) {
    for (const kp of this.processes) {
      if (startAll || !kp.ops.main) {
        const delayAmt = kp.ops.delayBefore || 3000
        await delay(delayAmt)

        kp.startLoop()
      }
    }
  }

  getProcessCommands() {
    return this.processes.map((p, i) => {
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
    })
  }

  getProcessStopLineGraphData(startTime) {
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

    return this.processes.map((p, pi) => {
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
  }

  getProcessStopBarGraphData() {
    const processData = this.processes.map(p => {
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
}

module.exports = { KimProcessManager }
